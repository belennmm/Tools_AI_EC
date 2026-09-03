# Usar imagen oficial de Python con soporte completo de PyTorch
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias del sistema (libpq para psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código (sin .env)
COPY *.py ./
COPY *.txt ./
COPY *.sql ./

# Por defecto ejecuta bash (para flexibility)
CMD ["/bin/bash"]
