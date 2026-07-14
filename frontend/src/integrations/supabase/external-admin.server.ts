// Cliente Supabase EXTERNO con SERVICE_ROLE. SOLO server-side.
// Importar este archivo desde código que llegue al navegador rompe el build a propósito.
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let _admin: SupabaseClient | null = null;

export function getExternalAdmin(): SupabaseClient {
  if (_admin) return _admin;
  const url = process.env.EXTERNAL_SUPABASE_URL;
  const key = process.env.EXTERNAL_SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error(
      "Faltan EXTERNAL_SUPABASE_URL o EXTERNAL_SUPABASE_SERVICE_ROLE_KEY en el entorno del servidor.",
    );
  }
  _admin = createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false, storage: undefined },
  });
  return _admin;
}
