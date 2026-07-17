import { InteractiveExercise } from "@/lib/apiService";

interface Props {
  exercise: InteractiveExercise;
}

export function VisualImage({ exercise }: Props) {
  if (!exercise.image_url && !exercise.image_prompt) return null;
  
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="text-center text-sm text-slate-500 italic">
        {exercise.image_prompt}
      </div>
      {exercise.image_url ? (
        <img 
          src={exercise.image_url} 
          alt={exercise.image_prompt || "Ejercicio visual"} 
          className="max-h-64 rounded-xl object-contain shadow-md"
        />
      ) : (
        <div className="flex h-48 w-full max-w-sm items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 text-slate-400">
          <p>Generando imagen...</p>
        </div>
      )}
    </div>
  );
}
