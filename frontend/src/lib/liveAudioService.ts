// Servicio cliente para el "Modo Audio en Tiempo Real" (estilo Gemini Live).
// Conecta vía WebSocket al pipeline de baja latencia del backend FastAPI
// (ws://localhost:8000/api/live), enviando chunks binarios del micrófono
// y reproduciendo en streaming los chunks de audio de respuesta.

export type LiveStatus = "idle" | "listening" | "thinking" | "speaking" | "error";

export interface LiveTurnContext {
  student_id: string;
  curso: string;
  asignatura: string;
  active_id_oa?: string | null;
}

export interface LiveAudioCallbacks {
  onStatus?: (s: LiveStatus) => void;
  onLevel?: (rms: number) => void; // 0..1 — útil para animar ondas
  onTranscript?: (text: string) => void;
  onResponse?: (text: string) => void;
  onError?: (err: Error) => void;
}

// URL del WebSocket del pipeline live. Override con VITE_LIVE_WS_URL si aplica.
const LIVE_WS_URL =
  (import.meta as any).env?.VITE_LIVE_WS_URL ??
  "ws://localhost:8000/api/live";

export class LiveAudioSession {
  private ws?: WebSocket;
  private wsReady = false;

  // Captura de micrófono
  private micStream?: MediaStream;
  private micCtx?: AudioContext;
  private micSource?: MediaStreamAudioSourceNode;
  private micAnalyser?: AnalyserNode;
  private recorder?: MediaRecorder;
  private rafMic?: number;
  private mime = "audio/webm;codecs=opus";

  // Reproducción del profesor
  private playCtx?: AudioContext;
  private playAnalyser?: AnalyserNode;
  private playGain?: GainNode;
  private playCursor = 0; // timestamp del próximo chunk programado
  private playingSources: AudioBufferSourceNode[] = [];
  private rafPlay?: number;
  private speakingActive = false;

  status: LiveStatus = "idle";

  constructor(
    private context: LiveTurnContext,
    private cb: LiveAudioCallbacks = {},
  ) {
    void this.connect();
  }

  private setStatus(s: LiveStatus) {
    this.status = s;
    this.cb.onStatus?.(s);
  }

  // -------------------- WebSocket --------------------

  private async connect() {
    try {
      const ws = new WebSocket(LIVE_WS_URL);
      ws.binaryType = "arraybuffer";
      this.ws = ws;

      ws.onopen = () => {
        this.wsReady = true;
        // Mensaje de inicialización que espera el backend
        this.sendJson({
          type: "init",
          curso: this.context.curso,
          asignatura: this.context.asignatura,
          id_oa: this.context.active_id_oa ?? null,
          student_id: this.context.student_id,
        });
      };

      ws.onmessage = (ev) => {
        if (typeof ev.data === "string") {
          this.handleJson(ev.data);
        } else if (ev.data instanceof ArrayBuffer) {
          void this.handleAudioChunk(ev.data);
        } else if (ev.data instanceof Blob) {
          ev.data.arrayBuffer().then((buf) => this.handleAudioChunk(buf));
        }
      };

      ws.onerror = () => {
        this.setStatus("error");
        this.cb.onError?.(new Error("Error de conexión con el pipeline live"));
      };

      ws.onclose = () => {
        this.wsReady = false;
      };
    } catch (err) {
      this.setStatus("error");
      this.cb.onError?.(err as Error);
    }
  }

  private sendJson(obj: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }

