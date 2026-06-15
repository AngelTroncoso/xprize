import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Super_Profesor - Tutoría Hiperpersonalizada IA",
  description: "Entorno educativo multi-agente impulsado por Gemini para un aprendizaje experto y adaptable.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
