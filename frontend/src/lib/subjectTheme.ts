import {
  BookOpen,
  Calculator,
  Globe2,
  Languages,
  Leaf,
  Music2,
  Palette,
  Sparkles,
  Laptop,
  Activity,
  type LucideIcon,
} from "lucide-react";

export interface SubjectTheme {
  key: string;
  label: string;
  emoji: string;
  icon: LucideIcon;
  // Background del shell
  appBg: string;
  // Gradiente del header / acentos
  gradient: string; // "from-X to-Y"
  gradientVia?: string;
  // Colores tailwind base (sin prefijo, ej "sky", "emerald")
  base: string;
  // Clases utilitarias derivadas
  ring: string;
  border: string;
  softBg: string;
  chip: string;
  text: string;
  glow: string;
  greeting: string;
}

const THEMES: Record<string, SubjectTheme> = {
  Matemática: {
    key: "math",
    label: "Matemática",
    emoji: "🧮",
    icon: Calculator,
    appBg: "bg-gradient-to-br from-sky-50 via-cyan-50 to-indigo-100",
    gradient: "from-sky-500 to-indigo-600",
    gradientVia: "via-cyan-500",
    base: "sky",
    ring: "ring-sky-300",
    border: "border-sky-200",
    softBg: "bg-sky-50",
    chip: "bg-sky-100 text-sky-700",
    text: "text-sky-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(14,165,233,0.45)]",
    greeting: "¡Resolvamos un desafío numérico! ➕✖️",
  },
  "Lenguaje y Comunicación": {
    key: "lang",
    label: "Lenguaje y Comunicación",
    emoji: "📖",
    icon: BookOpen,
    appBg: "bg-gradient-to-br from-rose-50 via-fuchsia-50 to-violet-100",
    gradient: "from-fuchsia-500 to-violet-600",
    gradientVia: "via-pink-500",
    base: "fuchsia",
    ring: "ring-fuchsia-300",
    border: "border-fuchsia-200",
    softBg: "bg-fuchsia-50",
    chip: "bg-fuchsia-100 text-fuchsia-700",
    text: "text-fuchsia-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(217,70,239,0.45)]",
    greeting: "¿Leemos un cuento o escribimos uno juntos? ✍️",
  },
  "Ciencias Naturales": {
    key: "science",
    label: "Ciencias Naturales",
    emoji: "🌿",
    icon: Leaf,
    appBg: "bg-gradient-to-br from-emerald-50 via-teal-50 to-lime-100",
    gradient: "from-emerald-500 to-teal-600",
    gradientVia: "via-green-500",
    base: "emerald",
    ring: "ring-emerald-300",
    border: "border-emerald-200",
    softBg: "bg-emerald-50",
    chip: "bg-emerald-100 text-emerald-700",
    text: "text-emerald-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(16,185,129,0.45)]",
    greeting: "¡Exploremos el mundo natural! 🔬🪴",
  },
  "Historia y Geografía": {
    key: "history",
    label: "Historia y Geografía",
    emoji: "🌎",
    icon: Globe2,
    appBg: "bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-100",
    gradient: "from-amber-500 to-orange-600",
    gradientVia: "via-yellow-500",
    base: "amber",
    ring: "ring-amber-300",
    border: "border-amber-200",
    softBg: "bg-amber-50",
    chip: "bg-amber-100 text-amber-800",
    text: "text-amber-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(245,158,11,0.45)]",
    greeting: "¡Viajemos por el tiempo y el mapa! 🗺️",
  },
  Inglés: {
    key: "english",
    label: "Inglés",
    emoji: "🗣️",
    icon: Languages,
    appBg: "bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-100",
    gradient: "from-indigo-500 to-blue-600",
    base: "indigo",
    ring: "ring-indigo-300",
    border: "border-indigo-200",
    softBg: "bg-indigo-50",
    chip: "bg-indigo-100 text-indigo-700",
    text: "text-indigo-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(99,102,241,0.45)]",
    greeting: "Let's practice English together! 🇬🇧",
  },
  Música: {
    key: "music",
    label: "Música",
    emoji: "🎵",
    icon: Music2,
    appBg: "bg-gradient-to-br from-purple-50 via-pink-50 to-rose-100",
    gradient: "from-purple-500 to-pink-600",
    base: "purple",
    ring: "ring-purple-300",
    border: "border-purple-200",
    softBg: "bg-purple-50",
    chip: "bg-purple-100 text-purple-700",
    text: "text-purple-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(168,85,247,0.45)]",
    greeting: "¡Hagamos música juntos! 🎶",
  },
  Arte: {
    key: "art",
    label: "Arte",
    emoji: "🎨",
    icon: Palette,
    appBg: "bg-gradient-to-br from-pink-50 via-rose-50 to-orange-100",
    gradient: "from-pink-500 to-orange-500",
    base: "pink",
    ring: "ring-pink-300",
    border: "border-pink-200",
    softBg: "bg-pink-50",
    chip: "bg-pink-100 text-pink-700",
    text: "text-pink-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(236,72,153,0.45)]",
    greeting: "¡Demos rienda suelta a la creatividad! 🖌️",
  },
  Tecnología: {
    key: "tech",
    label: "Tecnología",
    emoji: "💻",
    icon: Laptop,
    appBg: "bg-gradient-to-br from-slate-50 via-gray-100 to-zinc-200",
    gradient: "from-slate-600 to-zinc-800",
    base: "slate",
    ring: "ring-slate-300",
    border: "border-slate-300",
    softBg: "bg-slate-100",
    chip: "bg-slate-200 text-slate-800",
    text: "text-slate-800",
    glow: "shadow-[0_10px_30px_-10px_rgba(71,85,105,0.45)]",
    greeting: "¡Diseñemos y construyamos el futuro! ⚙️",
  },
  "Educación Física y Salud": {
    key: "pe",
    label: "Educación Física y Salud",
    emoji: "🏃",
    icon: Activity,
    appBg: "bg-gradient-to-br from-red-50 via-orange-50 to-rose-100",
    gradient: "from-red-500 to-orange-500",
    base: "red",
    ring: "ring-red-300",
    border: "border-red-200",
    softBg: "bg-red-50",
    chip: "bg-red-100 text-red-700",
    text: "text-red-700",
    glow: "shadow-[0_10px_30px_-10px_rgba(239,68,68,0.45)]",
    greeting: "¡A moverse y cuidar nuestra salud! 👟",
  },
};

