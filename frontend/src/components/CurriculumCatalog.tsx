import { useEffect, useMemo, useState } from "react";
import { BookOpen, Loader2, RefreshCw, ServerCrash } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  fetchCurriculumCatalog,
  type CurriculumObjective,
  type CurriculumUnit,
} from "@/integrations/supabase/external-client";
import { getSubjectTheme } from "@/lib/subjectTheme";

type UnitWithOAs = CurriculumUnit & { objectives: CurriculumObjective[] };

interface Props {
  curso: string;
  asignatura: string;
  onSelectOA?: (id: string) => void;
}

export function CurriculumCatalog({ curso, asignatura, onSelectOA }: Props) {
  const theme = useMemo(() => getSubjectTheme(asignatura), [asignatura]);
  const Icon = theme.icon;
  const [units, setUnits] = useState<UnitWithOAs[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCurriculumCatalog({ curso, asignatura });
      setUnits(data as UnitWithOAs[]);
      if (data.length === 0) {
        toast.message("Sin unidades para este filtro", {
          description: `No hay unidades publicadas para ${asignatura} · ${curso}.`,
        });
      }
    } catch (err: any) {
      console.error(err);
      const msg = err?.message ?? "Error desconocido";
      setError(msg);
      toast.error("No se pudo cargar el currículum", { description: msg });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curso, asignatura]);

  return (
    <div className="space-y-6">
      <div
        className={`overflow-hidden rounded-3xl border-2 ${theme.border} bg-gradient-to-r ${theme.gradient} p-5 text-white shadow-lg ${theme.glow}`}
      >
        <div className="flex items-center gap-4">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/20 backdrop-blur">
            <Icon className="h-7 w-7" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold uppercase tracking-wider text-white/80">
              Catálogo curricular {theme.emoji}
            </p>
            <h2 className="truncate text-2xl font-extrabold">
              {theme.label} · {curso}
            </h2>
            <p className="text-sm text-white/85">
              Haz click en un Objetivo de Aprendizaje (OA) para iniciar tu clase interactiva.
            </p>
          </div>
          <Button
            size="icon"
            variant="secondary"
            onClick={load}
            disabled={loading}
            aria-label="Refrescar"
            className="rounded-full bg-white/90 text-foreground hover:bg-white"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-2xl border-2 border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <ServerCrash className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-bold">No pudimos leer Supabase.</p>
            <p className="text-red-700/90">{error}</p>
            <p className="mt-1 text-xs text-red-700/80">
              Verifica que existan las tablas <code>curriculum_units</code> y{" "}
              <code>curriculum_objectives</code> con políticas RLS de lectura.
            </p>
          </div>
        </div>
      )}

      {loading && units.length === 0 && (
        <div className="flex items-center justify-center gap-2 rounded-2xl bg-white/70 py-10 text-foreground/60">
          <Loader2 className="h-5 w-5 animate-spin" />
          Cargando currículum…
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {units.map((u) => (
          <div
            key={String(u.id)}
            className={`overflow-hidden rounded-3xl border-2 ${theme.border} bg-white/80 backdrop-blur ${theme.glow}`}
          >
            <div
              className={`flex items-center gap-2 bg-gradient-to-r ${theme.gradient} px-4 py-3 text-white`}
            >
              <BookOpen className="h-4 w-4" />
              <p className="truncate text-sm font-bold uppercase tracking-wide">
                {u.eje}
              </p>
            </div>
            <div className="space-y-3 p-4">
              <h3 className="text-base font-extrabold text-foreground">{u.nombre}</h3>
              <ul className="space-y-2">
                {u.objectives.map((oa) => (
                  <li
                    key={String(oa.id)}
                    onClick={() => onSelectOA && onSelectOA(oa.code)}
                    className={`rounded-xl border ${theme.border} ${theme.softBg} p-3 cursor-pointer transition-transform hover:-translate-y-1 hover:shadow-md`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-md ${theme.chip} px-2 py-0.5 text-[11px] font-extrabold`}
                        >
                          {oa.code}
                        </span>
                        <p className={`text-sm font-semibold ${theme.text}`}>{oa.title}</p>
                      </div>
                      <div className={`shrink-0 rounded-full bg-gradient-to-r ${theme.gradient} px-2 py-1 text-[10px] font-bold text-white shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:opacity-100`}>
                        Comenzar Clase
                      </div>
                    </div>
                    {oa.concepts && oa.concepts.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {oa.concepts.map((c) => (
                          <span
                            key={c}
                            className={`rounded-full bg-white/90 px-2 py-0.5 text-[11px] font-medium ${theme.text} ring-1 ${theme.ring}`}
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
                {u.objectives.length === 0 && (
                  <li className="text-xs text-foreground/50">Sin OAs registrados.</li>
                )}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CurriculumCatalog;
