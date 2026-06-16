import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Any

load_dotenv()

class ModelRouter:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "dummy-key")
        self.client = genai.Client(api_key=api_key)
        
        # Modelos vigentes en 2026
        self.lite_model = "gemini-3.1-flash-lite"
        self.flash_model = "gemini-3.5-flash"
        self.pro_model = "gemini-3.1-pro"

    def execute_with_fallback(self, prompt: str, task_complexity: str = "medium", config: types.GenerateContentConfig = None) -> Any:
        """
        Ejecuta la llamada de Gemini con un enrutamiento inteligente basado en complejidad,
        e implementa un fallback resiliente si el modelo principal falla.
        """
        # Determinar modelo principal
        if task_complexity == "low":
            primary_model = self.lite_model
            fallback_models = [self.flash_model]
        elif task_complexity == "high":
            primary_model = self.pro_model
            fallback_models = [self.flash_model, self.lite_model]
        else: # medium
            primary_model = self.flash_model
            fallback_models = [self.pro_model, self.lite_model]

        models_to_try = [primary_model] + fallback_models
        last_exception = None

        for model in models_to_try:
            for retry in range(2): # 2 intentos por modelo
                try:
                    # Configuración por defecto si no se pasa una
                    cfg = config or types.GenerateContentConfig(temperature=0.4)
                    
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=cfg
                    )
                    return response
                except Exception as e:
                    last_exception = e
                    # Espera con retroceso exponencial simple antes de reintentar
                    time.sleep(1.0 * (retry + 1))
            
            # Si falló después de reintentos, el bucle pasa al siguiente modelo en la lista de fallback

        raise RuntimeError(f"Todos los modelos de Gemini fallaron en el ruteo. Último error: {last_exception}")
