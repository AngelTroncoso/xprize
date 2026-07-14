import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, Radio, Square, X } from "lucide-react";
import { toast } from "sonner";
import { getSubjectTheme } from "@/lib/subjectTheme";
import {
  LiveAudioSession,
  type LiveStatus,
} from "@/lib/liveAudioService";

interface LiveAudioModalProps {
  open: boolean;
  onClose: () => void;
  curso: string;
  asignatura: string;
  studentId: string;
  activeIdOa?: string | null;
}

const STATUS_COPY: Record<LiveStatus, { title: string; sub: string }> = {
  idle: { title: "Listo para escucharte", sub: "Toca el micrófono y cuéntame 💬" },
  listening: { title: "Te estoy escuchando…", sub: "Habla con confianza, sin apuro 🎙️" },
  thinking: { title: "Pensando tu respuesta…", sub: "Estoy preparando algo genial ✨" },
  speaking: { title: "Super_Profesor responde", sub: "Toca para interrumpir y hablar 🔊" },
  error: { title: "Hubo un problemita", sub: "Inténtalo otra vez 🙏" },
};

export function LiveAudioModal({
  open,
  onClose,
  curso,
  asignatura,
  studentId,
  activeIdOa = null,
}: LiveAudioModalProps) {
  const theme = useMemo(() => getSubjectTheme(asignatura), [asignatura]);
  const [status, setStatus] = useState<LiveStatus>("idle");
  const [level, setLevel] = useState(0);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const sessionRef = useRef<LiveAudioSession | null>(null);

  // Crear / refrescar la sesión cuando se abre
  useEffect(() => {
    if (!open) return;
    const s = new LiveAudioSession(
      { student_id: studentId, curso, asignatura, active_id_oa: activeIdOa },
      {
        onStatus: setStatus,
        onLevel: setLevel,
        onTranscript: setTranscript,
        onResponse: setResponse,
        onError: (err) => {
          console.error(err);
          toast.error("Audio en vivo", { description: err.message });
        },
      },
    );
    sessionRef.current = s;
    return () => {
      void s.close();
      sessionRef.current = null;
      setStatus("idle");
      setLevel(0);
      setTranscript("");
      setResponse("");
    };
  }, [open, studentId, curso, asignatura, activeIdOa]);

  // Mantener el contexto en sync (por si cambian sin cerrar)
  useEffect(() => {
    sessionRef.current?.updateContext({
      student_id: studentId,
      curso,
      asignatura,
      active_id_oa: activeIdOa,
    });
  }, [studentId, curso, asignatura, activeIdOa]);

  if (!open) return null;

  const handlePrimary = async () => {
    const s = sessionRef.current;
    if (!s) return;
    if (status === "listening") {
      await s.stopListening();
    } else if (status === "speaking" || status === "thinking") {
      // Interrupción tipo Gemini Live
      s.stopSpeaking();
      await s.startListening();
    } else {
      await s.startListening();
    }
  };

  const copy = STATUS_COPY[status];
  const isListening = status === "listening";
  const isSpeaking = status === "speaking";
  const isThinking = status === "thinking";

  // 5 barras animadas con amplitudes derivadas del level
  const bars = [0.6, 0.9, 1.2, 0.9, 0.6];

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/60 p-4 backdrop-blur-sm animate-fade-in">
      <div
        className={`relative w-full max-w-md overflow-hidden rounded-[2rem] border-2 ${theme.border} bg-white shadow-2xl ${theme.glow} animate-scale-in`}
      >
        {/* Header */}
        <div
          className={`flex items-center gap-3 bg-gradient-to-r ${theme.gradient} px-5 py-4 text-white`}
        >
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-white/20 ring-1 ring-white/40 backdrop-blur">
            <Radio className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-extrabold tracking-tight">
              Modo Audio en Vivo {theme.emoji}
            </h3>
            <p className="truncate text-xs text-white/85">
              {asignatura} · {curso}
              {activeIdOa ? ` · ${activeIdOa}` : ""}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Cerrar"
            className="grid h-9 w-9 place-items-center rounded-full bg-white/15 text-white transition hover:bg-white/25"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Visualizador */}
        <div className="relative grid place-items-center px-6 py-10">
          {/* Aros pulsantes */}
          <div
            className={`absolute h-56 w-56 rounded-full bg-gradient-to-br ${theme.gradient} opacity-20 blur-2xl transition-transform duration-300`}
            style={{
              transform: `scale(${1 + (isListening ? level * 0.6 : isSpeaking ? 0.5 : isThinking ? 0.25 : 0.1)})`,
            }}
          />
          <div
            className={`relative grid h-40 w-40 place-items-center rounded-full bg-gradient-to-br ${theme.gradient} text-white shadow-xl ${
              isListening ? "animate-pulse" : ""
            }`}
          >
            {/* Barras de onda */}
            <div className="flex items-end gap-1.5">
              {bars.map((mult, i) => {
                const base = 12;
                const dyn =
                  isListening ? level * 60 * mult :
                  isSpeaking ? (0.35 + Math.sin((Date.now() / 120) + i) * 0.25 + 0.4) * 40 :
                  isThinking ? 14 + Math.sin((Date.now() / 250) + i) * 6 :
                  10;
                return (
                  <span
                    key={i}
                    className="block w-2 rounded-full bg-white/95 transition-[height] duration-75"
                    style={{ height: `${Math.max(8, base + dyn)}px` }}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Copy de estado */}
        <div className="px-6 pb-4 text-center">
          <p className={`text-base font-extrabold ${theme.text}`}>{copy.title}</p>
          <p className="mt-1 text-sm text-foreground/60">{copy.sub}</p>
          {transcript && (
            <p className="mx-auto mt-4 max-w-sm rounded-2xl bg-slate-100 px-3 py-2 text-left text-xs text-foreground/70">
              <span className="font-bold">Tú:</span> {transcript}
            </p>
          )}
          {response && (
            <p
              className={`mx-auto mt-2 max-w-sm rounded-2xl ${theme.softBg} px-3 py-2 text-left text-xs ${theme.text}`}
            >
              <span className="font-bold">Profe:</span> {response}
            </p>
          )}
        </div>

        {/* Controles */}
        <div className="flex items-center justify-center gap-3 border-t border-slate-100 bg-white px-5 py-4">
          {(isSpeaking || isThinking) && (
            <button
              onClick={() => sessionRef.current?.stopSpeaking()}
              className="grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-700 transition hover:bg-slate-200"
              aria-label="Detener"
            >
              <Square className="h-4 w-4" fill="currentColor" />
            </button>
          )}

          <button
            onClick={handlePrimary}
            aria-label={isListening ? "Detener escucha" : "Hablar"}
            className={`group grid h-16 w-16 place-items-center rounded-full text-white shadow-lg transition-transform hover:scale-105 ${
              isListening
                ? "bg-red-500 animate-pulse"
                : `bg-gradient-to-br ${theme.gradient}`
            }`}
          >
            {isListening ? <MicOff className="h-7 w-7" /> : <Mic className="h-7 w-7" />}
          </button>

          <button
            onClick={onClose}
            className="grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-700 transition hover:bg-slate-200"
            aria-label="Cerrar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
