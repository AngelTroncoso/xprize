import { InteractiveExercise } from "@/lib/apiService";

interface Props {
  exercise: InteractiveExercise;
}

export function MultipleChoice({ exercise }: Props) {
  if (!exercise.options) return null;
  
  return (
    <div className="flex flex-col gap-3">
      {exercise.options.map((opt, i) => (
        <div key={i} className="rounded-lg border-2 border-slate-200 bg-slate-50 p-4 text-center text-base font-medium text-slate-700 hover:border-blue-400 hover:bg-blue-50 transition cursor-pointer">
          {opt}
        </div>
      ))}
    </div>
  );
}
