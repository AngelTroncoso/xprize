import { useState } from "react";
import { InteractiveExercise } from "@/lib/apiService";
import { toast } from "sonner";
import confetti from "canvas-confetti";
import { Button } from "@/components/ui/button";

interface Props {
  exercise: InteractiveExercise;
}

export function FillInBlanks({ exercise }: Props) {
  if (!exercise.text_with_blanks) return null;
  
  const parts = exercise.text_with_blanks.split("___");
  const numBlanks = parts.length - 1;
  const [answers, setAnswers] = useState<string[]>(Array(numBlanks).fill(""));
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);

  const checkAnswer = () => {
    if (isCorrect) return; // Ya resuelto
    
    // Asumimos que correct_answer puede ser una cadena de palabras separadas por comas, 
    // o simplemente validamos si escriben algo con sentido si no hay respuesta estricta.
    const expected = exercise.correct_answer?.trim().toLowerCase() || "";
    const current = answers.join(", ").trim().toLowerCase();
    
    // Lógica simple: Si no hay correct_answer, validamos que hayan llenado todo
    // Si hay, comprobamos si contiene las palabras esperadas
    const allFilled = answers.every(a => a.trim().length > 0);
    
    if (allFilled && (!expected || expected.includes(answers[0].trim().toLowerCase()))) {
      setIsCorrect(true);
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#f59e0b', '#10b981', '#3b82f6', '#a855f7']
      });
      toast.success("¡Muy bien! Oración completada 🌟", { position: "top-center" });
    } else {
      setIsCorrect(false);
      toast.error("Hay algo que revisar 🤔", { position: "top-center" });
    }
  };

  return (
    <div className="flex flex-col gap-6 mt-4">
      <div className="text-left text-2xl leading-relaxed text-slate-800 font-medium">
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {i < parts.length - 1 && (
              <input 
                type="text" 
                value={answers[i]}
                onChange={(e) => {
                  const newAns = [...answers];
                  newAns[i] = e.target.value;
                  setAnswers(newAns);
                  setIsCorrect(null);
                }}
                disabled={isCorrect === true}
                className={`inline-block mx-2 w-32 h-12 align-middle text-center rounded border-b-4 border-slate-300 bg-slate-50 focus:outline-none focus:border-blue-500 font-bold transition ${isCorrect === true ? 'border-green-500 text-green-700 bg-green-50' : ''} ${isCorrect === false ? 'border-red-500 text-red-700 bg-red-50' : ''}`} 
              />
            )}
          </span>
        ))}
      </div>
      
      {!isCorrect && (
        <Button 
          onClick={checkAnswer} 
          className="mt-4 self-center rounded-full bg-blue-600 hover:bg-blue-700 text-white font-bold px-8 py-6 text-lg shadow-md"
        >
          Comprobar
        </Button>
      )}
    </div>
  );
}
