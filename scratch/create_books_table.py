import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Credenciales de Supabase no encontradas.")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL statements para crear la tabla textbooks
# Usualmente esto se hace en la interfaz de Supabase o migraciones, pero usaremos RPC si existe,
# o simplemente insertaremos usando REST (Supabase creará la tabla si la configuramos previamente,
# pero REST no puede crear tablas).
# Como estamos usando la API REST de supabase-py, debemos ejecutar SQL directo o usar la UI.
# Afortunadamente podemos usar el Supabase CLI o un endpoint RPC si hay uno creado.

print("ATENCIÓN: Debes crear la tabla en Supabase manualmente si no tienes un RPC para ejecutar SQL.")
print("Estructura requerida:")
print("CREATE TABLE public.textbooks (")
print("  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),")
print("  curso TEXT NOT NULL,")
print("  asignatura TEXT NOT NULL,")
print("  titulo TEXT NOT NULL,")
print("  portada_url TEXT,")
print("  pdf_url TEXT,")
print("  gemini_file_id TEXT")
print(");")
