"""
Script para verificar la conexión a PostgreSQL y que pgvector esté habilitado.

Este script verifica:
1. Conexión exitosa a la base de datos
2. PostgreSQL responde correctamente
3. La extensión 'vector' está instalada y habilitada
"""

import os
import sys
from pathlib import Path

from colorama import Fore, init
from dotenv import load_dotenv

try:
    import psycopg2
except ImportError:
    print(f"{Fore.RED}Error: psycopg2 no está instalado.{Fore.RESET}")
    print("Instala las dependencias con: pip install -r requirements.txt")
    sys.exit(1)

init(autoreset=True)

# Cargar variables de entorno
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "parachute_rag")
DB_USER = os.getenv("DB_USER", "parachute_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def check_connection():
    """Verifica la conexión a PostgreSQL."""
    print(f"\n{Fore.CYAN}=== VERIFICACIÓN DE CONEXIÓN A POSTGRESQL ==={Fore.RESET}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"Base de datos: {DB_NAME}")
    print(f"Usuario: {DB_USER}\n")

    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        print(f"{Fore.GREEN}✓ Conexión exitosa a PostgreSQL{Fore.RESET}")

        cursor = connection.cursor()

        # Verificar que PostgreSQL responde
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"{Fore.GREEN}✓ PostgreSQL responde:{Fore.RESET}")
        print(f"  {version}\n")

        # Verificar que pgvector está habilitado
        cursor.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'vector';"
        )
        result = cursor.fetchone()

        if result:
            print(f"{Fore.GREEN}✓ Extensión 'vector' (pgvector) está habilitada{Fore.RESET}\n")
        else:
            print(f"{Fore.YELLOW}⚠ Extensión 'vector' no está disponible{Fore.RESET}")
            print("  Intenta crear la extensión con:")
            print("  CREATE EXTENSION IF NOT EXISTS vector;\n")

        # Verificar tablas creadas
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
        )
        tables = cursor.fetchall()
        print(f"{Fore.CYAN}Tablas en la base de datos:{Fore.RESET}")
        if tables:
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  (Sin tablas aún)")

        print(f"\n{Fore.GREEN}=== VERIFICACIÓN COMPLETADA CON ÉXITO ==={Fore.RESET}\n")

        cursor.close()
        connection.close()

    except psycopg2.OperationalError as error:
        print(f"{Fore.RED}✗ Error de conexión:{Fore.RESET}")
        print(f"  {error}\n")
        print("Asegúrate de que:")
        print("  1. Docker Desktop está ejecutándose")
        print("  2. El contenedor PostgreSQL está activo")
        print("  3. Las credenciales en .env son correctas\n")
        return False

    except Exception as error:
        print(f"{Fore.RED}✗ Error inesperado:{Fore.RESET}")
        print(f"  {error}\n")
        return False

    return True


if __name__ == "__main__":
    success = check_connection()
    sys.exit(0 if success else 1)
