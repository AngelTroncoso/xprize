import { InteractiveExercise } from "@/lib/apiService";
import { MultipleChoice } from "./MultipleChoice";
import { FillInBlanks } from "./FillInBlanks";
import { VisualImage } from "./VisualImage";

interface Props {
  exercise: InteractiveExercise;
}

export function ExerciseOverlay({ exercise }: Props) {
  return (
    <div className="w-full rounded-2xl bg-white/95 p-8 shadow-2xl ring-1 ring-black/5 overflow-y-auto max-h-full flex flex-col pointer-events-auto">
      <div className="mb-6 flex items-start justify-between">
        <h3 className="text-2xl font-extrabold text-slate-800">{exercise.title}</h3>
        {/* We can put an icon or something here */}
      </div>
      
      <div className="flex-1 flex flex-col justify-center">
        {exercise.type === "multiple_choice" && <MultipleChoice exercise={exercise} />}
        {exercise.type === "fill_in_blanks" && <FillInBlanks exercise={exercise} />}
        {exercise.type === "visual_image" && <VisualImage exercise={exercise} />}
      </div>
      
      <div className="mt-4 text-center text-xs text-slate-400 font-medium">
        💡 Usa el lápiz si necesitas hacer cálculos a los lados, y escribe tu respuesta en el chat o dale a Enviar Pizarra.
      </div>
    </div>
  );
}
