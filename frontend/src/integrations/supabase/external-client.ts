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

/**
 * Trae unidades + OAs anidados en una sola pasada (JOIN real por unit_id → curriculum_units.id).
 * Usa PostgREST embedded resources para evitar dos round-trips.
 */
export async function fetchCurriculumCatalog(filters?: {
  curso?: string;
  asignatura?: string;
}) {
  const supabase = await getExternalSupabase();
  let q = supabase
    .from("curriculum_units")
    .select(
      `id, curso, asignatura, eje_tematico,
       objectives:curriculum_objectives!unit_id(
         id, unit_id, curso, asignatura, eje_tematico,
         id_oa, descripcion, indicadores_evaluacion, conceptos_clave, metadata
       )`,
    );
  if (filters?.curso) q = q.eq("curso", filters.curso);
  q = applySubjectFilter(q, filters?.asignatura);
  const { data, error } = await q;
  if (error) throw error;
  return (data ?? []).map((u: any) => ({
    ...normalizeUnit(u),
    objectives: (u.objectives ?? []).map(normalizeObjective),
  }));
}
