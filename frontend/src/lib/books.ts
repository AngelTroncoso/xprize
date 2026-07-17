export interface Chapter {
  id: string;
  title: string;
  page_start: number;
}

export interface Textbook {
  id: string;
  curso: string;
  asignatura: string;
  titulo: string;
  portada_url: string;
  pdf_url: string;
  gemini_file_id: string; // Para inyectarlo en el prompt de la IA
  chapters?: Chapter[];
}

export const MINEDUC_BOOKS: Textbook[] = [
  // MATEMÁTICA
  {
    id: "mat-1",
    curso: "1° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 1° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145415_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-1-u1", title: "Unidad 1: Conociendo los números", page_start: 10 },
      { id: "mat-1-u2", title: "Unidad 2: Sumar y restar hasta 20", page_start: 50 },
      { id: "mat-1-u3", title: "Unidad 3: Figuras geométricas", page_start: 90 },
      { id: "mat-1-u4", title: "Unidad 4: Patrones y tiempo", page_start: 130 },
    ]
  },
  {
    id: "mat-2",
    curso: "2° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 2° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145416_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-2-u1", title: "Unidad 1: Contar hasta 100", page_start: 12 },
      { id: "mat-2-u2", title: "Unidad 2: Adición y sustracción", page_start: 48 },
      { id: "mat-2-u3", title: "Unidad 3: Multiplicación", page_start: 100 },
      { id: "mat-2-u4", title: "Unidad 4: Longitud y tiempo", page_start: 140 },
    ]
  },
  {
    id: "mat-3",
    curso: "3° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 3° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145417_recurso_pdf.pdf",
    gemini_file_id: "files/z82015efqcnv",
    chapters: [
      { id: "mat-3-u1", title: "Unidad 1: Números hasta el 1 000", page_start: 10 },
      { id: "mat-3-u2", title: "Unidad 2: Adición y sustracción", page_start: 46 },
      { id: "mat-3-u3", title: "Unidad 3: Multiplicación y división", page_start: 116 },
      { id: "mat-3-u4", title: "Unidad 4: Fracciones y tiempo", page_start: 184 },
      { id: "mat-3-u5", title: "Unidad 5: Geometría y medición", page_start: 242 },
    ]
  },
  {
    id: "mat-4",
    curso: "4° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 4° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145418_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-4-u1", title: "Unidad 1: Números hasta 10 000", page_start: 10 },
      { id: "mat-4-u2", title: "Unidad 2: Multiplicación y división", page_start: 50 },
      { id: "mat-4-u3", title: "Unidad 3: Fracciones y decimales", page_start: 120 },
      { id: "mat-4-u4", title: "Unidad 4: Geometría 3D", page_start: 180 },
    ]
  },
  {
    id: "mat-5",
    curso: "5° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 5° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145419_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-5-u1", title: "Unidad 1: Grandes números", page_start: 12 },
      { id: "mat-5-u2", title: "Unidad 2: Fracciones", page_start: 60 },
      { id: "mat-5-u3", title: "Unidad 3: Decimales", page_start: 110 },
      { id: "mat-5-u4", title: "Unidad 4: Área y perímetro", page_start: 160 },
    ]
  },
  {
    id: "mat-6",
    curso: "6° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 6° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145420_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-6-u1", title: "Unidad 1: Múltiplos y factores", page_start: 14 },
      { id: "mat-6-u2", title: "Unidad 2: Fracciones y razones", page_start: 55 },
      { id: "mat-6-u3", title: "Unidad 3: Porcentajes", page_start: 115 },
      { id: "mat-6-u4", title: "Unidad 4: Polígonos", page_start: 170 },
    ]
  },
  {
    id: "mat-7",
    curso: "7° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 7° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145421_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-7-u1", title: "Unidad 1: Números enteros", page_start: 10 },
      { id: "mat-7-u2", title: "Unidad 2: Proporcionalidad", page_start: 60 },
      { id: "mat-7-u3", title: "Unidad 3: Geometría", page_start: 120 },
      { id: "mat-7-u4", title: "Unidad 4: Probabilidad", page_start: 180 },
    ]
  },
  {
    id: "mat-8",
    curso: "8° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 8° Básico",
    portada_url: "/covers/cover_math.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145422_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "mat-8-u1", title: "Unidad 1: Números racionales", page_start: 12 },
      { id: "mat-8-u2", title: "Unidad 2: Álgebra y funciones", page_start: 70 },
      { id: "mat-8-u3", title: "Unidad 3: Teorema de Pitágoras", page_start: 130 },
      { id: "mat-8-u4", title: "Unidad 4: Estadística descriptiva", page_start: 190 },
    ]
  },

  // LENGUAJE Y COMUNICACIÓN
  {
    id: "len-1",
    curso: "1° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 1° Básico",
    portada_url: "/covers/cover_language.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145407_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "len-1-u1", title: "Unidad 1: Las Vocales", page_start: 8 },
      { id: "len-1-u2", title: "Unidad 2: Primeras Consonantes", page_start: 40 },
      { id: "len-1-u3", title: "Unidad 3: Lectura Inicial", page_start: 80 },
      { id: "len-1-u4", title: "Unidad 4: Cuentos y Fábulas", page_start: 120 },
    ]
  },
  {
    id: "len-2",
    curso: "2° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 2° Básico",
    portada_url: "/covers/cover_language.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145408_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "len-2-u1", title: "Unidad 1: Comprensión Lectora", page_start: 10 },
      { id: "len-2-u2", title: "Unidad 2: Poemas y Rimas", page_start: 50 },
      { id: "len-2-u3", title: "Unidad 3: Leyendas Chilenas", page_start: 100 },
      { id: "len-2-u4", title: "Unidad 4: Textos Informativos", page_start: 150 },
    ]
  },
  {
    id: "len-3",
    curso: "3° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 3° Básico",
    portada_url: "/covers/cover_language.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145409_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "len-3-u1", title: "Unidad 1: Narrativa y Cuentos", page_start: 12 },
      { id: "len-3-u2", title: "Unidad 2: El Mundo de la Poesía", page_start: 60 },
      { id: "len-3-u3", title: "Unidad 3: Textos No Literarios", page_start: 110 },
      { id: "len-3-u4", title: "Unidad 4: Obras de Teatro", page_start: 160 },
    ]
  },
  {
    id: "len-4",
    curso: "4° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 4° Básico",
    portada_url: "/covers/cover_language.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145410_recurso_pdf.pdf",
    gemini_file_id: "",
    chapters: [
      { id: "len-4-u1", title: "Unidad 1: Mitos y Leyendas", page_start: 14 },
      { id: "len-4-u2", title: "Unidad 2: Textos Poéticos", page_start: 70 },
      { id: "len-4-u3", title: "Unidad 3: Artículos Informativos", page_start: 125 },
      { id: "len-4-u4", title: "Unidad 4: Medios de Comunicación", page_start: 180 },
    ]
  }
];
