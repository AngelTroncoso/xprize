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
  id_oa: z.string().nullable().optional(),
});

export const sendChatMessageFn = createServerFn({ method: "POST" })
  .inputValidator((d) => ChatInput.parse(d))
  .handler(async ({ data }) => {
    const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:8000";
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        throw new Error(`Error del backend: ${res.status}`);
      }

      return res.json();
    } catch (error: any) {
      console.error("[chat] Error comunicando con backend:", error.message);
      throw new Error("No se pudo conectar con el motor de IA.");
    }
  });
