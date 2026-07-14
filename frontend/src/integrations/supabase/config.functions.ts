import { createServerFn } from "@tanstack/react-start";

/**
 * Expone al frontend solo la URL + ANON KEY del Supabase externo.
 * La SERVICE_ROLE_KEY NUNCA se entrega por aquí.
 */
export const getExternalSupabaseConfig = createServerFn({ method: "GET" }).handler(
  async () => {
    const url = process.env.EXTERNAL_SUPABASE_URL;
    const anonKey = process.env.EXTERNAL_SUPABASE_ANON_KEY;
    if (!url || !anonKey) {
      throw new Error(
        "Faltan EXTERNAL_SUPABASE_URL o EXTERNAL_SUPABASE_ANON_KEY en el entorno del servidor.",
      );
    }
    return { url, anonKey };
  },
);
