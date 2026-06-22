import ast
import sys
import types
from typing import Callable, Dict

import math
import datetime
import json
import re
import random
import string
import collections
import itertools
import functools
import typing

from app.models.database import db


# ---------------------------------------------------------------------------
# Políticas de seguridad
# ---------------------------------------------------------------------------

ALLOWED_MODULES: set[str] = {
    "math",
    "datetime",
    "json",
    "re",
    "random",
    "string",
    "collections",
    "itertools",
    "functools",
    "typing",
}

# Sub-attributes permitidos para módulos restringidos
ALLOWED_MODULE_ATTRS: dict[str, set[str]] = {
    "collections": {"Counter", "defaultdict", "deque", "namedtuple", "OrderedDict"},
    "datetime": {"date", "datetime", "time", "timedelta", "timezone", "UTC"},
    "typing": {
        "List", "Dict", "Set", "Tuple", "Optional", "Union", "Any",
        "Callable", "Iterable", "Iterator", "Sequence", "Mapping",
    },
}

# Builtins seguros expuestos al código dinámico
SAFE_BUILTINS: dict[str, object] = {
    "abs": abs,
    "all": all,
    "any": any,
    "ascii": ascii,
    "bin": bin,
    "bool": bool,
    "bytes": bytes,
    "chr": chr,
    "complex": complex,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "hex": hex,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "print": print,
    "range": range,
    "repr": repr,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}

# Atributos dunder explícitamente prohibidos (sólo se permite __name__ y __doc__)
BLOCKED_DUNDERS: set[str] = {
    "__import__",
    "__class__",
    "__bases__",
    "__subclasses__",
    "__mro__",
    "__globals__",
    "__code__",
    "__closure__",
    "__func__",
    "__self__",
    "__module__",
    "__dict__",
    "__weakref__",
    "__init__",
    "__new__",
    "__call__",
    "__repr__",
    "__str__",
    "__hash__",
    "__eq__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "__ne__",
    "__get__",
    "__set__",
    "__delete__",
    "__set_name__",
    "__instancecheck__",
    "__subclasscheck__",
    "__del__",
    "__delattr__",
    "__getattr__",
    "__getattribute__",
    "__setattr__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__iter__",
    "__next__",
    "__enter__",
    "__exit__",
    "__aenter__",
    "__aexit__",
    "__await__",
    "__aiter__",
    "__anext__",
    "__len__",
    "__length_hint__",
    "__contains__",
    "__add__",
    "__sub__",
    "__mul__",
    "__truediv__",
    "__floordiv__",
    "__mod__",
    "__pow__",
    "__and__",
    "__or__",
    "__xor__",
    "__lshift__",
    "__rshift__",
    "__iadd__",
    "__isub__",
    "__imul__",
    "__itruediv__",
    "__ifloordiv__",
    "__imod__",
    "__ipow__",
    "__iand__",
    "__ior__",
    "__ixor__",
    "__ilshift__",
    "__irshift__",
    "__neg__",
    "__pos__",
    "__abs__",
    "__invert__",
    "__complex__",
    "__int__",
    "__float__",
    "__round__",
    "__index__",
    "__trunc__",
    "__floor__",
    "__ceil__",
    "__sizeof__",
    "__reduce__",
    "__reduce_ex__",
    "__getstate__",
    "__setstate__",
    "__getnewargs__",
    "__getnewargs_ex__",
    "__init_subclass__",
    "__slots__",
    "__prepare__",
    "__build_class__",
    "__loader__",
    "__spec__",
    "__cached__",
    "__file__",
    "__path__",
    "__package__",
}


class SandboxSecurityError(Exception):
    """Error de seguridad al validar código dinámico."""


class ASTSecurityValidator(ast.NodeVisitor):
    """
    Validador AST que aplica políticas de seguridad estrictas:
    - Bloquea importaciones fuera de la whitelist.
    - Bloquea acceso a atributos dunder peligrosos.
    - Bloquea definiciones de clases, lambdas y walrus operators.
    - Limita constructs complejos que pueden ocultar ejecución peligrosa.
    """

    def __init__(self) -> None:
        self._allowed_imports = set(ALLOWED_MODULES)

    # ------------------------------------------------------------------
    # Declaraciones prohibidas
    # ------------------------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        raise SandboxSecurityError(
            f"Definición de clases no permitida en herramientas dinámicas: '{node.name}'"
        )

    def visit_Lambda(self, node: ast.Lambda) -> None:
        raise SandboxSecurityError(
            "Expresiones lambda no permitidas en sandbox de herramientas dinámicas"
        )

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        raise SandboxSecurityError(
            "Asignación con walrus operator (:=) no permitida en sandbox"
        )

    def visit_Global(self, node: ast.Global) -> None:
        raise SandboxSecurityError("Declaración 'global' no permitida en sandbox")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        raise SandboxSecurityError("Declaración 'nonlocal' no permitida en sandbox")

    # ------------------------------------------------------------------
    # Validación de importaciones
    # ------------------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module not in self._allowed_imports:
                raise SandboxSecurityError(
                    f"Importación del módulo '{alias.name}' no está en la whitelist"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module not in self._allowed_imports:
                raise SandboxSecurityError(
                    f"Importación desde el módulo '{node.module}' no está en la whitelist"
                )
            # Validar atributos específicos para módulos restringidos
            if base_module in ALLOWED_MODULE_ATTRS and node.names:
                allowed_attrs = ALLOWED_MODULE_ATTRS[base_module]
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    if alias.name not in allowed_attrs:
                        raise SandboxSecurityError(
                            f"Importación de '{alias.name}' desde '{node.module}' no permitida"
                        )
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Validación de acceso a atributos
    # ------------------------------------------------------------------

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if (
            isinstance(node.attr, str)
            and node.attr.startswith("__")
            and node.attr not in ("__name__", "__doc__")
        ):
            raise SandboxSecurityError(
                f"Acceso a atributo dunder prohibido: '{node.attr}'"
            )
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Validación de llamadas a funciones
    # ------------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        # Bloquear llamadas directas a atributos dunder (p.ej., cls.__init__())
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name.startswith("__") and attr_name not in ("__name__", "__doc__"):
                raise SandboxSecurityError(
                    f"Llamada a método dunder prohibido: '{attr_name}'"
                )
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Permitir declaraciones y expresiones funcionales seguras por defecto
    # ------------------------------------------------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Return(self, node: ast.Return) -> None:
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.generic_visit(node)

    def visit_Pass(self, node: ast.Pass) -> None:
        self.generic_visit(node)

    def visit_Break(self, node: ast.Break) -> None:
        self.generic_visit(node)

    def visit_Continue(self, node: ast.Continue) -> None:
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred) -> None:
        self.generic_visit(node)

    def visit_List(self, node: ast.List) -> None:
        self.generic_visit(node)

    def visit_Tuple(self, node: ast.Tuple) -> None:
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set) -> None:
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.generic_visit(node)

    def visit_FormattedValue(self, node: ast.FormattedValue) -> None:
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> None:
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.generic_visit(node)


