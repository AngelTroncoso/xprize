// Cliente Supabase EXTERNO (proyecto propio del usuario) para frontend.
// Hidrata bajo demanda llamando a una server fn que entrega URL + ANON_KEY.
// La service_role NUNCA viaja al navegador.
//
// Esquema REAL (confirmado por el usuario):
//   public.curriculum_units(id, curso, asignatura, eje_tematico)
//   public.curriculum_objectives(id, unit_id, curso, asignatura, eje_tematico,
//                                id_oa, descripcion, indicadores_evaluacion,
//                                conceptos_clave, metadata)
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { getExternalSupabaseConfig } from "./config.functions";

let _client: SupabaseClient | null = null;
let _initPromise: Promise<SupabaseClient> | null = null;

export async function getExternalSupabase(): Promise<SupabaseClient> {
  if (_client) return _client;
  if (_initPromise) return _initPromise;
  _initPromise = (async () => {
    const { url, anonKey } = await getExternalSupabaseConfig();
    _client = createClient(url, anonKey, {
      auth: {
        persistSession: typeof window !== "undefined",
        autoRefreshToken: typeof window !== "undefined",
      },
    });
    return _client;
  })();
  return _initPromise;
}

// -------------------- Tipos normalizados --------------------
export interface CurriculumUnit {
  id: string | number;
  curso: string;
  asignatura: string;
  eje: string; // eje_tematico
  nombre: string; // alias visual = eje_tematico (no hay columna nombre)
}

export interface CurriculumObjective {
  id: string | number;
  unit_id: string | number | null;
  code: string; // id_oa
  title: string; // descripcion
  concepts: string[]; // conceptos_clave
  indicators: string[]; // indicadores_evaluacion
  curso: string;
  asignatura: string;
  eje: string; // eje_tematico
  metadata?: Record<string, unknown> | null;
}

// -------------------- Helpers --------------------
function toArray(v: unknown): string[] {
  if (!v) return [];
  if (Array.isArray(v)) return v.map(String);
  if (typeof v === "object") {
    // jsonb a veces llega como objeto {items:[...]}
    const anyV = v as any;
    if (Array.isArray(anyV.items)) return anyV.items.map(String);
    return Object.values(anyV).map(String);
  }
  if (typeof v === "string") {
    const t = v.trim();
    if (t.startsWith("[")) {
      try {
        const arr = JSON.parse(t);
        if (Array.isArray(arr)) return arr.map(String);
      } catch {
        /* noop */
      }
    }
    return t.split(/[;,]/).map((s) => s.trim()).filter(Boolean);
  }
  return [];
}

function normalizeUnit(row: any): CurriculumUnit {
  return {
    id: row.id,
    curso: String(row.curso ?? ""),
    asignatura: String(row.asignatura ?? ""),
    eje: String(row.eje_tematico ?? ""),
    nombre: String(row.eje_tematico ?? "Unidad"),
  };
}

function normalizeObjective(row: any): CurriculumObjective {
  return {
    id: row.id,
    unit_id: row.unit_id ?? null,
    code: String(row.id_oa ?? "OA"),
    title: String(row.descripcion ?? ""),
    concepts: toArray(row.conceptos_clave),
    indicators: toArray(row.indicadores_evaluacion),
    curso: String(row.curso ?? ""),
    asignatura: String(row.asignatura ?? ""),
    eje: String(row.eje_tematico ?? ""),
    metadata: (row.metadata as Record<string, unknown> | null) ?? null,
  };
}

/** Religión se almacena como sub-vertientes (Católica/Evangélica/etc). */
export function isReligionFilter(asignatura?: string): boolean {
  return !!asignatura && /religi[oó]n|formaci[oó]n val[oó]rica/i.test(asignatura);
}

function applySubjectFilter(query: any, asignatura?: string, col = "asignatura") {
  if (!asignatura) return query;
  if (isReligionFilter(asignatura)) return query.ilike(col, "%religi%");
  return query.eq(col, asignatura);
}

// -------------------- Lecturas (RLS, anon/authenticated) --------------------
export async function fetchCurriculumUnits(filters?: {
  curso?: string;
  asignatura?: string;
}): Promise<CurriculumUnit[]> {
  const supabase = await getExternalSupabase();
  let q = supabase.from("curriculum_units").select("id, curso, asignatura, eje_tematico");
  if (filters?.curso) q = q.eq("curso", filters.curso);
  q = applySubjectFilter(q, filters?.asignatura);
  const { data, error } = await q;
  if (error) throw error;
  return (data ?? []).map(normalizeUnit);
}

export async function fetchCurriculumObjectives(
  unitIds?: Array<string | number>,
  filters?: { curso?: string; asignatura?: string },
): Promise<CurriculumObjective[]> {
  const supabase = await getExternalSupabase();
  let q = supabase
    .from("curriculum_objectives")
    .select(
      "id, unit_id, curso, asignatura, eje_tematico, id_oa, descripcion, indicadores_evaluacion, conceptos_clave, metadata",
    );
  if (unitIds && unitIds.length > 0) q = q.in("unit_id", unitIds);
  if (filters?.curso) q = q.eq("curso", filters.curso);
  q = applySubjectFilter(q, filters?.asignatura);
  const { data, error } = await q;
  if (error) throw error;
  return (data ?? []).map(normalizeObjective);
}

export async function fetchCurriculumCatalog(filters?: {
  curso?: string;
  asignatura?: string;
}) {
  const BACKEND_URL =
    (import.meta as any).env?.VITE_BACKEND_URL ?? "https://superprofesor-backend-253925950091.us-central1.run.app";

  let url = `${BACKEND_URL}/api/curriculum/oas`;
  if (filters?.curso || filters?.asignatura) {
    const params = new URLSearchParams();
    if (filters.curso) params.append("curso", filters.curso);
    if (filters.asignatura) params.append("asignatura", filters.asignatura);
    url += `?${params.toString()}`;
  }

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Error HTTP: ${res.status}`);
  }

  const data = await res.json();
  // El backend retorna { objetivos_aprendizaje: [...] } cuando hay filtros
  // o { curriculum: {...} } cuando no hay. Manejamos ambos casos o un array plano.
  const oasList = Array.isArray(data) ? data : data.objetivos_aprendizaje || [];

  const unitsMap = new Map<string, any>();

  for (const oa of oasList) {
    const eje = oa.eje_tematico || "General";
    if (!unitsMap.has(eje)) {
      unitsMap.set(eje, {
        id: eje,
        curso: oa.curso || filters?.curso || "",
        asignatura: oa.asignatura || filters?.asignatura || "",
        eje: eje,
        nombre: eje,
        objectives: [],
      });
    }

    unitsMap.get(eje).objectives.push({
      id: oa.id_oa,
      unit_id: eje,
      code: oa.id_oa,
      title: oa.descripcion,
      concepts: oa.conceptos_clave || [],
      indicators: oa.indicadores_evaluacion || [],
      curso: oa.curso || "",
      asignatura: oa.asignatura || "",
      eje: eje,
      metadata: null,
    });
  }

  return Array.from(unitsMap.values());
}
