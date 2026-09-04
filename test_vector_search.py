"""
Script para probar búsqueda vectorial en PostgreSQL + pgvector

 da los TOP 3 resultados SIN threshold de similitud


1. Carga modelo: sentence-transformers/all-MiniLM-L6-v2
2. Genera embedding de la pregunta (384 dimensiones)
3. Consulta PostgreSQL con búsqueda EXACTA (sin índice ANN)
4. Devuelve TOP 3 ordenados por similitud coseno
5. Muestra scores de 0.0 a 1.0
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


load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "parachute_rag")
DB_USER = os.getenv("DB_USER", "parachute_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 3


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
        print(f"{Fore.RED}Error de conexión: {e}{Fore.RESET}\n")
        sys.exit(1)


def load_model():
    """Carga el modelo de embeddings."""
    try:
        return SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"{Fore.RED}Error al cargar el modelo: {e}{Fore.RESET}\n")
        sys.exit(1)


def search_faqs(connection, query_embedding, top_k=TOP_K):
    """
    Busca FAQs similares usando pgvector con búsqueda EXACTA.
    
    SIN índice IVFFLAT para garantizar resultados precisos.
    Usa el operador <=> de pgvector (distancia coseno).
    
    Parámetros:
    - query_embedding: vector numpy convertido a lista
    - top_k: número de resultados (TOP_K = 3)
    
    Retorna:
    - Lista de tuplas con (faq_id, categoria, pregunta, respuesta, similarity_score)
    - similarity_score está en rango [0.0, 1.0] donde 1.0 = exacta
    """
    cursor = connection.cursor()
    
    #  embedding a formato JSON para pgvector
    embedding_json = json.dumps(query_embedding)
    
    # Consulta SQL
    # - LIMIT TOP_K (devuelve 3 resultados siempre, sin threshold)
    query = """
    SELECT 
        faq_id,
        categoria,
        pregunta,
        respuesta,
        (1 - (embedding <=> %s::vector)) AS similarity_score
    FROM faqs
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    
    try:
        cursor.execute(query, (embedding_json, embedding_json, top_k))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"{Fore.RED}Error en búsqueda: {e}{Fore.RESET}\n")
        cursor.close()
        return []


def display_results(question, results, query_number):
    """Muestra los resultados de forma legible."""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}Pregunta #{query_number}:{Fore.RESET} {question}\n")
    
    if not results:
        print(f"{Fore.RED}✗ No se encontraron resultados (error interno).{Fore.RESET}\n")
        return
    
    for i, (faq_id, categoria, pregunta, respuesta, score) in enumerate(results, 1):
       
        if score >= 0.7:
            score_color = Fore.GREEN
            score_marker = "✓ ALTA"
        elif score >= 0.5:
            score_color = Fore.YELLOW
            score_marker = "⚠ MEDIA"
        else:
            score_color = Fore.MAGENTA
            score_marker = "△ BAJA"
        
        print(f"{Fore.GREEN}Resultado #{i}{Fore.RESET}")
        print(f"  ID: {faq_id}")
        print(f"  Categoría: {categoria}")
        print(f"  {score_color}Similitud: {score:.4f} ({score_marker}){Fore.RESET}")
        print(f"  Pregunta: {pregunta}")
        print(f"  Respuesta: {respuesta[:100]}..." if len(respuesta) > 100 else f"  Respuesta: {respuesta}")
        print()


def main():
    """Función principal."""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.CYAN}=== PRUEBA DE BÚSQUEDA VECTORIAL (Sin Índice ANN) ==={Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    
    print(f"{Fore.CYAN}Cargando modelo: {MODEL_NAME}...{Fore.RESET}")
    model = load_model()
    print(f"{Fore.GREEN}✓ Modelo cargado (dimensión: 384){Fore.RESET}\n")
    
    # a base de datos
    print(f"{Fore.CYAN}Conectando a PostgreSQL...{Fore.RESET}")
    connection = connect_database()
    print(f"{Fore.GREEN}✓ Conexión establecida{Fore.RESET}\n")
    
    # hay datos
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM faqs;")
    count = cursor.fetchone()[0]
    
    #si existe índice IVFFLAT
    cursor.execute("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'faqs' AND indexname LIKE '%embedding%';
    """)
    indexes = cursor.fetchall()
    cursor.close()
    
    if count == 0:
        print(f"{Fore.RED}✗ Error: La tabla 'faqs' está vacía.{Fore.RESET}")
        print("Ejecuta: docker compose run --rm app python load_embeddings.py\n")
        connection.close()
        sys.exit(1)
    
    print(f"{Fore.CYAN}Registros en base de datos: {count}{Fore.RESET}")
    if indexes:
        print(f"{Fore.YELLOW}Índices detectados: {[idx[0] for idx in indexes]}{Fore.RESET}")
    else:
        print(f"{Fore.GREEN}✓ Sin índices ANN (búsqueda exacta){Fore.RESET}")
    print()
    
    #  prueba
    test_queries = [
        ("¿Cuál es el peso máximo permitido para saltar?", "EXACTA - Sobre peso"),
        ("¿Cómo puedo llegar al evento desde Guatemala?", "EXACTA - Sobre logística"),
        ("¿Puedo traer a mi familia para ver los saltos?", "EXACTA - Sobre acompañantes"),
        ("Información sobre el clima y la lluvia", "RELACIONADA - Clima"),
        ("¿Cuánto cuesta un viaje en avión?", "NO RELACIONADA - Fuera de tema"),
    ]
    
    print(f"{Fore.CYAN}Ejecutando {len(test_queries)} consultas de diagnóstico...\n{Fore.RESET}")
    
    for query_num, (question, desc) in enumerate(test_queries, 1):
        print(f"{Fore.CYAN}[{query_num}/{len(test_queries)}] {desc}{Fore.RESET}")
        
        # embedding de la pregunta
        question_embedding = model.encode(question).tolist()
        
        # FAQs similares (TOP 3 sin threshold)
        results = search_faqs(connection, question_embedding, top_k=TOP_K)
        
        #  resultados
        display_results(question, results, query_num)
    
    connection.close()
    
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.GREEN}=== PRUEBAS COMPLETADAS ==={Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")


if __name__ == "__main__": main()
