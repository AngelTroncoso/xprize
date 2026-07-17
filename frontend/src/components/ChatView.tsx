import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, Play, Radio, Send, Square } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Whiteboard } from "./Whiteboard";
import { LiveAudioModal } from "./LiveAudioModal";
import { BACKEND_HINT, base64ToAudioUrl, sendChatMessage } from "@/lib/apiService";
import { getSubjectTheme } from "@/lib/subjectTheme";

interface Message {
  id: string;
  role: "user" | "professor";
  text: string;
  audioUrl?: string;
}

interface ChatViewProps {
  curso: string;
  asignatura: string;
  studentId?: string;
  activeIdOa?: string | null;
  onBackToCatalog?: () => void;
}

export function ChatView({ curso, asignatura, studentId = "1", activeIdOa = null, onBackToCatalog }: ChatViewProps) {
  const [liveOpen, setLiveOpen] = useState(false);
  const theme = useMemo(() => getSubjectTheme(asignatura), [asignatura]);
  const SubjectIcon = theme.icon;
  const initial: Message[] = useMemo(
    () => [
      {
        id: "m1",
        role: "professor",
        text: `¡Hola! Soy tu Super_Profesor ${theme.emoji}. ${theme.greeting} Puedes hablarme, escribirme o dibujarme en la pizarra.`,
      },
    ],
    [theme.emoji, theme.greeting],
  );
  const [messages, setMessages] = useState<Message[]>(initial);
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [sending, setSending] = useState(false);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    audioRef.current = new Audio();
    audioRef.current.onended = () => setPlayingId(null);
    return () => {
      audioRef.current?.pause();
      audioRef.current = null;
    };
  }, []);

  const scroll = () => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  };

  const pushProfessor = (text: string, audioUrl?: string) => {
    const id = crypto.randomUUID();
    setMessages((m) => [...m, { id, role: "professor", text, audioUrl }]);
    scroll();
    if (audioUrl) playAudio(id, audioUrl);
  };

  const playAudio = (id: string, url: string) => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    audioRef.current.src = url;
    setPlayingId(id);
    audioRef.current.play().catch(() => setPlayingId(null));
  };

  const stopAudio = () => {
    audioRef.current?.pause();
    setPlayingId(null);
  };

  useEffect(() => {
    if (activeIdOa) {
      setMessages([]);
      handleSend(`[SISTEMA: Iniciar clase para OA]`, true);
    } else {
      setMessages(initial);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIdOa]);

  const handleSend = async (text?: string, isSystem = false) => {
    const content = (text ?? input).trim();
    if (!content || sending) return;
    
    if (!isSystem) {
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: content }]);
    }
    
    setInput("");
    setSending(true);
    scroll();
    try {
      const res = await sendChatMessage({
        student_id: studentId,
        curso,
        asignatura,
        message: content,
        id_oa: activeIdOa,
      });
      const audioUrl = res.audio_response_b64
        ? base64ToAudioUrl(res.audio_response_b64)
        : undefined;
      pushProfessor(res.response_text, audioUrl);
    } catch (err) {
      console.error(err);
      toast.error("Backend no disponible", { description: BACKEND_HINT });
      pushProfessor(
        "No pude conectarme con el servidor. Pídele a tu profe que encienda el backend (uvicorn en el puerto 8000) y vuelve a intentar 💡",
      );
    } finally {
      setSending(false);
    }
  };

  const handleMic = () => {
    const w = typeof window !== "undefined" ? (window as any) : null;
    const SR = w?.SpeechRecognition || w?.webkitSpeechRecognition;
    if (!SR) {
      toast.message("Tu navegador no soporta reconocimiento de voz", {
        description: "Prueba con Chrome o escribe tu pregunta.",
      });
      return;
    }
    const rec = new SR();
    rec.lang = "es-CL";
    rec.onstart = () => setListening(true);
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      handleSend(transcript);
    };
    rec.start();
  };

  return (
    <div className="flex flex-col lg:grid lg:h-[calc(100vh-220px)] lg:min-h-[560px] lg:grid-cols-[1fr_1fr] gap-4">
      {/* Chat */}
      <div className={`flex h-[600px] lg:h-full lg:min-h-0 flex-col overflow-hidden rounded-3xl border-2 ${theme.border} bg-white/80 backdrop-blur-xl ${theme.glow}`}>
        <div className={`flex items-center gap-3 border-b ${theme.border} bg-gradient-to-r ${theme.gradient} px-5 py-3 text-white`}>
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-white/20 backdrop-blur ring-1 ring-white/40">
            <SubjectIcon className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h2 className="truncate text-base font-extrabold tracking-tight">Super_Profesor {theme.emoji}</h2>
              {activeIdOa && (
                <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold backdrop-blur">
                  Resolviendo {activeIdOa}
                </span>
              )}
            </div>
            <p className="truncate text-xs text-white/85">
              {curso} • {asignatura}
            </p>
          </div>
          {activeIdOa && onBackToCatalog && (
            <button
              onClick={onBackToCatalog}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-white/20 px-3 py-1.5 text-xs font-extrabold text-white ring-1 ring-white/40 backdrop-blur transition hover:scale-105 hover:bg-white/30 mr-2"
              aria-label="Volver al Catálogo"
            >
              Volver al Catálogo
            </button>
          )}
          <button
            onClick={() => setLiveOpen(true)}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-white/20 px-3 py-1.5 text-xs font-extrabold text-white ring-1 ring-white/40 backdrop-blur transition hover:scale-105 hover:bg-white/30"
            aria-label="Abrir Modo Audio en Vivo"
          >
            <Radio className="h-3.5 w-3.5" />
            En vivo
          </button>
        </div>

        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-5">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-sm ${
                  m.role === "user"
                    ? `rounded-br-sm bg-gradient-to-br ${theme.gradient} text-white`
                    : `rounded-bl-sm bg-white text-foreground ring-1 ${theme.ring}`
                }`}
              >
                <p className="whitespace-pre-wrap">{m.text}</p>
                {m.role === "professor" && m.audioUrl && (
                  <button
                    onClick={() =>
                      playingId === m.id ? stopAudio() : playAudio(m.id, m.audioUrl!)
                    }
                    className={`mt-2 inline-flex items-center gap-2 rounded-full ${theme.chip} px-3 py-1 text-xs font-semibold transition hover:brightness-95`}
                  >
                    {playingId === m.id ? (
                      <>
                        <Square className="h-3.5 w-3.5" fill="currentColor" />
                        Detener
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5" fill="currentColor" />
                        Escuchar
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className={`rounded-2xl rounded-bl-sm bg-white px-4 py-3 text-sm ${theme.text} shadow-sm ring-1 ${theme.ring}`}>
                Super_Profesor está pensando…
              </div>
            </div>
          )}
        </div>

        <div className={`border-t ${theme.border} bg-white/90 p-3 backdrop-blur`}>
          <div className="flex items-center gap-2">
            <button
              onClick={handleMic}
              aria-label="Hablar"
              className={`grid h-12 w-12 shrink-0 place-items-center rounded-full text-white shadow-md transition ${
                listening
                  ? "animate-pulse bg-red-500"
                  : `bg-gradient-to-br ${theme.gradient} hover:scale-105`
              }`}
            >
              <Mic className="h-5 w-5" />
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder={listening ? "Escuchando..." : `Pregunta de ${theme.label.toLowerCase()}...`}
              className={`h-12 flex-1 rounded-full border-2 ${theme.border} ${theme.softBg} px-5 text-[15px] outline-none transition focus:bg-white focus:ring-2 focus:${theme.ring}`}
            />
            <Button
              onClick={() => handleSend()}
              disabled={sending}
              className={`h-12 w-12 shrink-0 rounded-full bg-gradient-to-br ${theme.gradient} p-0 text-white hover:brightness-110`}
              aria-label="Enviar"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Pizarra */}
      <Whiteboard
        curso={curso}
        asignatura={asignatura}
        studentId={studentId}
        onFeedback={(text, audioUrl) => pushProfessor(text, audioUrl)}
      />

      <LiveAudioModal
        open={liveOpen}
        onClose={() => setLiveOpen(false)}
        curso={curso}
        asignatura={asignatura}
        studentId={studentId}
        activeIdOa={activeIdOa}
      />
    </div>
  );
}
