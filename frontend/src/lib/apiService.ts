// Capa de servicio del frontend.
// Ahora apunta a las Server Functions de TanStack Start (Supabase + service_role),
// reemplazando los endpoints de FastAPI en localhost:8000.
import { sendChatMessageFn } from "@/lib/superProfesor/chat.functions";
import { analyzeCanvasFn } from "@/lib/superProfesor/canvas.functions";
import { getStudentProgressFn } from "@/lib/superProfesor/progress.functions";
export { liveAudioTurnFn } from "@/lib/superProfesor/liveAudio.functions";
export { LiveAudioSession } from "@/lib/liveAudioService";
export type { LiveStatus, LiveTurnContext, LiveAudioCallbacks } from "@/lib/liveAudioService";

export const BACKEND_HINT =
  "No se pudo contactar al Super_Profesor en el servidor. Revisa que las claves de Supabase (EXTERNAL_SUPABASE_*) estén configuradas y que la server function esté desplegada.";

// -------------------- Tipos --------------------
export interface ChatRequest {
  student_id: string;
  curso: string;
  asignatura: string;
  message: string;
  session_id?: string;
  student_interest?: string;
  current_topic?: string;
  id_oa?: string | null;
}

export interface ChatResponse {
  response_text: string;
  audio_response_b64?: string | null;
}

export interface CanvasAnalyzeRequest {
  student_id: string;
  curso: string;
  asignatura: string;
  canvas_data: string; // base64 puro (sin "data:image/png;base64,")
}

export interface CanvasAnalyzeResponse {
  feedback_text: string;
  audio_response_b64?: string | null;
}

// Estado de logro normalizado en el frontend
export type OAStatus = "dominado" | "en_progreso" | "no_iniciado";

export interface OANode {
  code: string;
  title: string;
  concepts: string[];
  status: OAStatus;
}
export interface EjeNode {
  name: string;
  oas: OANode[];
}
export interface AsignaturaNode {
  name: string;
  ejes: EjeNode[];
}
export interface CursoNode {
  name: string;
  asignaturas: AsignaturaNode[];
}
export interface ProgressTree {
  student_id: number | string;
  student_name: string;
  cursos: CursoNode[];
}

// -------------------- Helpers --------------------
/** Convierte un Base64 (audio mp3/wav) en un ObjectURL listo para <audio>. */
export function base64ToAudioUrl(b64: string, mime = "audio/mpeg"): string {
  const clean = b64.includes(",") ? b64.split(",")[1] : b64;
  const bytes = atob(clean);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return URL.createObjectURL(new Blob([arr], { type: mime }));
}

/** Quita el prefijo data:image/...;base64, si viene incluido. */
export function stripDataUrl(dataUrl: string): string {
  return dataUrl.includes(",") ? dataUrl.split(",")[1] : dataUrl;
}

const BACKEND_URL =
  (import.meta as any).env?.VITE_BACKEND_URL ?? "https://superprofesor-backend-253925950091.us-central1.run.app";

// -------------------- Llamadas (server functions) --------------------
export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  return sendChatMessageFn({ data: payload });
}

export async function analyzeCanvas(
  payload: CanvasAnalyzeRequest,
): Promise<CanvasAnalyzeResponse> {
  return analyzeCanvasFn({ data: payload });
}

export async function getStudentProgress(
  studentId: number | string,
): Promise<ProgressTree> {
  const raw = await getStudentProgressFn({ data: { student_id: studentId } });
  return normalizeProgress(raw);
}

// -------------------- Normalización del Árbol de Progreso --------------------
export function mapMasteryToStatus(level: unknown): OAStatus {
  if (typeof level === "number") {
    if (level >= 0.8) return "dominado";
    if (level > 0) return "en_progreso";
    return "no_iniciado";
  }
  const s = String(level ?? "").toLowerCase();
  if (["mastered", "dominado", "domain", "logrado", "achieved"].includes(s)) return "dominado";
  if (
    ["in_progress", "en_progreso", "progress", "partial", "ongoing", "developing"].includes(s)
  )
    return "en_progreso";
  return "no_iniciado";
}

function normalizeProgress(raw: any): ProgressTree {
  const cursos = (raw?.cursos ?? raw?.courses ?? []).map((c: any) => ({
    name: c.name ?? c.curso ?? "Curso",
    asignaturas: (c.asignaturas ?? c.subjects ?? []).map((a: any) => ({
      name: a.name ?? a.asignatura ?? "Asignatura",
      ejes: (a.ejes ?? a.axes ?? []).map((e: any) => ({
        name: e.name ?? e.eje ?? "Eje",
        oas: (e.oas ?? e.objectives ?? []).map((o: any) => ({
          code: o.code ?? o.oa_code ?? o.id ?? "OA",
          title: o.title ?? o.description ?? "",
          concepts: o.concepts ?? o.tags ?? [],
          status: mapMasteryToStatus(o.status ?? o.mastery_level ?? o.mastery),
        })),
      })),
    })),
  }));
  return {
    student_id: raw?.student_id ?? raw?.id ?? 1,
    student_name: raw?.student_name ?? raw?.name ?? "Estudiante",
    cursos,
  };
}
