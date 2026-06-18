import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { data: profile } = await supabase
    .from("profiles")
    .select("full_name, grade_level")
    .eq("id", user?.id)
    .single();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold mb-2">
          Bienvenido, {profile?.full_name ?? user?.email?.split("@")[0]}
        </h1>
        <p className="text-gray-400">
          {profile?.grade_level && `Nivel: ${profile.grade_level} · `}
          Panel de control de Super_Profesor
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="glass-panel rounded-2xl p-6">
          <p className="text-gray-400 text-sm mb-1">Lecciones completadas</p>
          <p className="text-3xl font-bold text-indigo-400">0</p>
        </div>
        <div className="glass-panel rounded-2xl p-6">
          <p className="text-gray-400 text-sm mb-1">Horas de estudio</p>
          <p className="text-3xl font-bold text-cyan-400">0</p>
        </div>
        <div className="glass-panel rounded-2xl p-6">
          <p className="text-gray-400 text-sm mb-1">Precisión promedio</p>
          <p className="text-3xl font-bold text-emerald-400">—</p>
        </div>
      </div>

      {/* Welcome card */}
      <div className="glass-panel-interactive p-8 rounded-2xl">
        <h2 className="text-xl font-bold mb-4">Empieza tu aprendizaje</h2>
        <p className="text-gray-400 leading-relaxed mb-6">
          Explora las secciones de Chat para conversar con tu tutor IA, 
          Progreso para ver tu evolución, y Perfil para ajustar tu configuración.
        </p>
        <div className="flex flex-wrap gap-4">
          <a
            href="/dashboard/chat"
            className="bg-gradient-accent text-white px-6 py-3 rounded-xl font-bold hover:opacity-95 transition-opacity shadow-lg shadow-indigo-500/20"
          >
            Ir al Chat
          </a>
          <a
            href="/dashboard/progreso"
            className="glass-panel text-white px-6 py-3 rounded-xl font-bold hover:border-white/20 transition-all"
          >
            Ver Progreso
          </a>
        </div>
      </div>
    </div>
  );
}