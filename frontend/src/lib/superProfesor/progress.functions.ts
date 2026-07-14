// Server fn: reemplaza FastAPI GET /api/students/{id}/progress
// Cruza student_mastery (oa_code) ↔ curriculum_objectives.id_oa usando
// service_role para construir el árbol Curso → Asignatura → Eje → OAs.
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import type { ProgressTree, OAStatus } from "@/lib/apiService";

const ProgressInput = z.object({
  student_id: z.union([z.string(), z.number()]),
});

function mapMastery(level: unknown): OAStatus {
  if (typeof level === "number") {
    if (level >= 0.8) return "dominado";
    if (level > 0) return "en_progreso";
    return "no_iniciado";
  }
  const s = String(level ?? "").toLowerCase();
  if (["mastered", "dominado", "logrado", "achieved"].includes(s)) return "dominado";
  if (["in_progress", "en_progreso", "partial", "developing"].includes(s))
    return "en_progreso";
  return "no_iniciado";
}

function pick<T = unknown>(row: any, ...keys: string[]): T | undefined {
  for (const k of keys) {
    if (row?.[k] !== undefined && row[k] !== null) return row[k] as T;
  }
  return undefined;
}

function toArray(v: unknown): string[] {
  if (!v) return [];
  if (Array.isArray(v)) return v.map(String);
  if (typeof v === "object") {
    const anyV = v as any;
    if (Array.isArray(anyV.items)) return anyV.items.map(String);
    return Object.values(anyV).map(String);
  }
  if (typeof v === "string")
    return v.split(/[;,]/).map((s) => s.trim()).filter(Boolean);
  return [];
}

export const getStudentProgressFn = createServerFn({ method: "GET" })
  .inputValidator((d) => ProgressInput.parse(d))
  .handler(async ({ data }): Promise<ProgressTree> => {
    const { getExternalAdmin } = await import(
      "@/integrations/supabase/external-admin.server"
    );
    const admin = getExternalAdmin();

    // 1. Catálogo válido (esquema real).
    const { data: oas, error: oasErr } = await admin
      .from("curriculum_objectives")
      .select(
        "id, curso, asignatura, eje_tematico, id_oa, descripcion, conceptos_clave",
      );
    if (oasErr) {
      console.error("[progress] curriculum_objectives error", oasErr);
      throw new Error(`No se pudo cargar el catálogo: ${oasErr.message}`);
    }

    // 2. Mastery del estudiante (tolerante a oa_code/code/id_oa).
    let mastery: any[] = [];
    const masteryRes = await admin
      .from("student_mastery")
      .select("*")
      .eq("student_id", data.student_id as any);
    if (!masteryRes.error) mastery = masteryRes.data ?? [];
    else
      console.warn(
        "[progress] student_mastery no disponible:",
        masteryRes.error.message,
      );

    // 3. Nombre del estudiante (best-effort).
    let student_name = "Estudiante";
    const studentRes = await admin
      .from("students")
      .select("*")
      .eq("id", data.student_id as any)
      .maybeSingle();
    if (!studentRes.error && studentRes.data) {
      student_name = String(
        pick(studentRes.data, "nombre", "name", "full_name") ?? student_name,
      );
    }

    // 4. Index de mastery por id_oa.
    const masteryByCode = new Map<string, unknown>();
    for (const m of mastery) {
      const code = String(pick(m, "id_oa", "oa_code", "code", "codigo") ?? "");
      if (!code) continue;
      masteryByCode.set(
        code,
        pick(m, "mastery_level", "mastery", "status", "level"),
      );
    }

    // 5. Árbol Curso → Asignatura (Religión unificada) → Eje → OAs.
    type OAOut = {
      code: string;
      title: string;
      concepts: string[];
      status: OAStatus;
    };
    const tree = new Map<string, Map<string, Map<string, OAOut[]>>>();
    for (const row of oas ?? []) {
      const curso = String(row.curso ?? "Sin curso");
      const asignaturaRaw = String(row.asignatura ?? "Sin asignatura");
      const asignatura = /religi[oó]n|formaci[oó]n val[oó]rica/i.test(asignaturaRaw)
        ? "Religión"
        : asignaturaRaw;
      const eje = String(row.eje_tematico ?? "General");
      const code = String(row.id_oa ?? "OA");
      const oa: OAOut = {
        code,
        title: String(row.descripcion ?? ""),
        concepts: toArray(row.conceptos_clave),
        status: mapMastery(masteryByCode.get(code)),
      };
      if (!tree.has(curso)) tree.set(curso, new Map());
      const asigMap = tree.get(curso)!;
      if (!asigMap.has(asignatura)) asigMap.set(asignatura, new Map());
      const ejeMap = asigMap.get(asignatura)!;
      if (!ejeMap.has(eje)) ejeMap.set(eje, []);
      ejeMap.get(eje)!.push(oa);
    }

    const cursos = Array.from(tree.entries()).map(([name, asigMap]) => ({
      name,
      asignaturas: Array.from(asigMap.entries()).map(([aname, ejeMap]) => ({
        name: aname,
        ejes: Array.from(ejeMap.entries()).map(([ename, oasList]) => ({
          name: ename,
          oas: oasList,
        })),
      })),
    }));

    return {
      student_id: data.student_id,
      student_name,
      cursos,
    };
  });
