"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import {
  Pencil,
  Eraser,
  Undo2,
  Trash2,
  Send,
  Loader2,
  Paintbrush,
} from "lucide-react";

const COLORS = ["#000000", "#2563eb", "#dc2626", "#16a34a", "#9333ea", "#d97706"];
const BRUSH_SIZES = [3, 6, 10, 16];

export interface CanvasResponse {
  agent: string;
  student_id: string;
  visual_analysis: string;
  pedagogic_feedback: string;
  comprehension_level: string;
  mastery_advancement: number;
  oa_metadata?: Record<string, unknown>;
  audio_feedback_b64?: string;
  audio_mime_type?: string;
}

interface PizarraModalProps {
  studentId?: string | null;
  curso?: string;
  asignatura?: string;
  onClose: () => void;
  onFeedback: (msg: {
    content: string;
    agent_used?: string;
    oa_metadata?: Record<string, unknown>;
    role: "assistant";
  }) => void;
}

export default function PizarraModal({ studentId, curso, asignatura, onClose, onFeedback }: PizarraModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState("#000000");
  const [brushSize, setBrushSize] = useState(6);
  const [tool, setTool] = useState<"pen" | "eraser">("pen");
  const [history, setHistory] = useState<ImageData[]>([]);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<CanvasResponse | null>(null);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    saveState();
  }, []);

  const getPos = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    return {
      x: (clientX - rect.left) * (canvas.width / rect.width),
      y: (clientY - rect.top) * (canvas.height / rect.height),
    };
  }, []);

  const startDrawing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    const pos = getPos(e);
    lastPoint.current = pos;
    setIsDrawing(true);
  }, [getPos]);

  const draw = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const pos = getPos(e);
    if (!lastPoint.current) {
      lastPoint.current = pos;
      return;
    }
    ctx.beginPath();
    ctx.moveTo(lastPoint.current.x, lastPoint.current.y);
    ctx.lineTo(pos.x, pos.y);
    ctx.strokeStyle = tool === "eraser" ? "#1a1a2e" : color;
    ctx.lineWidth = tool === "eraser" ? brushSize * 2 : brushSize;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
    lastPoint.current = pos;
  }, [isDrawing, getPos, color, brushSize, tool]);

  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
    lastPoint.current = null;
    saveState();
  }, []);

  const saveState = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
    setHistory((prev) => [...prev.slice(-19), data]);
  };

  const undo = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    if (history.length < 2) return;
    const prev = history[history.length - 2];
    ctx.putImageData(prev, 0, 0);
    setHistory((prev) => prev.slice(0, -1));
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setHistory([]);
    saveState();
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "z") {
        e.preventDefault();
        undo();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [history]);

  const sendToTeacher = async () => {
    if (!canvasRef.current || !studentId || !curso || !asignatura) return;
    setSending(true);
    setResult(null);

    const dataUrl = canvasRef.current.toDataURL("image/png");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/canvas/analyze`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            student_id: studentId,
            curso,
            asignatura,
            canvas_data: dataUrl,
            prompt_adicional: "El estudiante dibujó algo relacionado con matemáticas",
            enable_audio: false,
          }),
        }
      );

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || "Error al analizar");
      }

      const data: CanvasResponse = await res.json();
      setResult(data);

      const teacherMessage = {
        role: "assistant" as const,
        content: data.pedagogic_feedback || data.visual_analysis,
        agent_used: data.agent,
        oa_metadata: data.oa_metadata,
      };

      onFeedback(teacherMessage);
    } catch (err) {
      setResult({
        agent: "Error",
        student_id: studentId ?? "",
        visual_analysis: "",
        pedagogic_feedback: err instanceof Error ? err.message : "Error de conexión",
        comprehension_level: "emerging",
        mastery_advancement: 0,
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 12 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="w-full max-w-5xl glass-panel rounded-2xl my-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Pizarra Interactiva</h2>
            <p className="text-xs text-gray-400">
              Dibuja tu ejercicio y envía al profesor para recibir feedback
            </p>
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-300 hover:text-white"
          >
            Cerrar
          </button>
        </div>

        <div className="p-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setTool("pen")}
                className={`p-2 rounded-lg transition-all ${
                  tool === "pen"
                    ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Pencil className="w-5 h-5" />
              </button>
              <button
                onClick={() => setTool("eraser")}
                className={`p-2 rounded-lg transition-all ${
                  tool === "eraser"
                    ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Eraser className="w-5 h-5" />
              </button>

              <div className="w-px h-6 bg-white/10 mx-1" />

              {COLORS.map((c) => (
                <button
                  key={c}
                  onClick={() => {
                    setColor(c);
                    setTool("pen");
                  }}
                  className={`w-6 h-6 rounded-full border-2 transition-all ${
                    color === c && tool === "pen"
                      ? "border-white scale-110"
                      : "border-transparent"
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}

              <div className="w-px h-6 bg-white/10 mx-1" />

              {BRUSH_SIZES.map((s) => (
                <button
                  key={s}
                  onClick={() => setBrushSize(s)}
                  className={`p-1.5 rounded-lg transition-all ${
                    brushSize === s
                      ? "bg-indigo-500/20 text-indigo-400"
                      : "text-gray-400 hover:text-white"
                  }`}
                  title={`${s}px`}
                >
                  <div
                    className="rounded-full bg-current mx-auto"
                    style={{ width: Math.min(s + 2, 18), height: Math.min(s + 2, 18) }}
                  />
                </button>
              ))}

              <div className="w-px h-6 bg-white/10 mx-1" />

              <button
                onClick={undo}
                disabled={history.length < 2}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 disabled:opacity-30"
                title="Deshacer (Ctrl+Z)"
              >
                <Undo2 className="w-5 h-5" />
              </button>
              <button
                onClick={clearCanvas}
                className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/5"
                title="Limpiar"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>

            <div className="rounded-2xl overflow-hidden border border-white/5">
              <canvas
                ref={canvasRef}
                width={800}
                height={500}
                className="w-full cursor-crosshair touch-none"
                style={{ aspectRatio: "800/500", background: "#1a1a2e" }}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                onTouchStart={startDrawing}
                onTouchMove={draw}
                onTouchEnd={stopDrawing}
              />
            </div>
          </div>

          <div className="space-y-3">
            {sending && (
              <div className="rounded-2xl p-6 flex flex-col items-center justify-center text-center border border-white/5">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400 mb-3" />
                <p className="text-sm text-gray-400">Analizando tu dibujo...</p>
              </div>
            )}

            {result && !sending && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl p-4 space-y-3 border border-white/5"
              >
                <h3 className="text-sm font-semibold">Feedback del Profesor</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-500">Nivel:</span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      result.comprehension_level === "advanced"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : result.comprehension_level === "proficient"
                        ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                        : result.comprehension_level === "developing"
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-gray-500/10 text-gray-400 border border-gray-500/20"
                    }`}
                  >
                    {result.comprehension_level === "advanced"
                      ? "Avanzado"
                      : result.comprehension_level === "proficient"
                      ? "Competente"
                      : result.comprehension_level === "developing"
                      ? "En desarrollo"
                      : "Emergente"}
                  </span>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 mb-1">Análisis</p>
                  <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {result.visual_analysis || result.pedagogic_feedback}
                  </p>
                </div>
              </motion.div>
            )}

            <button
              onClick={sendToTeacher}
              disabled={!studentId || !curso || !asignatura || sending}
              className="w-full flex items-center justify-center gap-2 bg-gradient-accent text-white px-4 py-3 rounded-xl font-bold text-sm hover:opacity-95 disabled:opacity-40"
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Enviar al Profesor
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}