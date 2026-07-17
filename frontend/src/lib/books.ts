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
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72014:Texto-del-Estudiante-Matematica-1-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145415_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "mat-2",
    curso: "2° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 2° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72015:Texto-del-Estudiante-Matematica-2-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145416_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "mat-3",
    curso: "3° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 3° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72016:Texto-del-Estudiante-Matematica-3-Basico.jpg",
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
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72017:Texto-del-Estudiante-Matematica-4-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145418_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "mat-5",
    curso: "5° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 5° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72018:Texto-del-Estudiante-Matematica-5-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145419_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "mat-6",
    curso: "6° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 6° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72019:Texto-del-Estudiante-Matematica-6-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145420_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "mat-7",
    curso: "7° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 7° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72020:Texto-del-Estudiante-Matematica-7-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145421_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "mat-8",
    curso: "8° Básico",
    asignatura: "Matemática",
    titulo: "Matemática 8° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72021:Texto-del-Estudiante-Matematica-8-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145422_recurso_pdf.pdf",
    gemini_file_id: ""
  },

  // LENGUAJE Y COMUNICACIÓN
  {
    id: "len-1",
    curso: "1° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 1° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72006:Texto-del-Estudiante-Lenguaje-y-Comunicacion-1-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145407_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "len-2",
    curso: "2° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 2° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72007:Texto-del-Estudiante-Lenguaje-y-Comunicacion-2-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145408_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "len-3",
    curso: "3° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 3° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72008:Texto-del-Estudiante-Lenguaje-y-Comunicacion-3-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145409_recurso_pdf.pdf",
    gemini_file_id: ""
  },
  {
    id: "len-4",
    curso: "4° Básico",
    asignatura: "Lenguaje y Comunicación",
    titulo: "Lenguaje 4° Básico",
    portada_url: "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72009:Texto-del-Estudiante-Lenguaje-y-Comunicacion-4-Basico.jpg",
    pdf_url: "https://www.curriculumnacional.cl/614/articles-145410_recurso_pdf.pdf",
    gemini_file_id: ""
  }
];
