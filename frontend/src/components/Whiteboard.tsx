import { useEffect, useMemo, useRef, useState } from "react";
import { Eraser, Pencil, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  BACKEND_HINT,
  analyzeCanvas,
  base64ToAudioUrl,
  stripDataUrl,
} from "@/lib/apiService";
import { getSubjectTheme } from "@/lib/subjectTheme";

const COLORS = ["#1f2937", "#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#a855f7"];

type Tool = "pencil" | "eraser";

import { InteractiveExercise } from "@/lib/apiService";
import { ExerciseOverlay } from "./exercises/ExerciseOverlay";

interface WhiteboardProps {
  curso: string;
  asignatura: string;
  studentId?: string;
  activeExercise?: InteractiveExercise | null;
  onFeedback?: (text: string, audioUrl?: string) => void;
}

export function Whiteboard({
  curso,
  asignatura,
  studentId = "1",
  activeExercise,
  onFeedback,
}: WhiteboardProps) {
  const theme = useMemo(() => getSubjectTheme(asignatura), [asignatura]);
  const SubjectIcon = theme.icon;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const [tool, setTool] = useState<Tool>("pencil");
  const [color, setColor] = useState<string>(COLORS[0]);
  const [size, setSize] = useState<number>(4);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const parent = canvas.parentElement!;
    const resize = () => {
      const { width, height } = parent.getBoundingClientRect();
      const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
      canvas.width = width;
      canvas.height = height;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.putImageData(img, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  const getPos = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const start = (e: React.PointerEvent<HTMLCanvasElement>) => {
    drawing.current = true;
    const ctx = canvasRef.current!.getContext("2d")!;
    const { x, y } = getPos(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };
  const move = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current) return;
    const ctx = canvasRef.current!.getContext("2d")!;
    const { x, y } = getPos(e);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineWidth = tool === "eraser" ? size * 4 : size;
    ctx.strokeStyle = tool === "eraser" ? "#ffffff" : color;
    ctx.lineTo(x, y);
    ctx.stroke();
  };
  const end = () => {
    drawing.current = false;
  };

  const clear = () => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  };

  const send = async () => {
    const canvas = canvasRef.current!;
    const dataUrl = canvas.toDataURL("image/png");
    const canvas_data = stripDataUrl(dataUrl);
    setSending(true);
    try {
      const res = await analyzeCanvas({
        student_id: studentId,
        curso,
        asignatura,
        canvas_data,
      });
      const audioUrl = res.audio_response_b64
        ? base64ToAudioUrl(res.audio_response_b64)
        : undefined;
      onFeedback?.(`📝 ${res.feedback_text}`, audioUrl);
      toast.success("¡Pizarra enviada! Tu profe ya respondió.");
    } catch (err) {
      console.error(err);
      toast.error("Backend no disponible", { description: BACKEND_HINT });
      onFeedback?.(
        "No pude analizar tu pizarra porque el servidor no respondió. Pide ayuda para encender el backend FastAPI en el puerto 8000 🛠️",
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div className={`flex h-[500px] lg:h-full flex-col gap-3 rounded-3xl border-2 ${theme.border} bg-white/80 p-4 backdrop-blur-xl ${theme.glow}`}>
      <div className={`flex items-center gap-2 rounded-2xl ${theme.softBg} px-3 py-2`}>
        <div className={`grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br ${theme.gradient} text-white shadow`}>
          <SubjectIcon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className={`text-xs font-bold uppercase tracking-wide ${theme.text}`}>Pizarra</p>
          <p className="truncate text-[11px] text-foreground/60">{theme.label} · {curso}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant={tool === "pencil" ? "default" : "outline"}
          onClick={() => setTool("pencil")}
          className="rounded-full"
        >
          <Pencil className="mr-1 h-4 w-4" /> Lápiz
        </Button>
        <Button
          size="sm"
          variant={tool === "eraser" ? "default" : "outline"}
          onClick={() => setTool("eraser")}
          className="rounded-full"
        >
          <Eraser className="mr-1 h-4 w-4" /> Goma
        </Button>
        <Button size="sm" variant="outline" onClick={clear} className="rounded-full">
          <Trash2 className="mr-1 h-4 w-4" /> Limpiar
        </Button>
        <div className="ml-auto flex items-center gap-1">
          {COLORS.map((c) => (
            <button
              key={c}
              onClick={() => {
                setColor(c);
                setTool("pencil");
              }}
              aria-label={`color ${c}`}
              className={`h-7 w-7 rounded-full border-2 transition ${
                color === c ? "scale-110 border-foreground" : "border-white"
              }`}
              style={{ backgroundColor: c }}
            />
          ))}
        </div>
        <input
          type="range"
          min={2}
          max={20}
          value={size}
          onChange={(e) => setSize(Number(e.target.value))}
          className="ml-2 w-24"
        />
      </div>

      <div className={`relative flex-1 overflow-hidden rounded-2xl border-2 border-dashed ${theme.border} bg-white`}>
        <canvas
          ref={canvasRef}
          onPointerDown={start}
          onPointerMove={move}
          onPointerUp={end}
          onPointerLeave={end}
          className="h-full w-full cursor-crosshair touch-none"
        />
        {!activeExercise && (
          <div className="pointer-events-none absolute bottom-2 right-3 text-[11px] font-semibold text-foreground/30">
            {theme.emoji} Dibuja aquí
          </div>
        )}
        {activeExercise && (
          <div className="absolute inset-0 z-10 flex items-start justify-center p-4 pointer-events-none">
            <div className="pointer-events-auto w-full max-w-2xl mt-2 max-h-full">
              <ExerciseOverlay exercise={activeExercise} />
            </div>
          </div>
        )}
      </div>

      <Button
        onClick={send}
        disabled={sending}
        className={`h-12 rounded-full bg-gradient-to-r ${theme.gradient} text-base font-bold text-white shadow-md hover:brightness-110`}
      >
        <Send className="mr-2 h-5 w-5" />
        {sending ? "Enviando..." : "Enviar mi Pizarra al Profesor"}
      </Button>
    </div>
  );
}
