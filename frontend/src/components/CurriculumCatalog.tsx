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
import { Textbook } from "@/lib/books";

type UnitWithOAs = CurriculumUnit & { objectives: CurriculumObjective[] };

interface Props {
  curso: string;
  asignatura: string;
  book?: Textbook;
  onSelectOA?: (id: string) => void;
}

export function CurriculumCatalog({ curso, asignatura, book, onSelectOA }: Props) {
  const theme = useMemo(() => getSubjectTheme(asignatura), [asignatura]);
  const Icon = theme.icon;
  const [units, setUnits] = useState<UnitWithOAs[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    // Si tenemos un libro con capítulos, no necesitamos cargar de Supabase
    if (book?.chapters) {
      return;
    }
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
  }, [curso, asignatura, book]);

  // Si tenemos un libro seleccionado con capítulos, renderizar el Índice del Libro
  if (book && book.chapters) {
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
                Índice del Libro {theme.emoji}
              </p>
              <h2 className="truncate text-2xl font-extrabold">
                {book.titulo}
              </h2>
              <p className="text-sm text-white/85">
                Selecciona un capítulo o unidad para comenzar tu clase interactiva.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className={`overflow-hidden rounded-3xl border-2 ${theme.border} bg-white/80 backdrop-blur ${theme.glow} md:col-span-2`}>
            <div className={`flex items-center gap-2 bg-gradient-to-r ${theme.gradient} px-4 py-3 text-white`}>
              <BookOpen className="h-4 w-4" />
              <p className="truncate text-sm font-bold uppercase tracking-wide">
                Contenidos Oficiales MINEDUC
              </p>
            </div>
            <div className="space-y-3 p-4">
              <ul className="space-y-2">
                {book.chapters.map((chapter) => (
                  <li
                    key={chapter.id}
                    onClick={() => onSelectOA && onSelectOA(chapter.title)}
                    className={`rounded-xl border ${theme.border} ${theme.softBg} p-4 cursor-pointer transition-transform hover:-translate-y-1 hover:shadow-md flex items-center justify-between`}
                  >
                    <div className="flex items-center gap-4">
                      <span className={`flex items-center justify-center h-10 w-10 rounded-full ${theme.chip} text-sm font-bold`}>
                        {chapter.id.split('-u')[1]}
                      </span>
                      <p className={`text-base font-bold ${theme.text}`}>{chapter.title}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-foreground/50 font-medium">Pág. {chapter.page_start}</span>
                      <div className={`shrink-0 rounded-full bg-gradient-to-r ${theme.gradient} px-4 py-2 text-xs font-bold text-white shadow-md hover:scale-105 transition-transform cursor-pointer`}>
                        Comenzar Clase
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Si no hay libro seleccionado, pedir al usuario que seleccione uno en la Biblioteca
  return (
    <div className="space-y-6">
      <div
        className={`overflow-hidden rounded-3xl border-2 ${theme.border} bg-gradient-to-r ${theme.gradient} p-5 text-white shadow-lg ${theme.glow}`}
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
              Ve a la pestaña "Biblioteca" y selecciona un texto escolar para ver su índice.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CurriculumCatalog;
