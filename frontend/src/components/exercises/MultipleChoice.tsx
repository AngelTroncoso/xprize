import { useState } from "react";
import { InteractiveExercise } from "@/lib/apiService";
import { toast } from "sonner";
import { Star, XCircle } from "lucide-react";
import confetti from "canvas-confetti";

interface Props {
  exercise: InteractiveExercise;
}

export function MultipleChoice({ exercise }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);

  if (!exercise.options) return null;

  const handleSelect = (idx: number, opt: string) => {
    if (selected !== null && isCorrect) return; // Ya respondió bien

    setSelected(idx);
    
    // Si no hay correct_answer definida por la IA, se asume correcta por explorar
    const correctAnswer = exercise.correct_answer?.trim().toLowerCase();
    const currentOpt = opt.trim().toLowerCase();
    
    if (!correctAnswer || currentOpt === correctAnswer) {
      setIsCorrect(true);
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#f59e0b', '#10b981', '#3b82f6', '#a855f7']
      });
      toast.success("¡Excelente! Respuesta correcta 🌟", { position: "top-center" });
    } else {
      setIsCorrect(false);
      toast.error("Mmm, intenta de nuevo 🤔", { position: "top-center" });
      // Shake effect can be done with tailwind classes
    }
  };

  return (
    <div className="flex flex-col gap-4 mt-6">
      {exercise.options.map((opt, i) => {
        let btnClass = "w-full rounded-xl border-2 border-slate-300 bg-white p-5 text-left text-lg font-medium text-slate-800 shadow-sm transition hover:border-blue-500 hover:bg-blue-50 focus:outline-none focus:ring-4 focus:ring-blue-100 flex items-center justify-between";
        
        if (selected === i) {
          if (isCorrect) {
            btnClass = "w-full rounded-xl border-2 border-green-500 bg-green-50 p-5 text-left text-lg font-bold text-green-800 shadow-md transition flex items-center justify-between scale-105 animate-in zoom-in";
          } else if (isCorrect === false) {
            btnClass = "w-full rounded-xl border-2 border-red-500 bg-red-50 p-5 text-left text-lg font-medium text-red-800 shadow-sm transition flex items-center justify-between";
          }
        } else if (selected !== null && isCorrect && exercise.correct_answer && exercise.correct_answer.trim().toLowerCase() === opt.trim().toLowerCase()) {
           btnClass = "w-full rounded-xl border-2 border-green-500 bg-green-50 p-5 text-left text-lg font-bold text-green-800 shadow-md transition flex items-center justify-between opacity-70";
        }

        return (
          <button 
            key={i} 
            onClick={() => handleSelect(i, opt)}
            className={btnClass}
            disabled={selected !== null && isCorrect}
          >
            <span>{opt}</span>
            {selected === i && isCorrect && <Star className="h-6 w-6 text-yellow-500 fill-yellow-500" />}
            {selected === i && isCorrect === false && <XCircle className="h-6 w-6 text-red-500" />}
          </button>
        );
      })}
    </div>
  );
}
