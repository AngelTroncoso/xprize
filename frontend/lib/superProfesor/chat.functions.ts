/**
 * chat.functions.ts — Server Functions de Supabase para el Modo Audio en Tiempo Real
 *
 * Tarea 1: Pipeline de Baja Latencia para Audio Educativo
 * - Recibe ráfagas cortas de audio (Base64) desde el frontend
 * - Consulta curriculum_objectives usando getExternalAdmin() con el id_oa
 * - Recupera contexto pedagógico exacto (descripción, conceptos clave, indicadores)
 * - Inyecta prompt de sistema con identidad de "Súper Profesor" + currículo MINEDUC
 * - Envía a Gemini (vía FastAPI) y retorna el audio generado
 */

import { createClient } from "@supabase/supabase-js";

// ─── Tipos ───────────────────────────────────────────────────────────────────

export interface PedagogicalContext {
  id_oa: string;
  curso: string;
  asignatura: string;
  descripcion: string;
  conceptos_clave: string[];
  indicadores_evaluacion: string[];
}

export interface AudioChunkPayload {
  student_id: string;
  session_id: string;
  curso: string;
  asignatura: string;
  id_oa: string;
  audio_base64: string;
  /** Timestamp UTC ISO del chunk para correlación */
  chunk_ts?: string;
}

export interface AudioResponse {
  audio_base64: string;
  mime_type: string;
  session_id: string;
  /** Texto transcrito + respuesta pedagógica (útil para logging) */
  transcript: string;
}

// ─── Constantes ──────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Cliente Admin Supabase ──────────────────────────────────────────────────

/**
 * Obtiene un cliente Supabase con rol service_role (solo server-side).
 * En Next.js App Router, usar desde Server Components / Route Handlers / Server Actions.
 *
 * Ejemplo (Server Action o Route Handler):
 *   import { getExternalAdmin } from './chat.functions';
 *   const supabase = getExternalAdmin();
 */
export function getExternalAdmin() {
  const supabaseUrl =
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    process.env.SUPABASE_URL ||
    "";

  const supabaseKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_KEY ||
    "";

  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      "Faltan variables de entorno SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY"
    );
  }

  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}

// ─── Consulta Curricular Optimizada ─────────────────────────────────────────

/**
 * Consulta curriculum_objectives usando el id_oa y retorna el contexto
 * pedagógico completo necesario para el prompt de Gemini.
 *
 * Usa getExternalAdmin() para evitar RLS y ser lo más rápido posible.
 * La consulta se hace con índices天然的 sobre (curso, asignatura, id_oa).
 */
export async function fetchPedagogicalContext(
  curso: string,
  asignatura: string,
  id_oa: string
): Promise<PedagogicalContext | null> {
  const supabase = getExternalAdmin();

  // Consulta directa al índice compuesto (curso, asignatura, id_oa)
  const { data, error } = await supabase
    .from("curriculum_objectives")
    .select(
      `
      id_oa,
      curso,
      asignatura,
      descripcion,
      conceptos_clave,
      indicadores_evaluacion
    `
    )
    .eq("curso", curso)
    .eq("asignatura", asignatura)
    .eq("id_oa", id_oa)
    .limit(1)
    .maybeSingle();

  if (error) {
    console.error("[chat.functions] Error consultando curriculum_objectives:", error);
    return null;
  }

  if (!data) {
    console.warn(
      `[chat.functions] No se encontró OA: curso=${curso}, asignatura=${asignatura}, id_oa=${id_oa}`
    );
    return null;
  }

  return {
    id_oa: data.id_oa,
    curso: data.curso,
    asignatura: data.asignatura,
    descripcion: data.descripcion,
    conceptos_clave: data.conceptos_clave || [],
    indicadores_evaluacion: data.indicadores_evaluacion || [],
  };
}

// ─── Construcción de Prompt del Sistema ──────────────────────────────────────

/**
 * Construye el prompt del sistema para Gemini en formato "Súper Profesor".
 * Inyecta el contexto pedagógico del OA del MINEDUC.
 */
export function buildSuperProfesorSystemPrompt(ctx: PedagogicalContext): string {
  const conceptos = ctx.conceptos_clave.join(", ");
  const indicadores = ctx.indicadores_evaluacion.join(", ");

  return `Actúas como Súper Profesor para un alumno de ${ctx.curso} en Chile. Asignatura: ${ctx.asignatura}. Objetivo de Aprendizaje actual: ${ctx.descripcion}. Conceptos clave: ${conceptos}. Indicadores de evaluación: ${indicadores}. Mantén un tono sumamente lúdico, empático, usa analogías simples para niños y fomenta la curiosidad. Responde directamente en formato de audio optimizado para su reproducción instantánea.`;
}

// ─── Envío de Audio a FastAPI ────────────────────────────────────────────────

/**
 * Envía un chunk de audio al backend FastAPI para generar la respuesta
 * pedagógica con Gemini y retorna el audio de respuesta.
 *
 * @returns AudioResponse con el audio generado + metadatos
 */
