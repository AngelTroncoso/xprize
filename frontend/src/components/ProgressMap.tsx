import { useEffect, useMemo, useState } from "react";
import {
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

function OACard({ oa, theme }: { oa: OANode; theme: SubjectTheme }) {
  const meta = STATUS_META[oa.status];
  const Icon = meta.icon;
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border-2 ${theme.border} ${meta.tint} p-4 ring-1 ring-white transition hover:-translate-y-0.5 hover:shadow-lg ${theme.glow}`}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${meta.bar}`} aria-hidden />
      <div className="flex items-start justify-between gap-2 pl-2">
        <span
          className={`rounded-lg ${theme.chip} px-2 py-0.5 text-xs font-extrabold tracking-wide`}
        >
          {oa.code}
        </span>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold ${meta.chip}`}
        >
          <Icon className={`h-3 w-3 ${oa.status === "en_progreso" ? "animate-spin" : ""}`} />
          {meta.label}
        </span>
      </div>
      <p className="mt-2 pl-2 text-sm font-semibold leading-snug text-foreground">{oa.title}</p>
      <div className="mt-3 flex flex-wrap gap-1 pl-2">
        {oa.concepts.map((c) => (
          <span
            key={c}
            className={`rounded-full bg-white/90 px-2 py-0.5 text-[11px] font-medium ${theme.text} ring-1 ${theme.ring}`}
          >
            {c}
          </span>
        ))}
      </div>
    </div>
  );
}

function Eje({ name, oas, theme }: { name: string; oas: OANode[]; theme: SubjectTheme }) {
  const dominados = oas.filter((o) => o.status === "dominado").length;
  const pct = oas.length ? Math.round((dominados / oas.length) * 100) : 0;
  return (
    <div className={`rounded-2xl border-2 ${theme.border} bg-white/80 p-4 backdrop-blur`}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h4 className={`text-sm font-extrabold uppercase tracking-wide ${theme.text}`}>{name}</h4>
        <span className="text-xs font-semibold text-foreground/60">
          {dominados}/{oas.length} · {pct}%
        </span>
      </div>
      <div
        className={`mb-3 h-1.5 w-full overflow-hidden rounded-full ${theme.softBg} ring-1 ring-white`}
      >
        <div
          className={`h-full bg-gradient-to-r ${theme.gradient} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {oas.map((oa) => (
          <OACard key={`${name}-${oa.code}`} oa={oa} theme={theme} />
        ))}
      </div>
    </div>
  );
}

interface ProgressMapProps {
  studentId?: string | number;
  curso?: string;
  asignatura?: string;
}

