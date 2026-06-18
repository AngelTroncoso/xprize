"use client";

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
} from "recharts";
import { createClient } from "@/lib/supabase/client";
import { fetchApi } from "@/lib/api";
import {
  BookOpen,
  Flame,
  TrendingUp,
  Award,
  ArrowRight,
  Loader2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

/* ---------- Types ---------- */

interface OAItem {
  id_oa: string;
  descripcion: string;
  conceptos_clave: string[];
  nivel_logro: "mastered" | "partial" | "in_progress" | "not_started";
  mastery_level: "mastered" | "partial" | "in_progress" | "not_started";
  last_evaluation_date: string | null;
  evaluation_count: number;
}

interface EjeItem {
  eje_tematico: string;
  oas: OAItem[];
}

interface AsignaturaItem {
  asignatura: string;
  ejes: EjeItem[];
}

interface CursoNode {
  curso: string;
  asignaturas: AsignaturaItem[];
}

interface ProgressData {
  student_id: string;
  curriculum_tree: CursoNode[];
  summary: {
    total_oas: number;
    mastered: number;
    partial: number;
    in_progress: number;
    not_started: number;
    overall_mastery_percentage: number;
  };
  data_source: string;
}

/* ---------- Helpers ---------- */

const LEVEL_LABEL: Record<string, string> = {
  mastered: "Dominado",
  partial: "Parcial",
  in_progress: "En progreso",
  not_started: "No iniciado",
};

const LEVEL_COLOR: Record<string, string> = {
  mastered: "#22c55e",
  partial: "#f59e0b",
  in_progress: "#3b82f6",
  not_started: "#6b7280",
};

const LEVEL_EMOJI: Record<string, string> = {
  mastered: "🟢",
  partial: "🟡",
  in_progress: "🟡",
  not_started: "🔴",
};

function masteryToScore(level: string): number {
  switch (level) {
    case "mastered":
      return 4;
    case "partial":
      return 3;
    case "in_progress":
      return 2;
    default:
      return 1;
  }
}

function computeStreak(oas: OAItem[]): number {
  const dates = oas
    .map((o) => o.last_evaluation_date)
    .filter(Boolean) as string[];
  if (dates.length === 0) return 0;

  const sorted = dates.map((d) => new Date(d).toISOString().split("T")[0]).sort();
  const unique = Array.from(new Set(sorted)).reverse();

  let streak = 1;
  const today = new Date().toISOString().split("T")[0];
  // Start counting from today or the most recent date
  let checkDate = new Date(unique[0]);

  for (let i = 0; i < unique.length; i++) {
    const expected = new Date(checkDate);
    expected.setDate(expected.getDate() - i);
    const expectedStr = expected.toISOString().split("T")[0];
    if (unique[i] === expectedStr) {
      streak = i + 1;
    } else {
      break;
    }
  }

  return streak;
}

function computeAvgScore(oas: OAItem[]): number {
  const scores = oas.map((o) => masteryToScore(o.nivel_logro));
  if (scores.length === 0) return 0;
  return Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;
}

/* ---------- Component ---------- */

export default function ProgresoPage() {
  const [data, setData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [studentId, setStudentId] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) setStudentId(user.id);
    });
  }, []);

  useEffect(() => {
    if (!studentId) return;
    setLoading(true);
    fetchApi<ProgressData>(`/api/students/${studentId}/progress`)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Error al cargar datos");
        setLoading(false);
      });
  }, [studentId]);

  // Flatten all OAs + compute aggregates
  const { allOas, streak, avgScore, ejeData, timeData, worstOA } = useMemo(() => {
    if (!data) {
      return {
        allOas: [] as OAItem[],
        streak: 0,
        avgScore: 0,
        ejeData: [] as { name: string; Dominado: number; Parcial: number; "En progreso": number; "No iniciado": number; pct: number }[],
        timeData: [] as { date: string; score: number }[],
        worstOA: null as OAItem | null,
      };
    }

    const allOas: OAItem[] = [];
    const ejeMap: Record<string, OAItem[]> = {};

    for (const curso of data.curriculum_tree) {
      for (const asignatura of curso.asignaturas) {
        for (const eje of asignatura.ejes) {
          if (!ejeMap[eje.eje_tematico]) ejeMap[eje.eje_tematico] = [];
          ejeMap[eje.eje_tematico].push(...eje.oas);
          allOas.push(...eje.oas);
        }
      }
    }

    // By eje temático
    const ejeData = Object.entries(ejeMap).map(([name, oas]) => {
      const total = oas.length;
      const mastered = oas.filter((o) => o.nivel_logro === "mastered").length;
      const partial = oas.filter((o) => o.nivel_logro === "partial").length;
      const inProgress = oas.filter((o) => o.nivel_logro === "in_progress").length;
      const notStarted = oas.filter((o) => o.nivel_logro === "not_started").length;
      const pct = total ? Math.round((mastered / total) * 100) : 0;
      return { name, Dominado: mastered, Parcial: partial, "En progreso": inProgress, "No iniciado": notStarted, pct };
    });

    // Streak
    const streak = computeStreak(allOas);

    // Avg score
    const avgScore = computeAvgScore(allOas);

    // Time series — simulate from evaluation_history or fallback
    const evaluationDates: { date: string; score: number }[] = [];
    for (const oa of allOas) {
      if (oa.last_evaluation_date && oa.evaluation_count > 0) {
        const score = masteryToScore(oa.nivel_logro);
        evaluationDates.push({ date: oa.last_evaluation_date, score });
      }
    }
    // Group by date
    const dateMap: Record<string, number[]> = {};
    evaluationDates.forEach(({ date, score }) => {
      const day = date.split("T")[0];
      if (!dateMap[day]) dateMap[day] = [];
      dateMap[day].push(score);
    });
    const timeData = Object.entries(dateMap)
      .map(([date, scores]) => ({
        date,
        score: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-30);

    // Worst OA (lowest score)
    let worstOA: OAItem | null = null;
    let worstScore = Infinity;
    for (const oa of allOas) {
      const score = masteryToScore(oa.nivel_logro);
      if (score < worstScore) {
        worstScore = score;
        worstOA = oa;
      }
    }

    return { allOas, streak, avgScore, ejeData, timeData, worstOA };
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400 mx-auto mb-4" />
          <p className="text-gray-400">Cargando progreso...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center text-3xl mb-4">
          <AlertCircle className="w-8 h-8 text-red-400" />
        </div>
        <h2 className="text-lg font-semibold mb-2">Error al cargar datos</h2>
        <p className="text-gray-400 text-sm max-w-md">{error}</p>
      </div>
    );
  }

  const summary = data?.summary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-5xl mx-auto space-y-8"
    >
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Tu Progreso</h1>
        <p className="text-gray-400 text-sm mt-1">
          Resumen de tu avance en el plan de estudios
        </p>
      </div>

      {/* --- 1. Summary Cards --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel rounded-2xl p-6"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
          <p className="text-3xl font-bold text-emerald-400">
            {summary?.mastered ?? 0}
            <span className="text-lg text-gray-500 font-normal">
              {" "}
              / {summary?.total_oas ?? 0}
            </span>
          </p>
          <p className="text-sm text-gray-400 mt-1">OA completados</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-panel rounded-2xl p-6"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
              <Flame className="w-5 h-5 text-orange-400" />
            </div>
          </div>
          <p className="text-3xl font-bold text-orange-400">
            {streak}
            <span className="text-lg text-gray-500 font-normal"> días</span>
          </p>
          <p className="text-sm text-gray-400 mt-1">Racha consecutiva</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-panel rounded-2xl p-6"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
              <Award className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <p className="text-3xl font-bold text-indigo-400">
            {avgScore}
            <span className="text-lg text-gray-500 font-normal"> / 4</span>
          </p>
          <p className="text-sm text-gray-400 mt-1">Puntuación promedio</p>
        </motion.div>
      </div>

      {/* --- 2. Bar Chart — Dominio por Eje Temático --- */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass-panel rounded-2xl p-6"
      >
        <h2 className="text-lg font-semibold mb-6">Dominio por Eje Temático</h2>
        {ejeData.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">
            No hay datos de ejes temáticos disponibles
          </p>
        ) : (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={ejeData}
                margin={{ top: 10, right: 10, left: -10, bottom: 60 }}
                barSize={28}
                barGap={2}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  tickLine={false}
                  angle={-25}
                  textAnchor="end"
                />
                <YAxis
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(2,2,8,0.95)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#fff", fontWeight: 600 }}
                />
                <Bar dataKey="Dominado" stackId="a" fill="#22c55e" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Parcial" stackId="a" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                <Bar dataKey="En progreso" stackId="a" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                <Bar dataKey="No iniciado" stackId="a" fill="#6b7280" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-4 mt-4 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-emerald-500" /> Dominado
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-amber-500" /> Parcial
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-blue-500" /> En progreso
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-gray-500" /> No iniciado
          </span>
        </div>
      </motion.div>

      {/* --- 3. Line Chart — Progreso en el Tiempo --- */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-panel rounded-2xl p-6"
      >
        <h2 className="text-lg font-semibold mb-6">Progreso en el Tiempo</h2>
        {timeData.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">
            Aún no tienes evaluaciones registradas. ¡Empieza a aprender para ver tu evolución!
          </p>
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeData} margin={{ top: 10, right: 10, left: -10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#9ca3af", fontSize: 10 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  tickLine={false}
                  tickFormatter={(val: string) => {
                    const d = new Date(val);
                    return d.toLocaleDateString("es-CL", { day: "numeric", month: "short" });
                  }}
                />
                <YAxis
                  domain={[0, 4]}
                  ticks={[0, 1, 2, 3, 4]}
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(val: number) => {
                    const labels = ["", "No iniciado", "En progreso", "Parcial", "Dominado"];
                    return labels[val] || "";
                  }}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(2,2,8,0.95)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#fff", fontWeight: 600 }}
                  formatter={(value: number) => {
                    const labels = ["", "No iniciado", "En progreso", "Parcial", "Dominado"];
                    return [labels[Math.round(value)] || `${value.toFixed(1)}`, "Nivel"];
                  }}
                  labelFormatter={(label: string) =>
                    new Date(label).toLocaleDateString("es-CL", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                    })
                  }
                />
                <defs>
                  <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#818cf8" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="none"
                  fill="url(#scoreGradient)"
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#818cf8"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#818cf8", stroke: "#020208", strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: "#a78bfa", stroke: "#020208", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </motion.div>

      {/* --- 4. OA List with Status --- */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="glass-panel rounded-2xl p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Objetivos de Aprendizaje</h2>
          <span className="text-xs text-gray-500">{allOas.length} OA</span>
        </div>

        {allOas.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">
            No hay objetivos de aprendizaje en el plan de estudios
          </p>
        ) : (
          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
            {allOas.map((oa, idx) => (
              <motion.div
                key={oa.id_oa}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.02 }}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/5 transition-colors"
              >
                <span className="text-base flex-shrink-0">
                  {LEVEL_EMOJI[oa.nivel_logro] ?? "🔴"}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full">
                      {oa.id_oa}
                    </span>
                    <span
                      className="text-[10px] font-medium"
                      style={{ color: LEVEL_COLOR[oa.nivel_logro] ?? "#6b7280" }}
                    >
                      {LEVEL_LABEL[oa.nivel_logro] ?? "Desconocido"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 mt-1 line-clamp-2">
                    {oa.descripcion}
                  </p>
                  {oa.conceptos_clave && oa.conceptos_clave.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {oa.conceptos_clave.slice(0, 3).map((c) => (
                        <span
                          key={c}
                          className="text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-full"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0 text-right">
                  <p className="text-xs text-gray-500">{oa.evaluation_count} eval.</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* --- 5. Continue Button --- */}
      {worstOA && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-panel-interactive rounded-2xl p-6"
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Continuar donde lo dejé</h2>
              <p className="text-sm text-gray-400 mt-1">
                Tu OA con menor avance:{" "}
                <span className="text-cyan-400 font-medium">{worstOA.id_oa}</span>
                {" — "}
                {worstOA.descripcion.substring(0, 80)}...
              </p>
            </div>
            <Link
              href={`/dashboard/chat?curso=${encodeURIComponent(data?.curriculum_tree[0]?.curso ?? "")}&asignatura=${encodeURIComponent(data?.curriculum_tree[0]?.asignaturas[0]?.asignatura ?? "")}&oa=${worstOA.id_oa}`}
              className="flex items-center gap-2 bg-gradient-accent text-white px-6 py-3 rounded-xl font-bold hover:opacity-95 transition-opacity shadow-lg shadow-indigo-500/20 flex-shrink-0"
            >
              Continuar
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}