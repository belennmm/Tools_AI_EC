"""
Herramienta de búsqueda en base de conocimientos


1. recibe un string 
2. hace embedding con sentence-transformers
3. PostgreSQL + pgvector
4. da TOP 3 resultados con scores
"""

import json
import os
from typing import List, Dict, Any

import psycopg2
from sentence_transformers import SentenceTransformer

# Configuración
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "parachute_rag")
DB_USER = os.getenv("DB_USER", "parachute_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Instancia global del modelo (se carga una sola vez)
_model = None


def _get_model():
    """Obtiene la instancia del modelo (lazy loading)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_connection():
    """Establece conexión a PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def buscar_en_base_conocimiento(query: str) -> List[Dict[str, Any]]:
    """
    Busca en la base de conocimientos de Parachute S.A.
    
    Parámetros:
    -----------
    query : str
        Pregunta o consulta en lenguaje natural
    
    Retorna:
    --------
    list[dict]
        Lista de hasta 3 FAQs más similares, cada uno con:
        - faq_id: identificador único
        - categoria: categoría de la FAQ
        - pregunta: pregunta original
        - respuesta: respuesta completa
        - similarity_score: puntuación de similitud (0.0 a 1.0)
    
    Ejemplo:
    --------
    >>> resultados = buscar_en_base_conocimiento(
    ...     "¿Cuál es el peso máximo permitido?"
    ... )
    >>> print(resultados[0]['respuesta'])
    """
    try:
        # Obtener modelo
        model = _get_model()
        
        # Generar embedding de la consulta
        query_embedding = model.encode(query).tolist()
        
        
        # Conectar a PostgreSQL
        connection = _get_connection()
        cursor = connection.cursor()
        
        # Consulta SQL: TOP 3 con pgvector
        sql = """
        SELECT 
            faq_id,
            categoria,
            pregunta,
            respuesta,
            (1 - (embedding <=> %s::vector)) AS similarity_score
        FROM faqs
        ORDER BY embedding <=> %s::vector
        LIMIT 3;
        """
        
        embedding_json = json.dumps(query_embedding)
        cursor.execute(sql, (embedding_json, embedding_json))
        
        # Procesar resultados
        results = []
        for row in cursor.fetchall():
            faq_id, categoria, pregunta, respuesta, similarity_score = row
            results.append({
                "faq_id": faq_id,
                "categoria": categoria,
                "pregunta": pregunta,
                "respuesta": respuesta,
                "similarity_score": float(similarity_score)
            })
        
        cursor.close()
        connection.close()
        
        return results
    
    except psycopg2.OperationalError as e:
        return [{
            "error": f"Error de conexión a PostgreSQL: {str(e)}",
            "faq_id": None,
            "categoria": None,
            "pregunta": None,
            "respuesta": None,
            "similarity_score": 0.0
        }]
    except Exception as e:
        return [{
            "error": f"Error en búsqueda: {str(e)}",
            "faq_id": None,
            "categoria": None,
            "pregunta": None,
            "respuesta": None,
            "similarity_score": 0.0
        }]


# Esquema de la herramienta para OpenAI/Groq SDK
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "buscar_en_base_conocimiento",
        "description": "Busca preguntas frecuentes en la base de conocimientos de Parachute S.A. sobre el evento de paracaidismo. Devuelve las 3 FAQs más similares a la consulta del usuario.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Pregunta o consulta en lenguaje natural sobre el evento de paracaidismo de Parachute S.A."
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    consultas = [
        "¿Cuál es el peso máximo?",
        "¿Cómo puedo llegar al evento desde Guatemala?",
        "cómo llegar al aeródromo",
        "¿Qué pasa si llueve?",
        "¿Se permiten mascotas?"
    ]

    for consulta in consultas:
        print("\n" + "=" * 70)
        print(f"Consulta: {consulta}")
        print("=" * 70)

        resultados = buscar_en_base_conocimiento(consulta)

        for i, faq in enumerate(resultados, 1):
            print(
                f"{i}. {faq.get('faq_id')} | "
                f"{faq.get('similarity_score', 0):.4f} | "
                f"{faq.get('pregunta')}"
            )