  private sendBinary(buf: ArrayBuffer | Blob) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(buf as any);
    }
  }

  private handleJson(raw: string) {
    let msg: any;
    try {
      msg = JSON.parse(raw);
    } catch {
      return;
    }
    switch (msg.type) {
      case "transcript":
        if (msg.text) this.cb.onTranscript?.(msg.text);
        break;
      case "response_text":
      case "response":
        if (msg.text) this.cb.onResponse?.(msg.text);
        if (!this.speakingActive) this.setStatus("thinking");
        break;
      case "audio_start":
        this.beginSpeaking();
        break;
      case "audio_end":
      case "turn_end":
        this.endSpeakingSoon();
        break;
      case "error":
        this.setStatus("error");
        this.cb.onError?.(new Error(msg.message ?? "Error del servidor"));
        break;
      default:
        break;
    }
  }

  // -------------------- Micrófono --------------------

  async startListening() {
    // Interrumpir cualquier reproducción del profesor (efecto Gemini Live)
    this.stopSpeaking(true);

    try {
      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
          sampleRate: 16000,
        },
      });
    } catch (err) {
      this.setStatus("error");
      this.cb.onError?.(err as Error);
      return;
    }

    this.micCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    this.micSource = this.micCtx.createMediaStreamSource(this.micStream);
    this.micAnalyser = this.micCtx.createAnalyser();
    this.micAnalyser.fftSize = 512;
    this.micSource.connect(this.micAnalyser);
    this.tickMicLevel();

    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4",
    ];
    this.mime =
      candidates.find(
        (m) =>
          typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(m),
      ) ?? "audio/webm";

    // Aviso de inicio de turno (algunos pipelines lo aprovechan para VAD)
    this.sendJson({ type: "start", mime: this.mime });

    this.recorder = new MediaRecorder(this.micStream, { mimeType: this.mime });
    this.recorder.ondataavailable = async (e) => {
      if (e.data && e.data.size > 0) {
        const buf = await e.data.arrayBuffer();
        this.sendBinary(buf);
      }
    };
    this.recorder.onstop = () => {
      this.sendJson({ type: "stop" });
    };
    this.recorder.start(250); // chunks de 250ms en streaming continuo
    this.setStatus("listening");
  }

  async stopListening() {
    if (this.recorder && this.recorder.state !== "inactive") {
      try {
        this.recorder.stop();
      } catch {
        /* noop */
      }
    }
    this.recorder = undefined;
    this.micStream?.getTracks().forEach((t) => t.stop());
    this.micStream = undefined;
    if (this.rafMic) cancelAnimationFrame(this.rafMic);
    this.rafMic = undefined;
    if (this.status === "listening") this.setStatus("thinking");
  }

  /** Interrumpe la reproducción del profesor. Si `notify`, manda señal al backend. */
  stopSpeaking(notify = false) {
    for (const src of this.playingSources) {
      try {
        src.stop();
      } catch {
        /* noop */
      }
    }
    this.playingSources = [];
    this.playCursor = 0;
    this.speakingActive = false;
    if (this.rafPlay) cancelAnimationFrame(this.rafPlay);
    this.rafPlay = undefined;
    if (notify) {
      // Limpia el buffer del lado servidor para no recibir más audio en cola
      this.sendJson({ type: "interrupt" });
    }
    if (this.status === "speaking") this.setStatus("idle");
  }

  async close() {
    await this.stopListening();
    this.stopSpeaking(false);
    try {
      this.ws?.close();
    } catch {
      /* noop */
    }
    this.ws = undefined;
    this.wsReady = false;
    if (this.micCtx && this.micCtx.state !== "closed") await this.micCtx.close();
    if (this.playCtx && this.playCtx.state !== "closed") await this.playCtx.close();
    this.micCtx = undefined;
    this.playCtx = undefined;
    this.setStatus("idle");
  }

  updateContext(ctx: Partial<LiveTurnContext>) {
    const prev = this.context;
    this.context = { ...prev, ...ctx };
    // Si cambia el contexto pedagógico, reenvía init para refrescar el OA
    if (
      this.wsReady &&
      (prev.curso !== this.context.curso ||
        prev.asignatura !== this.context.asignatura ||
        prev.active_id_oa !== this.context.active_id_oa)
    ) {
      this.sendJson({
        type: "init",
        curso: this.context.curso,
        asignatura: this.context.asignatura,
        id_oa: this.context.active_id_oa ?? null,
        student_id: this.context.student_id,
      });
    }
  }

  // -------------------- Niveles / animaciones --------------------

  private tickMicLevel = () => {
    if (!this.micAnalyser) return;
    const buf = new Uint8Array(this.micAnalyser.fftSize);
    const loop = () => {
      if (!this.micAnalyser) return;
      this.micAnalyser.getByteTimeDomainData(buf);
      let sum = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / buf.length);
      this.cb.onLevel?.(Math.min(1, rms * 2.5));
      this.rafMic = requestAnimationFrame(loop);
    };
    loop();
  };

  private tickPlayLevel = () => {
    if (!this.playAnalyser) return;
    const buf = new Uint8Array(this.playAnalyser.fftSize);
    const loop = () => {
      if (!this.playAnalyser || !this.speakingActive) return;
      this.playAnalyser.getByteTimeDomainData(buf);
      let sum = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / buf.length);
      this.cb.onLevel?.(Math.min(1, rms * 2.5));
      this.rafPlay = requestAnimationFrame(loop);
    };
    loop();
  };

  // -------------------- Reproducción streaming --------------------

  private ensurePlayCtx() {
    if (!this.playCtx) {
      this.playCtx = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      this.playAnalyser = this.playCtx.createAnalyser();
      this.playAnalyser.fftSize = 512;
      this.playGain = this.playCtx.createGain();
      this.playGain.connect(this.playAnalyser);
      this.playAnalyser.connect(this.playCtx.destination);
    }
    return this.playCtx;
  }

  private beginSpeaking() {
    this.ensurePlayCtx();
    this.speakingActive = true;
    this.playCursor = 0;
    this.setStatus("speaking");
    this.tickPlayLevel();
  }

  private endSpeakingSoon() {
    // Espera a que se vacíe la cola programada antes de pasar a idle
    const ctx = this.playCtx;
    if (!ctx) {
      this.speakingActive = false;
      this.setStatus("idle");
      return;
    }
    const remaining = Math.max(0, this.playCursor - ctx.currentTime);
    window.setTimeout(
      () => {
        if (this.status === "speaking") {
          this.speakingActive = false;
          this.setStatus("idle");
          this.cb.onLevel?.(0);
        }
      },
      Math.ceil(remaining * 1000) + 50,
    );
  }

  private async handleAudioChunk(buf: ArrayBuffer) {
    if (!buf.byteLength) return;
    const ctx = this.ensurePlayCtx();
    if (!this.speakingActive) this.beginSpeaking();

    let audioBuffer: AudioBuffer;
    try {
      // decodeAudioData consume el buffer; clonamos para mantenerlo válido
      audioBuffer = await ctx.decodeAudioData(buf.slice(0));
    } catch (err) {
      // Si el backend manda PCM crudo en vez de un contenedor, ignoramos
      // silenciosamente este chunk (el pipeline define el formato).
      console.warn("[live] no se pudo decodificar chunk de audio", err);
      return;
    }

    const src = ctx.createBufferSource();
    src.buffer = audioBuffer;
    src.connect(this.playGain!);

    const now = ctx.currentTime;
    const startAt = Math.max(now, this.playCursor);
    src.start(startAt);
    this.playCursor = startAt + audioBuffer.duration;

    this.playingSources.push(src);
    src.onended = () => {
      this.playingSources = this.playingSources.filter((s) => s !== src);
    };
  }
}