class DynamicLoader:
    _loaded_tools: Dict[str, Callable] = {}

    @classmethod
    def _validate_and_compile(cls, code_str: str, filename: str) -> ast.AST:
        """
        Parsea el código fuente a AST, ejecuta el validador de seguridad
        y devuelve el AST compilable.
        """
        try:
            tree = ast.parse(code_str, filename=filename, mode="exec")
        except SyntaxError as exc:
            raise SandboxSecurityError(f"Código con error de sintaxis: {exc}")

        validator = ASTSecurityValidator()
        validator.visit(tree)
        ast.fix_missing_locations(tree)
        return compile(tree, filename=filename, mode="exec")

    @classmethod
    def _get_safe_globals(cls, module_name: str) -> dict:
        """
        Construye el entorno de ejecución restringido:
        - __builtins__ limitado a funciones seguras.
        - Módulos permitidos expuestos directamente.
        - Atributos de módulos restringidos filtrados.
        """
        safe_globals: dict = {
            "__builtins__": SAFE_BUILTINS,
            "__name__": module_name,
            "__doc__": None,
        }

        # Cargar módulos permitidos, aplicando restricciones de atributos
        raw_modules = {
            "math": math,
            "datetime": datetime,
            "json": json,
            "re": re,
            "random": random,
            "string": string,
            "collections": collections,
            "itertools": itertools,
            "functools": functools,
            "typing": typing,
        }

        for mod_name, mod in raw_modules.items():
            if mod_name in ALLOWED_MODULE_ATTRS:
                # Módulo restringido: exponer solo atributos permitidos
                restricted = types.ModuleType(mod_name)
                restricted.__doc__ = mod.__doc__
                for attr in ALLOWED_MODULE_ATTRS[mod_name]:
                    if hasattr(mod, attr):
                        setattr(restricted, attr, getattr(mod, attr))
                safe_globals[mod_name] = restricted
            else:
                # Módulo completo permitido
                safe_globals[mod_name] = mod

        return safe_globals

    @classmethod
    def load_tool_from_code(cls, code_str: str, tool_name: str) -> Callable:
        """
        Compila y carga en caliente una función de Python dentro de un módulo dinámico aislado.
        Utiliza un sandbox basado en AST (Abstract Syntax Tree) para validar la seguridad del
        código antes de ejecutarlo, aplicando whitelist de módulos, bloqueo de dunders peligrosos
        y un entorno de ejecución restringido.
        """
        module_name = f"app.dynamic_tools.{tool_name}"

        # Crear un nuevo objeto de módulo aislado
        module = types.ModuleType(module_name)
        module.__file__ = f"<dynamic_tool:{tool_name}>"

        # 1. Validar AST y compilar en sandbox (lanza SandboxSecurityError)
        compiled_code = cls._validate_and_compile(code_str, module.__file__)

        # 2. Preparar entorno restringido
        safe_globals = cls._get_safe_globals(module_name)

        # 3. Ejecutar código en el contexto del módulo aislado con entorno restringido
        exec(compiled_code, safe_globals)

        # 4. Sincronizar con el objeto de módulo para mantener consistencia
        module.__dict__.update(safe_globals)

        # 5. Registrar en sys.modules para que se comporte como librería importable
        sys.modules[module_name] = module

        # 6. Buscar la función principal del tool
        if hasattr(module, tool_name):
            tool_callable = getattr(module, tool_name)
        elif hasattr(module, "main"):
            tool_callable = getattr(module, "main")
        else:
            # Si no hay función con el nombre de la herramienta ni main,
            # tomar el primer callable definido en el módulo
            callables = [
                v for k, v in module.__dict__.items()
                if callable(v) and not k.startswith("_")
            ]
            if callables:
                tool_callable = callables[0]
            else:
                raise AttributeError(
                    f"No entry point function found in dynamic tool '{tool_name}'"
                )

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