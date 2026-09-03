"""
Agente de preguntas frecuentes para Parachute S.A.

El programa carga un archivo de preguntas frecuentes y usa su contenido
como contexto para responder preguntas mediante la API de Groq.
"""

import os
import sys
from pathlib import Path

from colorama import Fore, init
from dotenv import load_dotenv
from openai import APIError, OpenAI


init(autoreset=True)


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

FAQ_FILE = Path(__file__).parent / "FAQs_Parachute_SA_Guatemala_2026.txt"


def validate_api_key():
    """Verifica que exista una API key de Groq."""
    if not GROQ_API_KEY:
        print(f"{Fore.RED}Error: no se encontró GROQ_API_KEY.{Fore.RESET}")
        print("Crea un archivo .env y agrega:")
        print("GROQ_API_KEY=tu_api_key")
        sys.exit(1)


def load_faq():
    """Carga el archivo de preguntas frecuentes."""
    if not FAQ_FILE.exists():
        print(f"{Fore.RED}Error: no se encontró {FAQ_FILE.name}.{Fore.RESET}")
        sys.exit(1)

    with open(FAQ_FILE, "r", encoding="utf-8") as file:
        content = file.read()

    if not content.strip():
        print(f"{Fore.RED}Error: {FAQ_FILE.name} está vacío.{Fore.RESET}")
        sys.exit(1)

    return content


def create_client():
    """Crea el cliente para conectarse con Groq."""
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )


def build_system_prompt(faq_content):
    """Crea las instrucciones que usará el agente."""
    return f"""
Eres el agente de preguntas frecuentes de Parachute S.A.

Responde únicamente con información disponible en el documento proporcionado.
No uses conocimiento externo, no inventes datos y no agregues detalles que
no aparezcan claramente en el documento.

Si una pregunta solo puede responderse parcialmente, responde únicamente
la parte que sí está respaldada por el documento.

Si la información no aparece en el documento, responde:
"No cuento con información sobre eso en las preguntas frecuentes proporcionadas."

Mantén las respuestas breves, claras y naturales.

DOCUMENTO:
-------------------------------------------------
{faq_content}
--------------------------------------------------
"""


def get_agent_response(client, system_prompt, conversation_history):
    """Envía la conversación al modelo y devuelve su respuesta."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history,
            ],
            temperature=0.3,
            max_tokens=500,
        )

        return response.choices[0].message.content

    except APIError as error:
        print(f"{Fore.RED}Error de API: {error}{Fore.RESET}")
        return None


def show_welcome():
    """Muestra el mensaje de bienvenida."""
    print(f"\n{Fore.CYAN}Agente de Preguntas Frecuentes - Parachute S.A.{Fore.RESET}")
    print("Asistente para consultas del evento")
    print("Puedes hacer preguntas sobre horarios, requisitos, pagos y preparación.")
    print('Para salir escribe "Bye".\n')


def main():
    """Función principal del programa."""
    validate_api_key()

    faq_content = load_faq()
    client = create_client()
    system_prompt = build_system_prompt(faq_content)

    conversation_history = []

    show_welcome()

    try:
        while True:
            try:
                user_input = input(f"{Fore.YELLOW}Pregunta:{Fore.RESET} ").strip()
            except EOFError:
                break

            if user_input.lower() == "bye":
                break

            if not user_input:
                continue

            conversation_history.append(
                {"role": "user", "content": user_input}
            )

            response = get_agent_response(
                client,
                system_prompt,
                conversation_history,
            )

            if response is None:
                conversation_history.pop()
                continue

            print(f"{Fore.GREEN}Respuesta:{Fore.RESET} {response}\n")

            conversation_history.append(
                {"role": "assistant", "content": response}
            )

            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

    except KeyboardInterrupt:
        pass

    print(f"\n{Fore.CYAN}Gracias por usar el agente de Parachute S.A.{Fore.RESET}")


if __name__ == "__main__":
    main()
