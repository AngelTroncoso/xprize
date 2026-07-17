import { InteractiveExercise } from "@/lib/apiService";

interface Props {
  exercise: InteractiveExercise;
}

export function FillInBlanks({ exercise }: Props) {
  if (!exercise.text_with_blanks) return null;
  
  // Replace ___ with a styled blank space
  const parts = exercise.text_with_blanks.split("___");
  
  return (
    <div className="text-center text-xl leading-relaxed text-slate-700">
      {parts.map((part, i) => (
        <span key={i}>
          {part}
          {i < parts.length - 1 && (
            <span className="inline-block mx-2 w-24 border-b-4 border-slate-300"></span>
          )}
        </span>
      ))}
    </div>
  );
}
