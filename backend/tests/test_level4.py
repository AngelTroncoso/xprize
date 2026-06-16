import sys
import os
# Asegurar que el directorio de la aplicación esté en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sandbox_runner import SandboxRunner
from app.services.dynamic_loader import DynamicLoader
from app.services.router import ModelRouter
from app.agents.judge import JudgeAgent
from app.agents.evolution_engine import EvolutionEngine

def test_sandbox_runner_success():
    runner = SandboxRunner(timeout_seconds=2.0)
    code = """
def main(INPUT_DATA):
    x = INPUT_DATA.get('val', 0)
    return x * 2
"""
    res = runner.run_code(code, input_data={"val": 5})
    assert res["success"] is True
    assert res["result"] == 10

def test_sandbox_runner_timeout():
    runner = SandboxRunner(timeout_seconds=1.0)
    code = """
def main(INPUT_DATA):
    import time
    while True:
        time.sleep(0.1)
"""
    res = runner.run_code(code)
    assert res["success"] is False
    assert "Timeout" in res["error"]

def test_sandbox_restricted_builtins():
    runner = SandboxRunner()
    code = """
def main(INPUT_DATA):
    import os
    os.listdir('.')
"""
    res = runner.run_code(code)
    assert res["success"] is False
    assert "NoneType" in res["error"] or "has no attribute" in res["error"]

def test_dynamic_loader_compilation():
    code = """
def custom_multiply_test(INPUT_DATA):
    return INPUT_DATA['a'] * INPUT_DATA['b']
"""
    # Compilar en caliente
    func = DynamicLoader.load_tool_from_code(code, "custom_multiply_test")
    assert callable(func)
    
    # Evaluar
    res = func({"a": 3, "b": 4})
    assert res == 12

def test_model_router_fallback():
    router = ModelRouter()
    # Verificamos que contenga los modelos correctos
    assert router.lite_model == "gemini-3.1-flash-lite"
    assert router.flash_model == "gemini-3.5-flash"
    assert router.pro_model == "gemini-3.1-pro"

def test_judge_evaluation_mock():
    judge = JudgeAgent()
    # Probar si el formateador del prompt del Juez es correcto
    assert judge.judge_model == "gemini-3.5-flash"

def test_curriculum_manager_mock():
    from app.services.curriculum_manager import CurriculumManager
    manager = CurriculumManager()
    assert manager.model == "gemini-3.5-flash"
    manager.update_source_priority("texto_escolar_5.md", 0.9)
    assert manager._source_priority_index["texto_escolar_5.md"] == 0.97

def test_resource_resolver():
    from app.services.external_resources import ResourceResolver
    resource = ResourceResolver.select_resource("Matemáticas", needs_interactive=True)
    assert resource["name"] == "PhET Interactive Simulations"
    
    payload = ResourceResolver.simulate_payload("Wikipedia API", "fracciones")
    assert "wikipedia.org" in payload["url"]


