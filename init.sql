CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    faq_id VARCHAR(50) UNIQUE NOT NULL,
    categoria VARCHAR(255),
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- para 120 registros, búsqueda exacta es mejor que índice ANN.
-- y evita la pérdida de recall de un índice ANN mal ajustado.

-- si el dataset crece > 100k, agregar:


CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parachute_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parachute_user;