export async function sendAudioChunk(
  payload: AudioChunkPayload
): Promise<AudioResponse> {
  const endpoint = `${API_BASE}/api/audio/process-chunk`;

  // Obtener token de sesión para autorización
  const { createClient } = await import("@/lib/supabase/client");
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify({
      ...payload,
      chunk_ts: payload.chunk_ts || new Date().toISOString(),
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`[chat.functions] Error en audio chunk: ${response.status} — ${errorText}`);
  }

  return response.json();
}

// ─── Función Compuesta: Consulta OA + Envío de Audio ─────────────────────────

/**
 * Función optimizada de alto nivel que:
 * 1. Consulta el contexto pedagógico del OA en Supabase (getExternalAdmin)
 * 2. Construye el prompt del sistema con identidad Súper Profesor + MINEDUC
 * 3. Envía el chunk de audio al backend para procesamiento con Gemini
 * 4. Retorna el audio de respuesta listo para reproducir
 *
 * Diseñada para ser llamada desde Server Actions o Route Handlers de Next.js.
 */
export async function processAudioWithPedagogicalContext(
  params: AudioChunkPayload
): Promise<AudioResponse> {
  const { curso, asignatura, id_oa, student_id, session_id, audio_base64 } = params;

  // 1. Consultar contexto pedagógico del OA
  const ctx = await fetchPedagogicalContext(curso, asignatura, id_oa);

  if (!ctx) {
    console.warn(
      `[chat.functions] Contexto pedagógico no encontrado para ${id_oa}. Enviando sin contexto curricular.`
    );
  }

  // 2. Construir sistema prompt
  const systemPrompt = ctx
    ? buildSuperProfesorSystemPrompt(ctx)
    : `Actúas como Súper Profesor para un alumno de ${curso} en Chile. Asignatura: ${asignatura}. Mantén un tono sumamente lúdico, empático, usa analogías simples para niños y fomenta la curiosidad.`;

  // 3. Enviar chunk de audio con el contexto
  const response = await sendAudioChunk({
    student_id,
    session_id,
    curso,
    asignatura,
    id_oa,
    audio_base64,
    chunk_ts: new Date().toISOString(),
  });

  return {
    ...response,
    // Podríamos enriquecer la respuesta con el contexto usado
    transcript: `[Contexto: ${ctx?.descripcion || "sin OA"}]\n${response.transcript}`,
  };
}

// ─── WebSocket Client para Audio en Tiempo Real ──────────────────────────────

/**
 * Conecta al WebSocket de baja latencia en FastAPI (/api/live)
 * y gestiona el flujo bidireccional de audio en tiempo real.
 *
 * @param params - Parámetros de sesión y contexto pedagógico
 * @param onAudioChunk - Callback cuando llega un chunk de audio de Gemini
 * @param onError - Callback de error
 * @returns Función para enviar audio del micrófono y cerrar conexión
 */
export function connectLiveAudio(
  params: {
    student_id: string;
    session_id: string;
    curso: string;
    asignatura: string;
    id_oa: string;
  },
  onAudioChunk: (chunk: string) => void,
  onError: (error: Event) => void
): {
  sendAudio: (base64Chunk: string) => void;
  close: () => void;
} {
  const wsUrl = API_BASE.replace(/^http/, "ws");
  const ws = new WebSocket(`${wsUrl}/api/live`);

  let isReady = false;
  const pendingChunks: string[] = [];

  ws.onopen = () => {
    // Enviar mensaje de inicialización con contexto pedagógico
    const initMsg = {
      type: "init",
      session_id: params.session_id,
      student_id: params.student_id,
      curso: params.curso,
      asignatura: params.asignatura,
      id_oa: params.id_oa,
    };
    ws.send(JSON.stringify(initMsg));
    isReady = true;

    // Drenar chunks pendientes
    for (const chunk of pendingChunks) {
      ws.send(chunk);
    }
    pendingChunks.length = 0;
  };

  ws.onmessage = (event: MessageEvent) => {
    // El backend envía chunks de audio en Base64 como mensajes de texto
    // o directamente como Blob binario
    if (event.data instanceof Blob) {
      // Convertir Blob a Base64 para consistencia
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // El resultado incluye el prefijo data:application/octet-stream;base64,
        // extraemos solo la parte Base64
        const base64 = result.split(",")[1] || result;
        onAudioChunk(base64);
      };
      reader.readAsDataURL(event.data);
    } else {
      // Mensaje de texto: puede ser audio Base64 o metadatos
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "audio" && msg.base64) {
          onAudioChunk(msg.base64);
        } else if (msg.type === "error") {
          console.error("[live-audio] Error del backend:", msg.message);
        }
      } catch {
        // Si no es JSON, tratar como audio Base64 plano
        onAudioChunk(event.data);
      }
    }
  };

  ws.onerror = onError;

  ws.onclose = () => {
    isReady = false;
  };

  return {
    sendAudio: (base64Chunk: string) => {
      if (!isReady) {
        // Bufferear hasta que el WebSocket esté abierto
        pendingChunks.push(base64Chunk);
        return;
      }
      ws.send(base64Chunk);
    },
    close: () => {
      ws.close();
    },
  };
}