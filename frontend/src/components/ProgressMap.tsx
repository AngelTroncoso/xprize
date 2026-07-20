import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  Circle,
  Loader2,
  RefreshCw,
  Sparkles,
  Trophy,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { MOCK_PROGRESS } from "@/lib/curriculumData";
import {
  BACKEND_HINT,
  getStudentProgress,
  type OANode,
  type OAStatus,
  type ProgressTree,
} from "@/lib/apiService";
import { CURSO_META, getSubjectTheme, type SubjectTheme } from "@/lib/subjectTheme";
import { Textbook, Chapter } from "@/lib/books";

const STATUS_META: Record<
  OAStatus,
  { label: string; chip: string; icon: typeof CheckCircle2; tint: string; bar: string }
> = {
  dominado: {
    label: "Dominado",
    chip: "bg-emerald-500 text-white",
    icon: CheckCircle2,
    tint: "bg-emerald-50/80",
    bar: "bg-emerald-500",
  },
  en_progreso: {
    label: "En Progreso",
    chip: "bg-amber-500 text-white",
    icon: Loader2,
    tint: "bg-amber-50/80",
    bar: "bg-amber-500",
  },
  no_iniciado: {
    label: "Por Iniciar",
    chip: "bg-slate-400 text-white",
    icon: Circle,
    tint: "bg-white",
    bar: "bg-slate-300",
  },
};

function ChapterCard({ chapter, status, theme }: { chapter: Chapter; status: OAStatus; theme: SubjectTheme }) {
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border-2 ${theme.border} ${meta.tint} p-4 ring-1 ring-white transition hover:-translate-y-0.5 hover:shadow-lg ${theme.glow}`}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${meta.bar}`} aria-hidden />
      <div className="flex items-start justify-between gap-2 pl-2">
        <span
          className={`rounded-lg ${theme.chip} px-2 py-0.5 text-xs font-extrabold tracking-wide uppercase`}
        >
          {chapter.id.split('-').pop()}
        </span>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold ${meta.chip}`}
        >
          <Icon className={`h-3 w-3 ${status === "en_progreso" ? "animate-spin" : ""}`} />
          {meta.label}
        </span>
      </div>
      <p className="mt-2 pl-2 text-sm font-semibold leading-snug text-foreground">{chapter.title}</p>
      <div className="mt-3 flex flex-wrap gap-1 pl-2">
        <span className={`rounded-full bg-white/90 px-2 py-0.5 text-[11px] font-medium ${theme.text} ring-1 ${theme.ring}`}>
          Pág. {chapter.page_start}
        </span>
      </div>
    </div>
  );
}

interface ProgressMapProps {
  studentId?: string | number;
  curso?: string;
  asignatura?: string;
  book?: Textbook;
}

export function ProgressMap({ studentId = "00000000-0000-0000-0000-000000000001", curso, asignatura, book }: ProgressMapProps) {
  const headerTheme = useMemo(
    () => getSubjectTheme(book?.asignatura ?? asignatura ?? ""),
    [asignatura, book],
  );
  const HeaderIcon = headerTheme.icon;

  // Si no hay libro seleccionado, pedir al usuario que seleccione uno en la Biblioteca
  if (!book || !book.chapters) {
    return (
      <div className="space-y-6">
        <div
          className={`overflow-hidden rounded-3xl border-2 ${headerTheme.border} bg-gradient-to-r ${headerTheme.gradient} p-5 text-white shadow-lg ${headerTheme.glow}`}
        >
          <div className="flex items-center gap-4">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/20 backdrop-blur">
              <BookOpen className="h-7 w-7" />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="truncate text-2xl font-extrabold">
                Por favor selecciona un Libro
              </h2>
              <p className="text-sm text-white/85">
                Ve a la pestaña "Biblioteca" y selecciona un texto escolar para ver tu progreso.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Si hay un libro, mostramos el progreso del libro
  // Mapeamos capítulos a un estado ficticio para la demostración
  const chapterProgress = book.chapters.map((ch, idx) => ({
    ...ch,
    status: (idx === 0 ? "dominado" : idx === 1 ? "en_progreso" : "no_iniciado") as OAStatus,
  }));

  const dom = chapterProgress.filter(c => c.status === "dominado").length;
  const prog = chapterProgress.filter(c => c.status === "en_progreso").length;
  const noi = chapterProgress.filter(c => c.status === "no_iniciado").length;
  const total = chapterProgress.length;
  const pct = Math.round((dom / total) * 100);

  return (
    <div className="space-y-6">
      {/* Header gamificado tematizado por asignatura */}
      <div
        className={`overflow-hidden rounded-3xl border-2 ${headerTheme.border} bg-gradient-to-r ${headerTheme.gradient} ${headerTheme.gradientVia ?? ""} p-6 text-white shadow-lg ${headerTheme.glow}`}
      >
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 sm:flex sm:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-white/20 text-white shadow-md backdrop-blur">
              <HeaderIcon className="h-8 w-8" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase tracking-wider text-white/80">
                Mi Progreso · {book.titulo}
              </p>
              <h2 className="truncate text-2xl font-extrabold">¡Hola, Martina!</h2>
              <p className="text-sm text-white/90">
                Has completado {dom} de {total} módulos. ¡Sigue así! 🌟
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Stat n={dom} label="Completados" tone="emerald" />
            <Stat n={prog} label="En progreso" tone="amber" />
            <Stat n={noi} label="Por iniciar" tone="slate" />
          </div>
        </div>
      </div>

      <div className={`rounded-2xl border-2 ${headerTheme.border} bg-white/80 p-4 backdrop-blur shadow-sm`}>
        <div className="mb-3 flex items-center justify-between gap-2">
          <h4 className={`text-sm font-extrabold uppercase tracking-wide ${headerTheme.text}`}>Módulos del Libro</h4>
          <span className="text-xs font-semibold text-foreground/60">
            {dom}/{total} · {pct}%
          </span>
        </div>
        <div
          className={`mb-5 h-1.5 w-full overflow-hidden rounded-full ${headerTheme.softBg} ring-1 ring-white`}
        >
          <div
            className={`h-full bg-gradient-to-r ${headerTheme.gradient} transition-all`}
            style={{ width: `${pct}%` }}
          />
        </div>
        
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {chapterProgress.map((chapter) => (
            <ChapterCard key={chapter.id} chapter={chapter} status={chapter.status} theme={headerTheme} />
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({
  n,
  label,
  tone,
}: {
  n: number;
  label: string;
  tone: "emerald" | "amber" | "slate";
}) {
  const tones = {
    emerald: "bg-emerald-500 text-white",
    amber: "bg-amber-500 text-white",
    slate: "bg-slate-400 text-white",
  } as const;
  return (
    <div className="rounded-2xl bg-white/90 px-3 py-2 text-center shadow-sm ring-1 ring-white">
      <div
        className={`mx-auto mb-1 grid h-8 w-8 place-items-center rounded-full text-sm font-extrabold ${tones[tone]}`}
      >
        {n}
      </div>
      <p className="text-[10px] font-bold uppercase tracking-wide text-foreground/60">{label}</p>
    </div>
  );
}

export default ProgressMap;
