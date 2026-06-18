"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { User, Volume2, Save } from "lucide-react";

export default function PerfilPage() {
  const [autoPlay, setAutoPlay] = useState(false);
  const [saved, setSaved] = useState(false);
  const [user, setUser] = useState<{ email: string; id: string } | null>(null);
  const [profile, setProfile] = useState<{
    full_name: string;
    grade_level: string;
  } | null>(null);

  useEffect(() => {
    // Load preference
    const stored = localStorage.getItem("sp_auto_play_audio");
    setAutoPlay(stored === "true");

    // Load user info
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user: authUser } }) => {
      if (!authUser) return;
      setUser({ email: authUser.email ?? "", id: authUser.id });

      const { data: profileData } = await supabase
        .from("profiles")
        .select("full_name, grade_level")
        .eq("id", authUser.id)
        .single();

      if (profileData) {
        setProfile(profileData);
      }
    });
  }, []);

  const handleToggleAutoPlay = (value: boolean) => {
    setAutoPlay(value);
    localStorage.setItem("sp_auto_play_audio", value.toString());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Tu Perfil</h1>
        <p className="text-gray-400 text-sm mt-1">
          Administra tu información y preferencias
        </p>
      </div>

      {/* User info card */}
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
            <User className="w-7 h-7 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">
              {profile?.full_name ?? "Usuario"}
            </h2>
            <p className="text-sm text-gray-400">{user?.email}</p>
            {profile?.grade_level && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-medium text-cyan-400 mt-1">
                {profile.grade_level}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="glass-panel rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-6">Preferencias</h2>

        <div className="space-y-6">
          {/* Auto-play audio toggle */}
          <div className="flex items-center justify-between">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                <Volume2 className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">
                  Reproducir respuestas automáticamente
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Al recibir una respuesta del tutor IA, se reproducirá en voz
                  alta automáticamente
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={autoPlay}
                onChange={(e) => handleToggleAutoPlay(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/10 rounded-full peer peer-checked:bg-indigo-500 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all" />
            </label>
          </div>
        </div>

        {/* Saved indicator */}
        {saved && (
          <div className="flex items-center gap-2 mt-6 text-emerald-400 text-xs">
            <Save className="w-3 h-3" />
            Preferencia guardada
          </div>
        )}
      </div>

      {/* Info */}
      <div className="glass-panel rounded-2xl p-6 text-center">
        <p className="text-xs text-gray-500">
          Más opciones de configuración y personalización próximamente.
        </p>
      </div>
    </div>
  );
}