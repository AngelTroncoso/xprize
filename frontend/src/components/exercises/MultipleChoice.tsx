import { InteractiveExercise } from "@/lib/apiService";

interface Props {
  exercise: InteractiveExercise;
}

export function MultipleChoice({ exercise }: Props) {
  if (!exercise.options) return null;
  
  return (
    <div className="flex flex-col gap-4 mt-6">
      {exercise.options.map((opt, i) => (
        <button 
          key={i} 
          className="w-full rounded-xl border-2 border-slate-300 bg-white p-5 text-left text-lg font-medium text-slate-800 shadow-sm transition hover:border-blue-500 hover:bg-blue-50 focus:outline-none focus:ring-4 focus:ring-blue-100"
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
