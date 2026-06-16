import sys
import types
from typing import Callable, Dict
from app.models.database import db

class DynamicLoader:
    _loaded_tools: Dict[str, Callable] = {}

    @classmethod
    def load_tool_from_code(cls, code_str: str, tool_name: str) -> Callable:
        """
        Compila y carga en caliente una función de Python dentro de un módulo dinámico aislado.
        """
        module_name = f"app.dynamic_tools.{tool_name}"
        
        # Crear un nuevo objeto de módulo aislado
        module = types.ModuleType(module_name)
        module.__file__ = f"<dynamic_tool:{tool_name}>"
        
        # Compilar código
        compiled_code = compile(code_str, filename=module.__file__, mode="exec")
        
        # Ejecutar en el contexto de diccionario del módulo
        exec(compiled_code, module.__dict__)
        
        # Registrar en sys.modules para que se comporte como librería importable
        sys.modules[module_name] = module
        
        # Buscar la función principal del tool (que debe llamarse igual que el tool o contener 'main')
        if hasattr(module, tool_name):
            tool_callable = getattr(module, tool_name)
        elif hasattr(module, "main"):
            tool_callable = getattr(module, "main")
        else:
            # Si no hay función con el nombre de la herramienta ni main, tomar el primer callable
            callables = [v for k, v in module.__dict__.items() if callable(v) and not k.startswith("_")]
            if callables:
                tool_callable = callables[0]
            else:
                raise AttributeError(f"No entry point function found in dynamic tool '{tool_name}'")

        cls._loaded_tools[tool_name] = tool_callable
        return tool_callable

    @classmethod
    def get_tool(cls, tool_name: str) -> Callable:
        """Obtiene un tool dinámico cargado en memoria."""
        return cls._loaded_tools.get(tool_name)

    @classmethod
    def load_all_active_tools(cls) -> int:
        """
        Carga todas las herramientas aprobadas desde la base de datos Supabase en caliente.
        Retorna la cantidad de herramientas cargadas.
        """
        supabase_client = db.get_client()
        if not supabase_client:
            print("Supabase no configurado, omitiendo carga de herramientas desde DB.")
            return 0

        try:
            # Traer herramientas aprobadas de tool_approvals o de la tabla dynamic_tools
            response = supabase_client.table("dynamic_tools").select("*").execute()
            tools_list = response.data or []
            
            count = 0
            for tool in tools_list:
                try:
                    cls.load_tool_from_code(tool["code"], tool["name"])
                    count += 1
                except Exception as e:
                    print(f"Error al cargar herramienta dinámica '{tool['name']}': {e}")
            
            return count
        except Exception as e:
            print(f"Fallo al sincronizar herramientas dinámicas de la base de datos: {e}")
            return 0
