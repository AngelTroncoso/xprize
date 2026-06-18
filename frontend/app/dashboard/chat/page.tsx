"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { fetchApi } from "@/lib/api";
import { COURSES, getSubjectsForCourse } from "@/lib/curriculum";
import {
  Send,
  Loader2,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Volume2,
  StopCircle,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_used?: string;
  oa_metadata?: {
    id_oa?: string;
    descripcion?: string;
    curso?: string;
  };
}

interface ChatSession {
  session_id: string;
  started_at: string;
  first_message: string | null;
  metadata?: {
    curso?: string;
    asignatura?: string;
  };
}

interface ChatResponse {
  session_id: string;
  agent_used: string;
  response_text: string;
  oa_metadata: {
    id_oa?: string;
    descripcion?: string;
    curso?: string;
    conceptos_clave?: string[];
  };
}

export default function ChatPageContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [curso, setCurso] = useState("");
  const [asignatura, setAsignatura] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionsOpen, setSessionsOpen] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [studentId, setStudentId] = useState<string | null>(null);
  const [audioPlaying, setAudioPlaying] = useState<string | null>(null);
  const [autoPlayAudio, setAutoPlayAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load auto-play preference from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("sp_auto_play_audio");
    if (stored === "true") {
      setAutoPlayAudio(true);
    }
  }, []);

  // Get student ID on mount
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) setStudentId(user.id);
    });
  }, []);

  // Load sessions when studentId is ready
  useEffect(() => {
    if (!studentId) return;
    fetchSessions();
  }, [studentId]);

  const fetchSessions = async () => {
    if (!studentId) return;
    try {
      const data = await fetchApi<ChatSession[]>(
        `/api/chat/sessions/${studentId}`
      );
      setSessions(data.slice(0, 3));
    } catch {
      // Silently fail
    }
  };

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Play TTS audio
  const playAudio = useCallback(async (text: string, messageId: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setAudioPlaying(messageId);

    try {
      const res = await fetch(`${API_BASE}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          session_id: currentSessionId ?? "new",
        }),
      });

      if (!res.ok) throw new Error("Error al generar audio");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        setAudioPlaying(null);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };

      audio.onerror = () => {
        setAudioPlaying(null);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };

      await audio.play();
    } catch {
      setAudioPlaying(null);
    }
  }, [currentSessionId]);

  // Stop audio
  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setAudioPlaying(null);
  }, []);

  // Auto-play when a new assistant message arrives
  useEffect(() => {
    if (autoPlayAudio && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.role === "assistant" && audioPlaying === null) {
        playAudio(last.content, last.id);
      }
    }
  }, [messages, autoPlayAudio, audioPlaying, playAudio]);

  const sendMessage = async () => {
    if (!input.trim() || !curso || !asignatura || !studentId) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const body: Record<string, unknown> = {
        student_id: studentId,
        message: userMessage.content,
        curso,
        asignatura,
      };
      if (currentSessionId) {
        body.session_id = currentSessionId;
      }

      const data = await fetchApi<ChatResponse>("/api/chat", {
        method: "POST",
        body: JSON.stringify(body),
      });

      setCurrentSessionId(data.session_id);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response_text,
        agent_used: data.agent_used,
        oa_metadata: data.oa_metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (!currentSessionId) {
        fetchSessions();
      }
    } catch (err) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content:
          err instanceof Error
            ? `Error: ${err.message}`
            : "Error al conectar con el servidor",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const loadSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setMessages([]);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      {/* Sessions sidebar */}
      <AnimatePresence>
        {sessionsOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="glass-panel rounded-2xl overflow-hidden flex-shrink-0"
          >
            <div className="p-4 border-b border-white/5">
              <h3 className="text-sm font-semibold text-gray-300">
                Sesiones Recientes
              </h3>
            </div>
            <div className="p-2 space-y-1 overflow-y-auto max-h-[calc(100vh-12rem)]">
              {sessions.length === 0 && (
                <p className="text-xs text-gray-500 px-2 py-4 text-center">
                  No hay sesiones anteriores
                </p>
              )}
              {sessions.map((s) => (
                <button
                  key={s.session_id}
                  onClick={() => loadSession(s.session_id)}
                  className={`w-full text-left p-3 rounded-xl text-sm transition-all ${
                    currentSessionId === s.session_id
                      ? "bg-indigo-500/10 border border-indigo-500/20"
                      : "hover:bg-white/5"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <MessageSquare className="w-4 h-4 mt-0.5 text-gray-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-gray-300 truncate text-xs leading-relaxed">
                        {s.first_message ?? "Sesión vacía"}
                      </p>
                      <p className="text-gray-600 text-[10px] mt-1">
                        {new Date(s.started_at).toLocaleDateString("es-CL", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Toggle sessions button */}
      <button
        onClick={() => setSessionsOpen(!sessionsOpen)}
        className="self-center p-2 rounded-xl glass-panel hover:border-indigo-500/50 transition-all flex-shrink-0"
        title={sessionsOpen ? "Ocultar historial" : "Mostrar historial"}
      >
        {sessionsOpen ? (
          <ChevronLeft className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col glass-panel rounded-2xl overflow-hidden">
        {/* Header with course/subject selectors + auto-play toggle */}
        <div className="p-4 border-b border-white/5 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 font-medium">Curso:</label>
            <select
              value={curso}
              onChange={(e) => {
                setCurso(e.target.value);
                setAsignatura("");
              }}
              className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-indigo-500/50"
            >
              <option value="" className="bg-[#020208]">
                Seleccionar
              </option>
              {COURSES.map((c) => (
                <option key={c} value={c} className="bg-[#020208]">
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 font-medium">
              Asignatura:
            </label>
            <select
              value={asignatura}
              onChange={(e) => setAsignatura(e.target.value)}
              disabled={!curso}
              className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-indigo-500/50 disabled:opacity-40"
            >
              <option value="" className="bg-[#020208]">
                Seleccionar
              </option>
              {curso &&
                getSubjectsForCourse(curso).map((s) => (
                  <option key={s} value={s} className="bg-[#020208]">
                    {s}
                  </option>
                ))}
            </select>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <label className="text-[10px] text-gray-500 cursor-pointer select-none flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={autoPlayAudio}
                onChange={(e) => {
                  const v = e.target.checked;
                  setAutoPlayAudio(v);
                  localStorage.setItem("sp_auto_play_audio", v.toString());
                }}
                className="w-3 h-3 rounded border-white/10 bg-white/5 accent-indigo-500"
              />
              Audio auto
            </label>
            {audioPlaying && (
              <button
                onClick={stopAudio}
                className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"
              >
                <StopCircle className="w-3 h-3" />
                Detener
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-3xl mb-4">
                💬
              </div>
              <h2 className="text-lg font-semibold mb-2">
                Consulta a tu Tutor IA
              </h2>
              <p className="text-gray-400 text-sm max-w-md">
                Selecciona un curso y asignatura, luego escribe tu duda o
                pregunta. El Agente Pedagógico te guiará paso a paso.
              </p>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                    msg.role === "user"
                      ? "bg-gradient-accent text-white rounded-br-sm"
                      : "glass-panel rounded-bl-sm"
                  }`}
                >
                  {/* OA Badge */}
                  {msg.role === "assistant" && msg.oa_metadata?.id_oa && (
                    <div className="flex items-center gap-1.5 mb-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-medium text-cyan-400">
                        {msg.oa_metadata.id_oa}
                      </span>
                      {msg.oa_metadata.descripcion && (
                        <span className="text-[10px] text-gray-500 truncate max-w-[120px]">
                          {msg.oa_metadata.descripcion}
                        </span>
                      )}
                      {msg.oa_metadata.curso && (
                        <span className="text-[10px] text-gray-500">
                          · {msg.oa_metadata.curso}
                        </span>
                      )}
                    </div>
                  )}

                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </p>

                  {/* Agent tag + Audio button */}
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
                    <div className="flex items-center gap-2">
                      {msg.role === "assistant" && msg.agent_used && (
                        <p className="text-[10px] text-gray-500">
                          {msg.agent_used}
                        </p>
                      )}
                    </div>
                    {/* TTS Audio button on assistant messages */}
                    {msg.role === "assistant" && (
                      <button
                        onClick={() => {
                          if (audioPlaying === msg.id) {
                            stopAudio();
                          } else {
                            playAudio(msg.content, msg.id);
                          }
                        }}
                        className={`p-1.5 rounded-lg transition-all ${
                          audioPlaying === msg.id
                            ? "bg-indigo-500/20 text-indigo-400 animate-pulse"
                            : "text-gray-500 hover:text-indigo-400 hover:bg-white/5"
                        }`}
                        title={
                          audioPlaying === msg.id
                            ? "Reproduciendo..."
                            : "Escuchar respuesta"
                        }
                      >
                        {audioPlaying === msg.id ? (
                          <StopCircle className="w-4 h-4" />
                        ) : (
                          <Volume2 className="w-4 h-4" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="glass-panel rounded-2xl rounded-bl-sm px-5 py-4">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  !curso || !asignatura
                    ? "Selecciona curso y asignatura arriba..."
                    : "Escribe tu mensaje... (Enter para enviar)"
                }
                rows={2}
                disabled={!curso || !asignatura || loading}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all resize-none disabled:opacity-40"
                style={{ minHeight: 48 }}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!input.trim() || !curso || !asignatura || loading}
              className="p-3 rounded-xl bg-gradient-accent text-white hover:opacity-95 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-[10px] text-gray-600 mt-2 text-center">
            Las respuestas son generadas por IA y pueden contener errores.
            Siempre verifica con tu profesor.
          </p>
        </div>
      </div>
    </div>
  );
}