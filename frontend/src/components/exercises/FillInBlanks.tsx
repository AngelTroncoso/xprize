import { InteractiveExercise } from "@/lib/apiService";

interface Props {
  exercise: InteractiveExercise;
}

export function FillInBlanks({ exercise }: Props) {
  if (!exercise.text_with_blanks) return null;
  
  // Replace ___ with a styled blank space
  const parts = exercise.text_with_blanks.split("___");
  
  return (
    <div className="text-left text-2xl leading-relaxed text-slate-800 mt-6 font-medium">
      {parts.map((part, i) => (
        <span key={i}>
          {part}
          {i < parts.length - 1 && (
            <span className="inline-block mx-2 w-28 h-10 align-middle rounded border-2 border-slate-300 bg-slate-50 shadow-inner"></span>
          )}
        </span>
      ))}
    </div>
  );
}
