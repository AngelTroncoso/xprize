import sys
import os
import tempfile
import subprocess
from typing import Dict, Any

class SandboxRunner:
    def __init__(self, timeout_seconds: float = 5.0, memory_limit_mb: int = 128):
        self.timeout = timeout_seconds
        self.memory_limit = memory_limit_mb

    def run_code(self, code_str: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta un script de Python de forma aislada utilizando un subproceso.
        Retorna un diccionario con la salida estándar, errores y si fue exitoso.
        """
        # Preparar datos de entrada pasados al script
        input_init = f"INPUT_DATA = {repr(input_data or {})}\n"
        
        # Envolver el código en una estructura ejecutable básica
        full_code = f"""
import sys
import json

{input_init}

# Restringir ciertas operaciones peligrosas a nivel de ejecución básica
# (Nota: En producción se recomienda un sandbox como gVisor o E2B)
sys.modules['os'] = None
sys.modules['shutil'] = None

try:
{self._indent_code(code_str)}
    # Capturar variables globales resultantes de la ejecución
    # Si definen una función 'main' la ejecutamos con INPUT_DATA
    if 'main' in globals() and callable(globals()['main']):
        result = globals()['main'](INPUT_DATA)
        print("SANDBOX_RESULT:" + json.dumps({"status": "success", "result": result}))
    else:
        print("SANDBOX_RESULT:" + json.dumps({"status": "success", "result": "Code ran successfully without 'main'"}))
except Exception as e:
    print("SANDBOX_RESULT:" + json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
    sys.exit(1)
"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as temp_file:
            temp_file.write(full_code)
            temp_path = temp_file.name

        try:
            # Ejecutar con el mismo intérprete de Python en un subproceso
            process = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            stdout = process.stdout
            stderr = process.stderr
            
            # Buscar resultado estructurado del sandbox
            result_data = None
            for line in stdout.splitlines():
                if line.startswith("SANDBOX_RESULT:"):
                    result_data = json_load_safe(line[len("SANDBOX_RESULT:"):])
                    break
            
            if not result_data:
                # Si ocurrió un error fatal de sintaxis o ejecución externa
                return {
                    "success": False,
                    "stdout": stdout,
                    "stderr": stderr or "Execution failed to return structured results.",
                    "error": "Sintaxis o error estructural antes de la ejecución del código principal."
                }
            
            if result_data.get("status") == "error":
                return {
                    "success": False,
                    "stdout": stdout,
                    "stderr": stderr,
                    "error": result_data.get("error")
                }
                
            return {
                "success": True,
                "stdout": stdout,
                "stderr": stderr,
                "result": result_data.get("result")
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds.",
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "error": f"Fallo al iniciar el Sandbox: {str(e)}"
            }
        finally:
            # Asegurar la limpieza del archivo temporal
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _indent_code(self, code: str) -> str:
        """Indenta el código recibido para meterlo dentro del bloque try-except."""
        lines = code.splitlines()
        indented_lines = ["    " + line for line in lines]
        return "\n".join(indented_lines)

def json_load_safe(data: str):
    import json
    try:
        return json.loads(data)
    except:
        return None
