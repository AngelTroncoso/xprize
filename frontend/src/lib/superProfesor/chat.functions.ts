// Server fn: reemplaza FastAPI POST /api/chat
// Carga OAs reales del catálogo (curriculum_objectives) para el curso/asignatura
// seleccionados y los inyecta como contexto al modelo.
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const ChatInput = z.object({
  student_id: z.string(),
  curso: z.string(),
  asignatura: z.string(),
  message: z.string().min(1),
});

function isReligion(a: string) {
  return /religi[oó]n|formaci[oó]n val[oó]rica/i.test(a);
}

async function loadCurriculumContext(curso: string, asignatura: string) {
  const { getExternalAdmin } = await import(
    "@/integrations/supabase/external-admin.server"
  );
  const admin = getExternalAdmin();
  let q = admin
    .from("curriculum_objectives")
    .select("id_oa, descripcion, eje_tematico, conceptos_clave, indicadores_evaluacion")
    .eq("curso", curso)
    .limit(40);
  q = isReligion(asignatura)
    ? q.ilike("asignatura", "%religi%")
    : q.eq("asignatura", asignatura);
  const { data, error } = await q;
  if (error) {
    console.error("[chat] curriculum context error:", error.message);
    throw new Error(`No se pudo cargar el contexto curricular: ${error.message}`);
  }
  return data ?? [];
}

export const sendChatMessageFn = createServerFn({ method: "POST" })
  .inputValidator((d) => ChatInput.parse(d))
  .handler(async ({ data }) => {
    const oas = await loadCurriculumContext(data.curso, data.asignatura);

    // TODO: orquestar agente IA con `oas` como contexto + registrar el turno.
    const response_text =
      `🧠 Recibí tu mensaje de **${data.asignatura}** (${data.curso}): "${data.message}".\n\n` +
      `Tengo ${oas.length} OA(s) reales del catálogo MINEDUC como contexto. ` +
      `(Conecta aquí tu modelo IA para generar la respuesta final.)`;

    return {
      response_text,
      audio_response_b64: null as string | null,
    };
  });
