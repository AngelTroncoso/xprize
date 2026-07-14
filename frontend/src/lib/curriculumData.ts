import type { ProgressTree } from "./apiService";

// Datos estáticos simulados basados en el currículum MINEDUC (Chile).
// Matemática 3° y 4° básico + Lenguaje 3° básico.
export const MOCK_PROGRESS: ProgressTree = {
  student_id: 1,
  student_name: "Martina Rojas",
  cursos: [
    {
      name: "3° Básico",
      asignaturas: [
        {
          name: "Matemática",
          ejes: [
            {
              name: "Números y Operaciones",
              oas: [
                {
                  code: "OA_01",
                  title: "Contar números del 0 al 1.000",
                  concepts: ["Conteo", "Secuencias", "Patrones numéricos"],
                  status: "dominado",
                },
                {
                  code: "OA_06",
                  title: "Demostrar que comprenden la adición y sustracción",
                  concepts: ["Suma", "Resta", "Reagrupación"],
                  status: "en_progreso",
                },
                {
                  code: "OA_08",
                  title: "Demostrar la multiplicación hasta 10x10",
                  concepts: ["Tablas de multiplicar", "Grupos iguales"],
                  status: "no_iniciado",
                },
              ],
            },
            {
              name: "Geometría",
              oas: [
                {
                  code: "OA_16",
                  title: "Describir cubos, paralelepípedos, esferas, conos y cilindros",
                  concepts: ["Figuras 3D", "Caras", "Aristas", "Vértices"],
                  status: "en_progreso",
                },
              ],
            },
            {
              name: "Medición",
              oas: [
                {
                  code: "OA_21",
                  title: "Leer y registrar la hora en relojes análogos y digitales",
                  concepts: ["Hora", "Minutos", "Reloj"],
                  status: "dominado",
                },
              ],
            },
          ],
        },
        {
          name: "Lenguaje y Comunicación",
          ejes: [
            {
              name: "Lectura",
              oas: [
                {
                  code: "OA_04",
                  title: "Profundizar su comprensión de las narraciones leídas",
                  concepts: ["Personajes", "Ambiente", "Problema", "Solución"],
                  status: "dominado",
                },
                {
                  code: "OA_06",
                  title: "Leer independientemente y comprender textos no literarios",
                  concepts: ["Idea principal", "Información explícita"],
                  status: "en_progreso",
                },
              ],
            },
            {
              name: "Escritura",
              oas: [
                {
                  code: "OA_15",
                  title: "Escribir cartas, instrucciones y noticias",
                  concepts: ["Estructura del texto", "Propósito comunicativo"],
                  status: "no_iniciado",
                },
              ],
            },
            {
              name: "Comunicación Oral",
              oas: [
                {
                  code: "OA_27",
                  title: "Expresarse de manera coherente y articulada",
                  concepts: ["Vocabulario", "Pronunciación", "Volumen"],
                  status: "en_progreso",
                },
              ],
            },
          ],
        },
      ],
    },
    {
      name: "4° Básico",
      asignaturas: [
        {
          name: "Matemática",
          ejes: [
            {
              name: "Números y Operaciones",
              oas: [
                {
                  code: "OA_03",
                  title: "Demostrar que comprenden la adición y sustracción de números hasta 1.000",
                  concepts: ["Algoritmo", "Estimación", "Reagrupación"],
                  status: "no_iniciado",
                },
                {
                  code: "OA_08",
                  title: "Demostrar que comprenden las fracciones con denominadores 100, 12, 10, 8, 6, 5, 4, 3, 2",
                  concepts: ["Fracciones", "Denominador", "Numerador"],
                  status: "no_iniciado",
                },
              ],
            },
            {
              name: "Patrones y Álgebra",
              oas: [
                {
                  code: "OA_13",
                  title: "Identificar y describir patrones numéricos",
                  concepts: ["Patrón", "Regla", "Secuencia"],
                  status: "no_iniciado",
                },
              ],
            },
          ],
        },
      ],
    },
  ],
};
