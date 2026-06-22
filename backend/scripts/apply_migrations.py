import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = BACKEND_DIR.parent / "supabase" / "migrations"
MIGRATION_FILES = [
    "003_curriculum_catalog.sql",
    "004_add_clave_compuesta.sql",
]


def get_mgmt_config():
    load_dotenv(BACKEND_DIR / ".env")
    url = os.getenv("SUPABASE_URL", "")
    secret_key = os.getenv("SUPABASE_SECRET_KEY", "")
    if not url or not secret_key:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_SECRET_KEY en xprize/backend/.env"
        )
    # Extract project ref from URL: https://<ref>.supabase.co
    project_ref = url.replace("https://", "").replace("http://", "").split(".")[0]
    api_url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    return api_url, secret_key


def run_migration(api_url: str, secret_key: str, file_path: Path) -> bool:
    print(f"\n📄 Ejecutando migración: {file_path.name}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }
        # Managment API expects JSON with "query" field
        payload = {"query": sql_content}
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            print(f"✅ Migración {file_path.name} aplicada exitosamente")
            return True
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Error al ejecutar {file_path.name}: {str(e)}")
        return False


def main():
    print("🚀 Iniciando aplicación de migraciones de Supabase (Management API)...")
    try:
        api_url, secret_key = get_mgmt_config()
    except RuntimeError as e:
        print(f"❌ Error de configuración: {e}")
        sys.exit(1)

    all_success = True
    for migration_file in MIGRATION_FILES:
        migration_path = MIGRATIONS_DIR / migration_file
        if not migration_path.exists():
            print(f"❌ Archivo de migración no encontrado: {migration_path}")
            all_success = False
            continue
        success = run_migration(api_url, secret_key, migration_path)
        if not success:
            all_success = False

    if all_success:
        print("\n✅ Todas las migraciones aplicadas correctamente")
        sys.exit(0)
    else:
        print("\n❌ Algunas migraciones fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
