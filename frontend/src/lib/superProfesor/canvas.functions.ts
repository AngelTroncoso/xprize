// Server fn: reemplaza FastAPI POST /api/canvas/analyze
// Carga OAs reales del catálogo para anclar la retroalimentación al currículum.
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const CanvasInput = z.object({
  student_id: z.string(),
  curso: z.string(),
  asignatura: z.string(),
  canvas_data: z.string().min(10),
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
    console.error("[canvas] curriculum context error:", error.message);
    throw new Error(`No se pudo cargar el contexto curricular: ${error.message}`);
  }
  return data ?? [];
}

export const analyzeCanvasFn = createServerFn({ method: "POST" })
  .inputValidator((d) => CanvasInput.parse(d))
  .handler(async ({ data }) => {
    const bytes = Math.round((data.canvas_data.length * 3) / 4);
    const oas = await loadCurriculumContext(data.curso, data.asignatura);

    // TODO: enviar canvas_data (PNG base64) + OAs a modelo multimodal y persistir evidencia.
    const feedback_text =
      `🎨 Analicé tu pizarra de **${data.asignatura}** (${data.curso}, ${bytes} bytes). ` +
      `Tengo ${oas.length} OA(s) reales del catálogo MINEDUC para evaluar tu trabajo. ` +
      `(Conecta aquí tu modelo multimodal para la retroalimentación real.)`;

    return {
      feedback_text,
      audio_response_b64: null as string | null,
    };
  });
