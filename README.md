# Agent Parachute S.A

Agente de preguntas frecuentes para Parachute S.A. desarrollado en Python.

El agente responde únicamente con información obtenida del archivo `Corpus_FAQs_Parachute_SA_2026.txt`.

Si la información solicitada no aparece en la base de conocimientos, el agente indica que no cuenta con información suficiente para responder.

## VIDEO

Video demostrativo: [https://youtu.be/F_v7aJ-50D0](https://youtu.be/F_v7aJ-50D0)

## Tecnologías

- Python
- PostgreSQL
- pgvector
- Docker / Docker Compose
- sentence-transformers
- OpenAI Python SDK
- Groq como proveedor del modelo
- psycopg2
- python-dotenv
- colorama

Modelo de lenguaje utilizado:

`openai/gpt-oss-120b`

Modelo de embeddings utilizado:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Dimensión de los embeddings:

`384`

## Arquitectura

El proyecto utiliza una arquitectura RAG con búsqueda vectorial y tool calling:

```text
Usuario
   ↓
Pregunta
   ↓
Parachute_Agent.py
   ↓
Groq mediante API compatible con OpenAI
   ↓
Tool call: buscar_en_base_conocimiento
   ↓
knowledge_tool.py
   ↓
sentence-transformers
   ↓
Embedding de la consulta
   ↓
PostgreSQL + pgvector
   ↓
TOP 3 FAQs más similares
   ↓
Resultado de la herramienta
   ↓
Groq
   ↓
Respuesta final
```

La única fuente de información del agente es el contenido almacenado a partir de `Corpus_FAQs_Parachute_SA_2026.txt`.

Se revisa si los resultados recuperados y el agente responde únicamente con información respaldada por las FAQs. Si ninguna FAQ recuperada contiene información suficiente, el agente se lo dice al usuario.

## Infraestructura

La base de datos se ejecuta mediante Docker utilizando PostgreSQL con la extensión `pgvector`.

Python se ejecuta también dentro de Docker para evitar problemas de compatibilidad con las dependencias locales.

## Instalación

Se requiere:

- Docker Desktop
- Git
- Una API key de Groq

Clonar o descargar el repositorio y abrir una terminal en la carpeta del proyecto.

## Variables de entorno

Crear el archivo `.env` a partir de `.env.example`:

```powershell
Copy-Item .env.example .env
```

Luego configurar las variables necesarias.


Implementar API KEY de Grook.

Levantar PostgreSQL:

```powershell
docker compose up -d postgres
```

Verificar que el contenedor esté activo:

```powershell
docker compose ps
```

Construir la imagen de la aplicación:

```powershell
docker compose build app
```

## Script de carga

El archivo `load_embeddings.py`:

1. Lee el corpus `Corpus_FAQs_Parachute_SA_2026.txt`.
2. Extrae las FAQs.
3. Genera embeddings locales con `sentence-transformers`.
4. Inserta las FAQs y sus embeddings en PostgreSQL.
5. Verifica que los registros hayan sido almacenados correctamente.

Para ejecutar el script de carga:

```powershell
docker compose run --rm app python load_embeddings.py
```

La carga esperada debe detectar:

```text
120 FAQs
120 registros insertados
120 FAQs con embeddings
```

Los embeddings para la búsqueda son la pregunta de cada FAQ, mientras que la respuesta completa se conserva en PostgreSQL ya que lo utiliza el agente.

## Búsqueda vectorial

La búsqueda utiliza `pgvector` con distancia coseno.

La herramienta recupera los tres resultados más similares:

```text
TOP 3 FAQs
```

Para probar directamente la búsqueda vectorial:

```powershell
docker compose run --rm app python test_vector_search.py
```


## Ejecución del agente

Para iniciar el agente:

```powershell
docker compose run --rm app python Parachute_Agent.py
```

Ejemplo:

```text
PARACHUTE S.A. - Agente de Atención al Cliente

Pregunta: ¿Cuál es el peso máximo permitido para saltar?

[Consultando base de conocimientos...]

Respuesta:
El límite máximo estricto para saltar es 100 kg.
```


## Terminar Sesión

Se termina la sesión al decir:

```text
Bye
```

sin importar mayúsculas o minúsculas.

También se puede forzar con:

```text
Ctrl+C
```


## Seguridad

La API key no se almacena directamente en el código.

Se utiliza una variable de entorno mediante el archivo `.env`.

El archivo `.env` está excluido del repositorio mediante `.gitignore`.



## Consideraciones

El archivo original de Parachute S.A. contiene algunas respuestas completas y otras respuestas genéricas.

El agente no completa información faltante utilizando conocimiento externo.

Cuando una FAQ es relevante pero no contiene el dato solicitado, el agente indica que la información específica no está disponible en la base de conocimientos.

Esto permite cumplir con la condición de responder únicamente utilizando la información proporcionada en el corpus.
