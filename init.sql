-- Crear extensión de vectores
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear tabla para embeddings
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    faq_id VARCHAR(50) UNIQUE NOT NULL,
    categoria VARCHAR(255),
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NOTA: Para 120 registros, búsqueda exacta es mejor que índice ANN.
-- pgvector hace full-scan con operador <=> en ~1ms para 120 registros.
-- IVFFLAT con lists=100 es DEMASIADO agresivo para este dataset pequeño.
-- Se omite índice intencionalmente. Si el dataset crece > 100k, agregar:
--   CREATE INDEX idx_faq_embedding ON faqs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Crear tabla para historial de conversaciones 
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parachute_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parachute_user;
