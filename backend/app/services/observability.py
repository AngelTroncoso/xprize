import time
import functools
from typing import Dict, Any, Optional
from app.models.database import db

class Tracer:
    @staticmethod
    def log_span(
        session_id: str,
        span_name: str,
        span_kind: str,
        input_data: Any,
        output_data: Any,
        latency_ms: int,
        token_prompt: Optional[int] = 0,
        token_completion: Optional[int] = 0,
        model_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Registra una traza de ejecución en la base de datos de Supabase.
        Sigue la semántica y estructura estandarizada de AgentOps (OpenInference).
        """
        supabase_client = db.get_client()
        if not supabase_client:
            print(f"[AgentOps Trace - {span_kind}] {span_name} - Latency: {latency_ms}ms - Model: {model_name}")
            return None

        try:
            # En producción, serializamos datos complejos a JSON
            import json
            def serialize(val):
                try:
                    return json.loads(json.dumps(val))
                except:
                    return {"raw": str(val)}

            trace_payload = {
                "session_id": session_id,
                "span_name": span_name,
                "span_kind": span_kind,
                "input_data": serialize(input_data),
                "output_data": serialize(output_data),
                "latency_ms": latency_ms,
                "token_prompt": token_prompt,
                "token_completion": token_completion,
                "model_name": model_name
            }

            response = supabase_client.table("agent_traces").insert(trace_payload).execute()
            if response.data:
                trace_id = response.data[0]["id"]
                # Lanzar evaluación de Juez asíncrona de manera opcional
                return trace_id
            return None
        except Exception as e:
            print(f"Error al escribir traza en la base de datos: {e}")
            return None

def trace_agent_step(span_name: str, span_kind: str):
    """
    Decorador para interceptar y registrar automáticamente llamadas de agentes y herramientas.
    Requiere que el primer argumento de la función o los kwargs contengan 'session_id'.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Buscar session_id en los argumentos
            session_id = kwargs.get("session_id") or "00000000-0000-0000-0000-000000000000"
            
            input_info = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}
            
            exception_raised = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                exception_raised = e
                result = {"error": str(e)}
                raise e
            finally:
                end_time = time.time()
                latency = int((end_time - start_time) * 1000)
                
                # Intentar extraer info de tokens o modelo de los metadatos de retorno si aplica
                token_prompt = 0
                token_completion = 0
                model_used = None
                
                if isinstance(result, dict):
                    token_prompt = result.get("token_prompt", 0)
                    token_completion = result.get("token_completion", 0)
                    model_used = result.get("model_name")
                
                Tracer.log_span(
                    session_id=session_id,
                    span_name=span_name,
                    span_kind=span_kind,
                    input_data=input_info,
                    output_data=result,
                    latency_ms=latency,
                    token_prompt=token_prompt,
                    token_completion=token_completion,
                    model_name=model_used
                )
                
        return wrapper
    return decorator
