const CURRICULUM_ENTRIES = [
  { curso: "1° Básico", asignatura: "Lenguaje y Comunicación" },
  { curso: "1° Básico", asignatura: "Matemática" },
  { curso: "2° Básico", asignatura: "Lenguaje y Comunicación" },
  { curso: "2° Básico", asignatura: "Matemática" },
  { curso: "3° Básico", asignatura: "Matemática" },
  { curso: "5° Básico", asignatura: "Lenguaje y Comunicación" },
  { curso: "5° Básico", asignatura: "Matemática" },
  { curso: "6° Básico", asignatura: "Lenguaje y Comunicación" },
  { curso: "6° Básico", asignatura: "Matemática" },
  { curso: "7° Básico", asignatura: "Lenguaje y Comunicación" },
  { curso: "7° Básico", asignatura: "Matemática" },
  { curso: "8° Básico", asignatura: "Lenguaje y Comunicación" },
  { curso: "8° Básico", asignatura: "Matemática" },
];

export const COURSES = Array.from(
  new Set(CURRICULUM_ENTRIES.map((e) => e.curso))
).sort();

export function getSubjectsForCourse(curso: string): string[] {
  return CURRICULUM_ENTRIES.filter((e) => e.curso === curso).map(
    (e) => e.asignatura
  );
}