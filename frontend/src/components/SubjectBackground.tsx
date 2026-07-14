import { useMemo, type ReactNode } from "react";
import type { SubjectTheme } from "@/lib/subjectTheme";

interface Props {
  theme: SubjectTheme;
}

/**
 * Fondo decorativo temático por asignatura.
 * Renderiza un patrón SVG sutil (baja opacidad) acorde a la materia activa.
 * Se ubica detrás del contenido como capa fija.
 */
export function SubjectBackground({ theme }: Props) {
  const pattern = useMemo(() => buildPattern(theme.key), [theme.key]);
  const id = `pat-${theme.key}`;

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      <svg
        className="h-full w-full opacity-[0.13] transition-opacity duration-700 dark:opacity-[0.08]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id={id}
            x="0"
            y="0"
            width={pattern.size}
            height={pattern.size}
            patternUnits="userSpaceOnUse"
          >
            <g
              fill="none"
              stroke={pattern.stroke}
              strokeWidth={pattern.strokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {pattern.content}
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill={`url(#${id})`} />
      </svg>
    </div>
  );
}

interface PatternSpec {
  size: number;
  stroke: string;
  strokeWidth: number;
  content: ReactNode;
}

function buildPattern(key: string): PatternSpec {
  switch (key) {
    case "math":
      return {
        size: 220,
        stroke: "#0284c7",
        strokeWidth: 1.4,
        content: (
          <g fontFamily="ui-monospace, monospace" fontSize="18" fill="#0284c7" stroke="none">
            <text x="10" y="30">π</text>
            <text x="60" y="80">∑</text>
            <text x="120" y="40">√x</text>
            <text x="170" y="100">∞</text>
            <text x="20" y="130">a² + b²</text>
            <text x="140" y="170">∫</text>
            <text x="60" y="200">7 + 3</text>
            <text x="180" y="200">÷</text>
            <text x="10" y="180">≠</text>
            <text x="100" y="110">x²</text>
          </g>
        ),
      };
    case "lang":
      return {
        size: 200,
        stroke: "#a21caf",
        strokeWidth: 1.4,
        content: (
          <>
            <g fontFamily="Georgia, serif" fontSize="22" fill="#a21caf" stroke="none">
              <text x="10" y="35">A</text>
              <text x="55" y="80">¿?</text>
              <text x="120" y="50">“”</text>
              <text x="160" y="110">;</text>
              <text x="20" y="150">¡!</text>
              <text x="80" y="180">abc</text>
              <text x="150" y="180">.</text>
            </g>
            {/* Pluma estilizada */}
            <path d="M40 110 q15 -15 35 -10 q-5 20 -20 25 z" />
            <path d="M150 30 q12 -10 28 -6 l-4 14 q-12 4 -22 0 z" />
          </>
        ),
      };
    case "science":
      return {
        size: 220,
        stroke: "#059669",
        strokeWidth: 1.4,
        content: (
          <>
            {/* Hoja */}
            <path d="M30 60 q20 -40 60 -30 q10 40 -30 60 q-30 0 -30 -30 z" />
            <path d="M40 70 q15 5 35 0" />
            {/* Molécula */}
            <circle cx="150" cy="50" r="6" />
            <circle cx="180" cy="80" r="6" />
            <circle cx="140" cy="90" r="6" />
            <path d="M150 50 L180 80 M150 50 L140 90 M180 80 L140 90" />
            {/* Gota */}
            <path d="M70 160 q-12 18 0 28 q12 -10 0 -28 z" />
            {/* Hojita */}
            <path d="M150 150 q18 -10 30 0 q-10 18 -30 0 z" />
            <path d="M150 150 L180 150" />
            {/* Átomo orbital */}
            <ellipse cx="190" cy="180" rx="22" ry="9" />
            <ellipse cx="190" cy="180" rx="22" ry="9" transform="rotate(60 190 180)" />
            <circle cx="190" cy="180" r="3" fill="#059669" />
          </>
        ),
      };
    case "history":
      return {
        size: 240,
        stroke: "#b45309",
        strokeWidth: 1.4,
        content: (
          <>
            {/* Globo */}
            <circle cx="50" cy="60" r="28" />
            <path d="M22 60 h56 M50 32 q-18 28 0 56 M50 32 q18 28 0 56" />
            {/* Brújula */}
            <circle cx="170" cy="70" r="24" />
            <path d="M170 50 L176 70 L170 90 L164 70 Z" fill="#b45309" stroke="none" />
            {/* Columna */}
            <path d="M60 150 v50 M70 150 v50 M80 150 v50 M55 150 h30 M55 200 h30" />
            {/* Pergamino */}
            <path d="M130 160 q10 -10 30 0 q10 -10 30 0 v30 q-10 10 -30 0 q-10 10 -30 0 z" />
            <path d="M140 170 h40 M140 178 h40 M140 186 h30" />
          </>
        ),
      };
    case "english":
      return {
        size: 200,
        stroke: "#4f46e5",
        strokeWidth: 1.4,
        content: (
          <g fontFamily="Helvetica, Arial, sans-serif" fontSize="20" fill="#4f46e5" stroke="none">
            <text x="10" y="35" fontWeight="700">Hi!</text>
            <text x="80" y="70">Hello</text>
            <text x="150" y="40">A B C</text>
            <text x="20" y="110">London</text>
            <text x="120" y="130">🇬🇧</text>
            <text x="40" y="170">Yes / No</text>
            <text x="150" y="180">?</text>
          </g>
        ),
      };
    case "music":
      return {
        size: 200,
        stroke: "#9333ea",
        strokeWidth: 1.6,
        content: (
          <>
            {/* Pentagrama */}
            <path d="M0 40 h200 M0 50 h200 M0 60 h200 M0 70 h200 M0 80 h200" strokeWidth="0.8" />
            {/* Nota corchea */}
            <circle cx="40" cy="75" r="6" fill="#9333ea" stroke="none" />
            <path d="M46 75 v-30 q14 6 12 22" />
            {/* Negra */}
            <circle cx="110" cy="65" r="6" fill="#9333ea" stroke="none" />
            <path d="M116 65 v-32" />
            {/* Doble corchea */}
            <circle cx="160" cy="70" r="6" fill="#9333ea" stroke="none" />
            <circle cx="185" cy="65" r="6" fill="#9333ea" stroke="none" />
            <path d="M166 70 v-30 M191 65 v-30 M166 40 h25" />
            {/* Clave de sol simplificada */}
            <path d="M20 150 q15 -10 15 -25 q0 -15 -15 -15 q-15 0 -15 18 q0 18 22 22 q22 4 22 22 q0 18 -22 18 q-12 0 -16 -10" />
          </>
        ),
      };
    case "art":
      return {
        size: 200,
        stroke: "#db2777",
        strokeWidth: 1.4,
        content: (
          <>
            {/* Paleta */}
            <path d="M40 60 q-30 0 -30 30 q0 30 30 30 q15 0 18 -12 q2 -10 12 -10 q20 0 20 -22 q0 -28 -50 -16 z" />
            <circle cx="30" cy="80" r="4" fill="#db2777" stroke="none" />
            <circle cx="45" cy="70" r="4" fill="#db2777" stroke="none" />
            <circle cx="60" cy="80" r="4" fill="#db2777" stroke="none" />
            {/* Pincel */}
            <path d="M130 30 l40 40 l-10 10 l-40 -40 z" />
            <path d="M120 80 q-10 20 0 30 q20 -10 20 -20 z" />
            {/* Lápiz */}
            <path d="M150 130 l40 40 M150 130 l-8 8 l40 40 l8 -8 z" />
            {/* Estrella */}
            <path d="M60 170 l6 14 l15 1 l-12 10 l4 15 l-13 -9 l-13 9 l4 -15 l-12 -10 l15 -1 z" />
          </>
        ),
      };
    default:
      return {
        size: 200,
        stroke: "#8b5cf6",
        strokeWidth: 1.4,
        content: (
          <>
            <circle cx="40" cy="40" r="4" fill="#8b5cf6" stroke="none" />
            <circle cx="120" cy="80" r="4" fill="#8b5cf6" stroke="none" />
            <circle cx="170" cy="150" r="4" fill="#8b5cf6" stroke="none" />
            <path d="M30 150 l8 -16 l8 16 l16 -8 l-8 16 l8 8 l-16 0 l-8 16 l-8 -16 l-16 0 l8 -8 l-8 -16 z" />
          </>
        ),
      };
  }
}
