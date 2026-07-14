import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { BookOpen, GraduationCap, MessagesSquare, Trophy } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChatView } from "@/components/ChatView";
import { ProgressMap } from "@/components/ProgressMap";
import { CurriculumCatalog } from "@/components/CurriculumCatalog";
import { SubjectBackground } from "@/components/SubjectBackground";
import {
  ASIGNATURAS,
  CURSOS,
  CURSO_META,
  getSubjectTheme,
} from "@/lib/subjectTheme";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Super_Profesor — Aprende jugando" },
      {
        name: "description",
        content:
          "Plataforma educativa interactiva para niños de educación básica en Chile (1° a 8°): chat multimodal, pizarra y mapa curricular MINEDUC.",
      },
      { property: "og:title", content: "Super_Profesor" },
      {
        property: "og:description",
        content: "Chat con voz, pizarra interactiva y seguimiento curricular MINEDUC.",
      },
    ],
  }),
  component: Home,
});

function Home() {
  const [tab, setTab] = useState("chat");
  const [curso, setCurso] = useState("3° Básico");
  const [asignatura, setAsignatura] = useState<string>(ASIGNATURAS[0]);

  const theme = useMemo(() => getSubjectTheme(asignatura), [asignatura]);
  const cursoMeta = CURSO_META[curso];
  const SubjectIcon = theme.icon;

  return (
    <div className={`relative min-h-screen transition-colors duration-500 ${theme.appBg}`}>
      <SubjectBackground theme={theme} />
      {/* Decorativos sutiles */}
      <div
        aria-hidden
        className={`pointer-events-none fixed inset-x-0 top-0 -z-0 h-72 bg-gradient-to-b from-white/40 to-transparent`}
      />

      <header className="relative border-b border-white/60 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <div
              className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br ${theme.gradient} text-white shadow-lg ${theme.glow} transition-all duration-500`}
            >
              <GraduationCap className="h-6 w-6" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-xl font-extrabold tracking-tight text-foreground sm:text-2xl">
                Super<span className={theme.text}>_Profesor</span>
              </h1>
              <p className="flex items-center gap-1.5 text-xs text-foreground/60">
                <SubjectIcon className="h-3.5 w-3.5" />
                {theme.label} • {curso}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Select value={curso} onValueChange={setCurso}>
              <SelectTrigger
                className={`h-10 w-[150px] rounded-full border-2 ${theme.border} bg-white text-sm font-bold ${theme.text}`}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CURSOS.map((c) => (
                  <SelectItem key={c} value={c}>
                    <span className="mr-2">{CURSO_META[c]?.emoji}</span>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={asignatura} onValueChange={setAsignatura}>
              <SelectTrigger
                className={`h-10 w-[220px] rounded-full border-2 ${theme.border} bg-white text-sm font-bold ${theme.text}`}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ASIGNATURAS.map((a) => {
                  const t = getSubjectTheme(a);
                  return (
                    <SelectItem key={a} value={a}>
                      <span className="mr-2">{t.emoji}</span>
                      {a}
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            <div
              className={`shrink-0 rounded-full bg-white px-3 py-1.5 text-xs font-bold ${theme.text} ring-2 ${theme.ring}`}
            >
              👧 Martina
            </div>
          </div>
        </div>

        {/* Banner contextual de asignatura/curso */}
        <div className="mx-auto max-w-7xl px-4 pb-4">
          <div
            className={`flex items-center gap-3 rounded-2xl bg-gradient-to-r ${theme.gradient} px-4 py-2.5 text-white shadow-md ${theme.glow}`}
          >
            <span className="text-xl">{theme.emoji}</span>
            <p className="truncate text-sm font-semibold">
              {theme.label} · {curso}
            </p>
            <span className="ml-auto hidden items-center gap-1 rounded-full bg-white/20 px-2.5 py-1 text-[11px] font-bold backdrop-blur sm:inline-flex">
              <span>{cursoMeta?.emoji}</span> Nivel {curso}
            </span>
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-7xl px-4 py-6">
        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <TabsList className="mx-auto mb-6 grid h-auto w-full max-w-2xl grid-cols-3 rounded-full bg-white/80 p-1.5 shadow-md ring-1 ring-white backdrop-blur">
            <TabsTrigger
              value="chat"
              className="gap-2 rounded-full py-2.5 text-sm font-bold transition data-[state=active]:bg-foreground data-[state=active]:text-background data-[state=active]:shadow-md"
            >
              <MessagesSquare className="h-4 w-4" />
              Clase Interactiva
            </TabsTrigger>
            <TabsTrigger
              value="catalog"
              className="gap-2 rounded-full py-2.5 text-sm font-bold transition data-[state=active]:bg-gradient-to-r data-[state=active]:from-sky-500 data-[state=active]:to-indigo-500 data-[state=active]:text-white data-[state=active]:shadow-md"
            >
              <BookOpen className="h-4 w-4" />
              Catálogo
            </TabsTrigger>
            <TabsTrigger
              value="progress"
              className="gap-2 rounded-full py-2.5 text-sm font-bold transition data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-500 data-[state=active]:to-orange-500 data-[state=active]:text-white data-[state=active]:shadow-md"
            >
              <Trophy className="h-4 w-4" />
              Mi Mapa
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="mt-0">
            <ChatView curso={curso} asignatura={asignatura} studentId="1" />
          </TabsContent>
          <TabsContent value="catalog" className="mt-0">
            <CurriculumCatalog curso={curso} asignatura={asignatura} />
          </TabsContent>
          <TabsContent value="progress" className="mt-0">
            <ProgressMap studentId="1" curso={curso} asignatura={asignatura} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
