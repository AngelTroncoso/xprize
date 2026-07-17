import { MINEDUC_BOOKS, Textbook } from "@/lib/books";
import { getSubjectTheme } from "@/lib/subjectTheme";
import { BookOpen } from "lucide-react";

interface Props {
  curso: string;
  asignatura: string;
  onSelectBook: (book: Textbook) => void;
}

export function Bookshelf({ curso, asignatura, onSelectBook }: Props) {
  // Filtrar los libros por el curso y asignatura seleccionados en la cabecera
  const filteredBooks = MINEDUC_BOOKS.filter(
    (b) => b.curso === curso && b.asignatura === asignatura
  );

  const theme = getSubjectTheme(asignatura);

  return (
    <div className="flex flex-col items-center gap-8 py-8">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-foreground">Tu Biblioteca MINEDUC</h2>
        <p className="mt-2 text-foreground/60">Selecciona tu libro para comenzar a aprender</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
        {filteredBooks.map((book) => (
          <div 
            key={book.id} 
            className="group relative flex flex-col items-center cursor-pointer transition-transform hover:-translate-y-2"
            onClick={() => onSelectBook(book)}
          >
            {/* Libro Portada */}
            <div className={`w-48 h-64 rounded-r-xl rounded-l-sm bg-white shadow-xl ring-1 ring-black/10 overflow-hidden relative border-l-4 ${theme.border}`}>
              {book.portada_url ? (
                <img src={book.portada_url} alt={book.titulo} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-slate-100">
                  <BookOpen className={`w-12 h-12 ${theme.text} opacity-50`} />
                </div>
              )}
              {/* Lomo del libro simulado */}
              <div className="absolute inset-y-0 left-0 w-1 bg-black/10" />
            </div>

            {/* Repisa */}
            <div className="w-56 h-4 bg-amber-700/80 rounded mt-2 shadow-sm border-b-2 border-amber-900/50" />
            <div className="w-48 h-8 bg-amber-900/40 clip-shelf -mt-1 blur-sm opacity-50" />

            {/* Titulo */}
            <div className="mt-4 text-center">
              <h3 className="font-bold text-slate-800 group-hover:text-blue-600 transition-colors">{book.titulo}</h3>
              <p className="text-sm text-slate-500">{book.curso}</p>
            </div>
          </div>
        ))}

        {filteredBooks.length === 0 && (
          <div className="col-span-full py-12 text-center text-slate-500">
            No hay libros disponibles para {curso} - {asignatura}.
          </div>
        )}
      </div>
    </div>
  );
}
