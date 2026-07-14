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

export const analyzeCanvasFn = createServerFn({ method: "POST" })
  .inputValidator((d) => CanvasInput.parse(d))
  .handler(async ({ data }) => {
    const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:8000";
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/canvas/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        throw new Error(`Error del backend: ${res.status}`);
      }

      return res.json();
    } catch (error: any) {
      console.error("[canvas] Error comunicando con backend:", error.message);
      throw new Error("No se pudo analizar la pizarra.");
    }
  });