const DEFAULT: SubjectTheme = {
  key: "default",
  label: "General",
  emoji: "✨",
  icon: Sparkles,
  appBg: "bg-gradient-to-br from-slate-50 via-violet-50 to-pink-50",
  gradient: "from-violet-500 to-fuchsia-500",
  base: "violet",
  ring: "ring-violet-300",
  border: "border-violet-200",
  softBg: "bg-violet-50",
  chip: "bg-violet-100 text-violet-700",
  text: "text-violet-700",
  glow: "shadow-[0_10px_30px_-10px_rgba(139,92,246,0.45)]",
  greeting: "¿Sobre qué quieres aprender hoy?",
};

export function getSubjectTheme(asignatura: string): SubjectTheme {
  return THEMES[asignatura] ?? DEFAULT;
}

export const ASIGNATURAS = Object.keys(THEMES);

export const CURSOS = [
  "1° Básico",
  "2° Básico",
  "3° Básico",
  "4° Básico",
  "5° Básico",
  "6° Básico",
  "7° Básico",
  "8° Básico",
];

export const CURSO_META: Record<string, { emoji: string; gradient: string }> = {
  "1° Básico": { emoji: "🐣", gradient: "from-pink-400 to-rose-400" },
  "2° Básico": { emoji: "🦊", gradient: "from-orange-400 to-amber-400" },
  "3° Básico": { emoji: "🐯", gradient: "from-amber-400 to-yellow-400" },
  "4° Básico": { emoji: "🦁", gradient: "from-yellow-400 to-lime-400" },
  "5° Básico": { emoji: "🐼", gradient: "from-emerald-400 to-teal-400" },
  "6° Básico": { emoji: "🦉", gradient: "from-sky-400 to-cyan-400" },
  "7° Básico": { emoji: "🚀", gradient: "from-indigo-400 to-blue-500" },
  "8° Básico": { emoji: "🛰️", gradient: "from-violet-500 to-fuchsia-500" },
};
