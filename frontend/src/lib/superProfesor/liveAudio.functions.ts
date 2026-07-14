// Server fn: recibe chunks de audio (base64 PCM/webm) del alumno y devuelve
// la respuesta del Super_Profesor (texto + audio base64). Boilerplate para
// orquestar el agente de IA en tiempo real (estilo Gemini Live).
//
// La conexión "bidireccional estable" del frontend se simula aquí por turnos
// HTTP corto-largo: el cliente envía cada turno (uno o varios chunks
// concatenados) y recibe la respuesta. Cuando exista un transport WS/SSE,
// reemplazar este handler por una server route en src/routes/api/.
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const LiveTurnInput = z.object({
  student_id: z.string(),
  curso: z.string(),
  asignatura: z.string(),
  active_id_oa: z.string().nullable().optional(),
  // Chunk binario codificado en base64 (mime tipo "audio/webm" o "audio/pcm")
  audio_chunk_b64: z.string().min(1),
  mime: z.string().default("audio/webm"),
});

function isReligion(a: string) {
  return /religi[oó]n|formaci[oó]n val[oó]rica/i.test(a);
}

async function loadOaContext(
  curso: string,
  asignatura: string,
  activeOa?: string | null,
) {
  const { getExternalAdmin } = await import(
    "@/integrations/supabase/external-admin.server"
  );
  const admin = getExternalAdmin();
  let q = admin
    .from("curriculum_objectives")
    .select("id_oa, descripcion, eje_tematico, conceptos_clave")
    .eq("curso", curso)
    .limit(20);
  q = isReligion(asignatura)
    ? q.ilike("asignatura", "%religi%")
    : q.eq("asignatura", asignatura);
  if (activeOa) q = q.eq("id_oa", activeOa);
  const { data, error } = await q;
  if (error) throw new Error(error.message);
  return data ?? [];
}

export const liveAudioTurnFn = createServerFn({ method: "POST" })
  .inputValidator((d) => LiveTurnInput.parse(d))
  .handler(async ({ data }) => {
    const oas = await loadOaContext(data.curso, data.asignatura, data.active_id_oa);

    // TODO: pasar el chunk a STT → LLM (con `oas` como contexto) → TTS
    // y devolver el audio resultante en base64.
    return {
      transcript: "(transcripción simulada del alumno)",
      response_text:
        `Te escuché perfecto en ${data.asignatura} (${data.curso}). ` +
        `Tengo ${oas.length} OA(s) de contexto. ¡Sigamos!`,
      audio_response_b64: null as string | null,
      mime: "audio/mpeg",
    };
  });
