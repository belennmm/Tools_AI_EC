   # Parachute RAG

Agente de preguntas frecuentes para Parachute S.A. desarrollado en Python.

El programa carga el archivo `FAQs_Parachute_SA_Guatemala_2026.txt` y utiliza su contenido como contexto para responder preguntas sobre el evento de paracaidismo.

Si la información solicitada no aparece en el archivo, el agente indica que no cuenta con esa información.

## VIDEO
Video demostrativo: https://youtu.be/F_v7aJ-50D0

## Tecnologías

- Python
- OpenAI Python SDK
- Groq como proveedor del modelo
- python-dotenv
- colorama

Modelo utilizado:

`openai/gpt-oss-120b`

## Arquitectura

El proyecto utiliza una arquitectura RAG sencilla:

```text
Usuario
   ↓
Pregunta
   ↓
Parachute_RAG.py
   ↓
Archivo de FAQs
   ↓
Contexto + pregunta
   ↓
Groq mediante API compatible con OpenAI
   ↓
Respuesta
```

El archivo de FAQs es la única fuente de información utilizada por el agente.

## Instalación

Crear un entorno virtual:

```powershell
python -m venv venv
```

Activarlo:

```powershell
.\venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
pip install -r requirements.txt
```

## API Key

Crear el archivo `.env` a partir de `.env.example`:

```powershell
Copy-Item .env.example .env
```

Luego agregar la API key de Groq:

```env
GROQ_API_KEY=tu_api_key
```

La API key puede obtenerse desde:

https://console.groq.com

El archivo `.env` está incluido en `.gitignore` y no debe subirse al repositorio.

## Ejecución

Con el entorno virtual activado:

```powershell
python Parachute_RAG.py
```

Ejemplo:

```text
Agente de Preguntas Frecuentes - Parachute S.A.
Asistente para consultas del evento
Puedes hacer preguntas sobre horarios, requisitos, pagos y preparación.
Para salir escribe "Bye".

Pregunta: ¿Cuál es el peso máximo?
Respuesta: El límite de peso máximo es de 100 kg (220 lbs).

Pregunta: ¿Puedo llevar a mi perro?
Respuesta: No cuento con información sobre eso en las preguntas frecuentes proporcionadas.
```

La sesión puede finalizar escribiendo:

```text
Bye
```

o utilizando `Ctrl+C`.

## Archivos

```text
RAG_AI_EC/
├── Parachute_RAG.py
├── FAQs_Parachute_SA_Guatemala_2026.txt
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Seguridad

La API key no se almacena directamente en el código. Se utiliza una variable de entorno mediante el archivo `.env`.
