"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { fetchApi } from "@/lib/api";
import { COURSES, getSubjectsForCourse } from "@/lib/curriculum";
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

interface CanvasResponse {
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

export default function PizarraPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState("#000000");
  const [brushSize, setBrushSize] = useState(6);
  const [tool, setTool] = useState<"pen" | "eraser">("pen");
  const [history, setHistory] = useState<ImageData[]>([]);
  const [studentId, setStudentId] = useState<string | null>(null);
  const [curso, setCurso] = useState("");
  const [asignatura, setAsignatura] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<CanvasResponse | null>(null);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) setStudentId(user.id);
    });
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    saveState();
  }, []);

  const getPos = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      const canvas = canvasRef.current;
      if (!canvas) return { x: 0, y: 0 };
      const rect = canvas.getBoundingClientRect();
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
      return {
        x: (clientX - rect.left) * (canvas.width / rect.width),
        y: (clientY - rect.top) * (canvas.height / rect.height),
      };
    },
    []
  );

  const startDrawing = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      e.preventDefault();
      const pos = getPos(e);
      lastPoint.current = pos;
      setIsDrawing(true);
    },
    [getPos]
  );

  const draw = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
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
    },
    [isDrawing, getPos, color, brushSize, tool]
  );

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

  // Keyboard shortcut: Ctrl+Z -> undo
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-6xl mx-auto space-y-6"
    >
      <div>
        <h1 className="text-2xl font-bold">Pizarra Interactiva</h1>
        <p className="text-gray-400 text-sm mt-1">
          Dibuja tus ejercicios y recibe feedback del Super_Profesor
        </p>
      </div>

      {/* Course / Subject selectors */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Curso:</label>
          <select
            value={curso}
            onChange={(e) => {
              setCurso(e.target.value);
              setAsignatura("");
            }}
            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-indigo-500/50"
          >
            <option value="">Seleccionar</option>
            {COURSES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Asignatura:</label>
          <select
            value={asignatura}
            onChange={(e) => setAsignatura(e.target.value)}
            disabled={!curso}
            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-indigo-500/50 disabled:opacity-40"
          >
            <option value="">Seleccionar</option>
            {curso &&
              getSubjectsForCourse(curso).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Canvas */}
        <div className="lg:col-span-2 space-y-4">
          {/* Toolbar */}
          <div className="glass-panel rounded-2xl p-3 flex flex-wrap items-center gap-3">
            {/* Tools */}
            <button
              onClick={() => setTool("pen")}
              className={`p-2 rounded-lg transition-all ${
                tool === "pen"
                  ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
              title="Lápiz"
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
              title="Borrador"
            >
              <Eraser className="w-5 h-5" />
            </button>

            <div className="w-px h-6 bg-white/10 mx-1" />

            {/* Colors */}
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
                title={c}
              />
            ))}

            <div className="w-px h-6 bg-white/10 mx-1" />

            {/* Brush sizes */}
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

            {/* Actions */}
            <button
              onClick={undo}
              disabled={history.length < 2}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 disabled:opacity-30 transition-all"
              title="Deshacer (Ctrl+Z)"
            >
              <Undo2 className="w-5 h-5" />
            </button>
            <button
              onClick={clearCanvas}
              className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/5 transition-all"
              title="Limpiar"
            >
              <Trash2 className="w-5 h-5" />
            </button>

            <div className="flex-1" />

            <button
              onClick={sendToTeacher}
              disabled={!studentId || !curso || !asignatura || sending}
              className="flex items-center gap-2 bg-gradient-accent text-white px-4 py-2 rounded-xl font-bold text-sm hover:opacity-95 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Enviar al Profesor
            </button>
          </div>

          {/* Canvas */}
          <div className="glass-panel rounded-2xl p-2">
            <canvas
              ref={canvasRef}
              width={800}
              height={500}
              className="w-full rounded-xl cursor-crosshair touch-none"
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

        {/* Result panel */}
        <div className="space-y-4">
          {sending && (
            <div className="glass-panel rounded-2xl p-6 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400 mb-4" />
              <p className="text-sm text-gray-400">
                Analizando tu dibujo...
              </p>
            </div>
          )}

          {result && !sending && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-panel rounded-2xl p-6 space-y-4"
            >
              <h3 className="text-sm font-semibold">Feedback del Profesor</h3>

              {result.comprehension_level && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Nivel:</span>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
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
              )}

              {result.mastery_advancement > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Avance</p>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all"
                      style={{ width: `${Math.round(result.mastery_advancement * 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {Math.round(result.mastery_advancement * 100)}%
                  </p>
                </div>
              )}

              <div>
                <p className="text-xs text-gray-500 mb-1">Análisis visual</p>
                <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {result.visual_analysis || result.pedagogic_feedback}
                </p>
              </div>

              {result.pedagogic_feedback && result.pedagogic_feedback !== result.visual_analysis && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Feedback</p>
                  <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {result.pedagogic_feedback}
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {!result && !sending && (
            <div className="glass-panel rounded-2xl p-6 text-center">
              <Paintbrush className="w-10 h-10 text-gray-600 mx-auto mb-3" />
              <p className="text-sm text-gray-500">
                Dibuja algo en la pizarra y presiona "Enviar al Profesor" para recibir feedback
              </p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}