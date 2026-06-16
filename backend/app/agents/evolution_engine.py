import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from app.services.sandbox_runner import SandboxRunner
from app.models.database import db

# Schemas para salidas estructuradas del bucle auto-evolutivo
class ToolGenerationDraft(BaseModel):
    tool_name: str = Field(..., description="Nombre único de la función en snake_case (ej. validate_regex)")
    description: str = Field(..., description="Descripción detallada de qué hace y qué parámetros recibe")
    code: str = Field(..., description="Código limpio de la función Python. Debe incluir tipado y docstring.")
    test_code: str = Field(..., description="Código de prueba unitario. Debe incluir aserciones (assert) y probar casos límite.")

class EvolutionEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "dummy-key")
        self.client = genai.Client(api_key=api_key)
        self.generator_model = "gemini-3.1-pro" # Modelo avanzado para codificación
        self.sandbox = SandboxRunner(timeout_seconds=5.0)

    def evolve_new_capability(self, gap_description: str) -> Dict[str, Any]:
        """
        Inicia el proceso de evolución para crear una nueva herramienta técnica basada en un gap identificado.
        Ejecuta el ciclo de generación, pruebas en sandbox y auto-corrección (self-healing).
        """
        # Sistema de Prompting
        prompt = f"""
        Actúa como el Agente Ingeniero de Sistemas en el bucle de auto-evolución (Nivel 4) de Super_Profesor.
        Hemos detectado un vacío de capacidades o una falla recurrente de validación descrita como:
        "{gap_description}"
        
        Tu tarea es diseñar y codificar una nueva herramienta en Python que resuelva esta carencia.
        Adicionalmente debes proveer un código de pruebas estructurado para testear la solución.
        
        Reglas de código:
        - La función principal debe llamarse igual que 'tool_name' o 'main'.
        - Debe recibir un diccionario 'INPUT_DATA' y retornar un resultado serializable a JSON.
        - El código de pruebas debe poder ejecutarse solo y levantar AssertionError si algo falla.
        """

        max_attempts = 3
        current_attempt = 1
        last_error = ""
        draft = None

        while current_attempt <= max_attempts:
            try:
                # Si es un reintento, retroalimentamos el error
                execution_context_prompt = prompt
                if last_error:
                    execution_context_prompt += f"\n\n[REINTENTO {current_attempt}] El código anterior falló en el Sandbox con el siguiente error. Por favor corrígelo:\n{last_error}"

                # 1. Llamar a Gemini con Structured Outputs
                response = self.client.models.generate_content(
                    model=self.generator_model,
                    contents=execution_context_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ToolGenerationDraft,
                        temperature=0.3
                    )
                )
                draft: ToolGenerationDraft = response.parsed

                # 2. Unir el código principal y los tests para probarlos en el Sandbox
                full_test_script = f"""
{draft.code}

# --- Suite de Tests Unitarios ---
try:
{self._indent_code(draft.test_code)}
    print("ALL TESTS PASSED")
except AssertionError as ae:
    raise AssertionError("Test falló: " + str(ae))
"""

                # 3. Correr en el sandbox
                sandbox_result = self.sandbox.run_code(full_test_script)

                if sandbox_result["success"] and "ALL TESTS PASSED" in sandbox_result["stdout"]:
                    # Evolución exitosa: registrar propuesta de herramienta en la cola HITL
                    self._register_for_approval(draft)
                    return {
                        "status": "success",
                        "attempts": current_attempt,
                        "tool_name": draft.tool_name,
                        "description": draft.description,
                        "code": draft.code,
                        "message": "Herramienta auto-generada y validada en sandbox con éxito. Esperando aprobación HITL."
                    }
                else:
                    # El test falló o hubo un error de ejecución
                    last_error = sandbox_result.get("error") or sandbox_result.get("stderr") or "Prueba fallida de aserciones."
                    current_attempt += 1

            except Exception as e:
                last_error = str(e)
                current_attempt += 1

        return {
            "status": "failed",
            "attempts": max_attempts,
            "last_error": last_error,
            "message": f"No se pudo autogenerar una herramienta libre de errores tras {max_attempts} intentos."
        }

    def _register_for_approval(self, draft: ToolGenerationDraft):
        """Guarda la herramienta generada en la cola de aprobación de Supabase."""
        supabase_client = db.get_client()
        if not supabase_client:
            print(f"[HITL GATE] Supabase no configurado. Ignorando guardado físico de la herramienta: {draft.tool_name}")
            return

        try:
            supabase_client.table("tool_approvals").insert({
                "tool_name": draft.tool_name,
                "description": draft.description,
                "code": draft.code,
                "status": "pending"
            }).execute()
        except Exception as e:
            print(f"Error al registrar la herramienta en la cola de aprobación: {e}")

    def _indent_code(self, code: str) -> str:
        lines = code.splitlines()
        return "\n".join(["    " + line for line in lines])
