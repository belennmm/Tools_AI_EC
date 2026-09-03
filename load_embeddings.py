"""
Script para cargar FAQs del corpus en PostgreSQL + pgvector.

Este script:
1. Lee el corpus de FAQs
2. Extrae cada FAQ correctamente
3. Genera embeddings con sentence-transformers (all-MiniLM-L6-v2)
4. Conecta a PostgreSQL
5. Inserta los embeddings en la tabla 'faqs'
6. Evita duplicados usando UPSERT
"""

import json
import os
import sys
from pathlib import Path

import psycopg2
from colorama import Fore, init
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

init(autoreset=True)

# Cargar variables de entorno
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "parachute_rag")
DB_USER = os.getenv("DB_USER", "parachute_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CORPUS_FILE = Path(__file__).parent / "Corpus_FAQs_Parachute_SA_2026.txt"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


def validate_files():
    """Valida que el archivo del corpus existe."""
    if not CORPUS_FILE.exists():
        print(f"{Fore.RED}Error: no se encontró {CORPUS_FILE.name}.{Fore.RESET}")
        sys.exit(1)
    print(f"{Fore.GREEN}✓ Corpus encontrado: {CORPUS_FILE.name}{Fore.RESET}\n")


def parse_corpus():
    """
    Lee y parsea el corpus de FAQs.
    Retorna una lista de diccionarios con los datos de cada FAQ.
    """
    print(f"{Fore.CYAN}Leyendo corpus...{Fore.RESET}")
    
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    faqs = []
    # Separador de bloques
    blocks = content.split("------------------------------------------------------------")
    
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("BASE DE DATOS"):
            continue
        
        faq_data = {}
        
        # Extraer ID
        id_line = [line for line in block.split("\n") if line.startswith("ID:")]
        if id_line:
            faq_data["faq_id"] = id_line[0].replace("ID:", "").strip()
        
        # Extraer CATEGORÍA
        cat_line = [line for line in block.split("\n") if line.startswith("CATEGORÍA:")]
        if cat_line:
            faq_data["categoria"] = cat_line[0].replace("CATEGORÍA:", "").strip()
        
        # Extraer PREGUNTA
        preg_line = [line for line in block.split("\n") if line.startswith("PREGUNTA:")]
        if preg_line:
            faq_data["pregunta"] = preg_line[0].replace("PREGUNTA:", "").strip()
        
        # Extraer RESPUESTA (múltiples líneas)
        resp_start = False
        respuesta_lines = []
        for line in block.split("\n"):
            if line.startswith("RESPUESTA:"):
                resp_start = True
                respuesta_lines.append(line.replace("RESPUESTA:", "").strip())
            elif resp_start and line.startswith("METADATA:"):
                break
            elif resp_start:
                respuesta_lines.append(line.strip())
        
        if respuesta_lines:
            faq_data["respuesta"] = " ".join(respuesta_lines).strip()
        
        # Validar que el FAQ tiene los campos necesarios
        if all(key in faq_data for key in ["faq_id", "categoria", "pregunta", "respuesta"]):
            faqs.append(faq_data)
    
    print(f"{Fore.GREEN}✓ Total de FAQs detectadas: {len(faqs)}{Fore.RESET}\n")
    return faqs


def load_model():
    """Carga el modelo de embeddings."""
    print(f"{Fore.CYAN}Cargando modelo: {MODEL_NAME}...{Fore.RESET}")
    try:
        model = SentenceTransformer(MODEL_NAME)
        print(f"{Fore.GREEN}✓ Modelo cargado correctamente{Fore.RESET}")
        print(f"{Fore.GREEN}✓ Dimensión de embeddings: {EMBEDDING_DIMENSION}{Fore.RESET}\n")
        return model
    except Exception as e:
        print(f"{Fore.RED}Error al cargar el modelo: {e}{Fore.RESET}")
        sys.exit(1)


def generate_embedding_text(faq):
    """Genera el texto combinado para embeddings."""
    return f"Categoría: {faq['categoria']}. Pregunta: {faq['pregunta']}. Respuesta: {faq['respuesta']}"


def generate_embeddings(model, faqs):
    """Genera embeddings para todas las FAQs."""
    print(f"{Fore.CYAN}Generando embeddings para {len(faqs)} FAQs...{Fore.RESET}")
    
    # Crear textos combinados
    texts = [generate_embedding_text(faq) for faq in faqs]
    
    # Generar embeddings
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Asociar embeddings a FAQs
    for faq, embedding in zip(faqs, embeddings):
        faq["embedding"] = embedding.tolist()
    
    print(f"{Fore.GREEN}✓ Embeddings generados correctamente{Fore.RESET}\n")
    return faqs


def connect_database():
    """Establece conexión a PostgreSQL."""
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        return connection
    except psycopg2.OperationalError as e:
        print(f"{Fore.RED}Error de conexión a PostgreSQL: {e}{Fore.RESET}")
        print("Asegúrate de que Docker está corriendo y el contenedor está activo.\n")
        sys.exit(1)


def insert_embeddings(connection, faqs):
    """Inserta los embeddings en PostgreSQL."""
    print(f"{Fore.CYAN}Insertando embeddings en PostgreSQL...{Fore.RESET}")
    
    cursor = connection.cursor()
    
    # Limpiar registros anteriores (estrategia simple)
    try:
        cursor.execute("DELETE FROM faqs;")
        connection.commit()
        print(f"{Fore.YELLOW}  Tabla limpiada{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.YELLOW}  Advertencia al limpiar tabla: {e}{Fore.RESET}")
    
    inserted = 0
    failed = 0
    
    for faq in faqs:
        try:
            # Registrar el tipo vector de pgvector
            cursor.execute("""
                INSERT INTO faqs (faq_id, categoria, pregunta, respuesta, embedding)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (faq_id) DO UPDATE SET
                    categoria = EXCLUDED.categoria,
                    pregunta = EXCLUDED.pregunta,
                    respuesta = EXCLUDED.respuesta,
                    embedding = EXCLUDED.embedding;
            """, (
                faq["faq_id"],
                faq["categoria"],
                faq["pregunta"],
                faq["respuesta"],
                # pgvector acepta arrays como JSON
                json.dumps(faq["embedding"])
            ))
            inserted += 1
        except Exception as e:
            print(f"{Fore.YELLOW}  Error al insertar {faq['faq_id']}: {e}{Fore.RESET}")
            failed += 1
    
    connection.commit()
    cursor.close()
    
    print(f"{Fore.GREEN}✓ Registros insertados: {inserted}{Fore.RESET}")
    if failed > 0:
        print(f"{Fore.YELLOW}⚠ Registros fallidos: {failed}{Fore.RESET}")
    print()


def verify_insertion(connection):
    """Verifica que los datos se insertaron correctamente."""
    cursor = connection.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM faqs;")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL;")
    with_embeddings = cursor.fetchone()[0]
    
    cursor.close()
    
    print(f"{Fore.CYAN}Verificación de base de datos:{Fore.RESET}")
    print(f"  Total de FAQs: {count}")
    print(f"  FAQs con embeddings: {with_embeddings}")
    
    if count == with_embeddings:
        print(f"{Fore.GREEN}✓ Todos los registros tienen embeddings{Fore.RESET}\n")
    else:
        print(f"{Fore.YELLOW}⚠ Algunos registros no tienen embeddings{Fore.RESET}\n")


def main():
    """Función principal."""
    print(f"\n{Fore.CYAN}=== CARGA DE EMBEDDINGS - PARACHUTE RAG ==={Fore.RESET}\n")
    
    # 1. Validar corpus
    validate_files()
    
    # 2. Parsear corpus
    faqs = parse_corpus()
    
    if not faqs:
        print(f"{Fore.RED}Error: no se detectaron FAQs en el corpus.{Fore.RESET}")
        sys.exit(1)
    
    # 3. Cargar modelo
    model = load_model()
    
    # 4. Generar embeddings
    faqs = generate_embeddings(model, faqs)
    
    # 5. Conectar a base de datos
    print(f"{Fore.CYAN}Conectando a PostgreSQL...{Fore.RESET}")
    connection = connect_database()
    print(f"{Fore.GREEN}✓ Conexión establecida{Fore.RESET}\n")
    
    # 6. Insertar embeddings
    insert_embeddings(connection, faqs)
    
    # 7. Verificar
    verify_insertion(connection)
    
    connection.close()
    
    print(f"{Fore.GREEN}=== CARGA COMPLETADA EXITOSAMENTE ==={Fore.RESET}\n")


if __name__ == "__main__":
    main()