export function ProgressMap({ studentId = 1, curso, asignatura }: ProgressMapProps) {
  const [data, setData] = useState<ProgressTree>(MOCK_PROGRESS);
  const [loading, setLoading] = useState(false);
  const [usingMock, setUsingMock] = useState(true);
  const [openCurso, setOpenCurso] = useState<string | null>(
    curso ?? MOCK_PROGRESS.cursos[0]?.name ?? null,
  );
  const [openAsig, setOpenAsig] = useState<string | null>(null);

  const headerTheme = useMemo(
    () => getSubjectTheme(asignatura ?? ""),
    [asignatura],
  );
  const HeaderIcon = headerTheme.icon;

  const load = async () => {
    setLoading(true);
    try {
      const tree = await getStudentProgress(studentId);
      setData(tree);
      setUsingMock(false);
      setOpenCurso(curso ?? tree.cursos[0]?.name ?? null);
      toast.success("Progreso actualizado desde el backend ✨");
    } catch (err) {
      console.error(err);
      setUsingMock(true);
      setData(MOCK_PROGRESS);
      toast.error("Backend no disponible", { description: BACKEND_HINT });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId]);

  // Sincroniza expansión con el filtro global
  useEffect(() => {
    if (curso) setOpenCurso(curso);
    if (curso && asignatura) setOpenAsig(`${curso}::${asignatura}`);
  }, [curso, asignatura]);

  const { dom, prog, noi, total } = useMemo(() => {
    const allOAs = data.cursos.flatMap((c) =>
      c.asignaturas.flatMap((a) => a.ejes.flatMap((e) => e.oas)),
    );
    return {
      dom: allOAs.filter((o) => o.status === "dominado").length,
      prog: allOAs.filter((o) => o.status === "en_progreso").length,
      noi: allOAs.filter((o) => o.status === "no_iniciado").length,
      total: allOAs.length,
    };
  }, [data]);

  return (
    <div className="space-y-6">
      {usingMock && (
        <div className="rounded-2xl border-2 border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          ⚠️ Mostrando datos de demostración. Levanta el backend FastAPI en{" "}
          <code className="rounded bg-amber-100 px-1">localhost:8000</code> para ver el progreso
          real.
        </div>
      )}

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
                Mapa de Progreso · {headerTheme.label}
              </p>
              <h2 className="truncate text-2xl font-extrabold">¡Hola, {data.student_name}!</h2>
              <p className="text-sm text-white/90">
                Has dominado {dom} de {total} objetivos. ¡Sigue así! 🌟
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Stat n={dom} label="Dominados" tone="emerald" />
            <Stat n={prog} label="En progreso" tone="amber" />
            <Stat n={noi} label="Por iniciar" tone="slate" />
            <Button
              size="icon"
              variant="secondary"
              onClick={load}
              disabled={loading}
              className="rounded-full bg-white/90 text-foreground hover:bg-white"
              aria-label="Refrescar"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
      </div>

      {/* Árbol Curso > Asignatura > Eje > OAs */}
      <div className="space-y-4">
        {data.cursos.map((cursoNode) => {
          const cursoOpen = openCurso === cursoNode.name;
          const cursoMeta = CURSO_META[cursoNode.name] ?? {
            emoji: "🎓",
            gradient: "from-violet-500 to-fuchsia-500",
          };
          const isFilteredCurso = curso === cursoNode.name;
          return (
            <div
              key={cursoNode.name}
              className={`overflow-hidden rounded-3xl border-2 bg-white/60 backdrop-blur transition ${
                isFilteredCurso ? "border-foreground/30 shadow-lg" : "border-white"
              }`}
            >
              <button
                onClick={() => setOpenCurso(cursoOpen ? null : cursoNode.name)}
                className={`flex w-full items-center justify-between gap-3 bg-gradient-to-r ${cursoMeta.gradient} px-5 py-4 text-left text-white`}
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="text-2xl drop-shadow">{cursoMeta.emoji}</span>
                  <span className="truncate text-lg font-extrabold">{cursoNode.name}</span>
                  {isFilteredCurso && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-white/25 px-2 py-0.5 text-[11px] font-bold backdrop-blur">
                      <Sparkles className="h-3 w-3" /> Tu curso
                    </span>
                  )}
                </div>
                <ChevronDown
                  className={`h-5 w-5 shrink-0 transition ${cursoOpen ? "rotate-180" : ""}`}
                />
              </button>

              {cursoOpen && (
                <div className="space-y-3 p-4">
                  {cursoNode.asignaturas.map((asig) => {
                    const asigKey = `${cursoNode.name}::${asig.name}`;
                    const asigOpen = openAsig === asigKey;
                    const asigTheme = getSubjectTheme(asig.name);
                    const AsigIcon = asigTheme.icon;
                    const isFilteredAsig =
                      isFilteredCurso && asignatura === asig.name;
                    return (
                      <div
                        key={asigKey}
                        className={`overflow-hidden rounded-2xl border-2 ${asigTheme.border} ${asigTheme.softBg} ${
                          isFilteredAsig ? `ring-2 ${asigTheme.ring}` : ""
                        }`}
                      >
                        <button
                          onClick={() => setOpenAsig(asigOpen ? null : asigKey)}
                          className={`flex w-full items-center justify-between gap-3 bg-gradient-to-r ${asigTheme.gradient} px-4 py-3 text-left text-white`}
                        >
                          <span className="flex min-w-0 items-center gap-2 truncate text-base font-extrabold">
                            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/20 backdrop-blur">
                              <AsigIcon className="h-4 w-4" />
                            </span>
                            <span className="text-lg">{asigTheme.emoji}</span>
                            <span className="truncate">{asig.name}</span>
                          </span>
                          <ChevronDown
                            className={`h-4 w-4 shrink-0 transition ${
                              asigOpen ? "rotate-180" : ""
                            }`}
                          />
                        </button>
                        {asigOpen && (
                          <div className="space-y-3 p-4">
                            {asig.ejes.map((eje) => (
                              <Eje
                                key={eje.name}
                                name={eje.name}
                                oas={eje.oas}
                                theme={asigTheme}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
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
