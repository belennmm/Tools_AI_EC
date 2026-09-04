"""
Agente final en terminal para Parachute S.A.

1. mantiene conversación multi-turno
2. usa tool calling para buscar en la base de conocimiento
3. solo responde con información explícita recuperada
4. admite cuando no tiene información

"""

import json
import os
import sys
from typing import List, Dict, Any

from colorama import Fore, Style, init
from dotenv import load_dotenv
from openai import OpenAI


from knowledge_tool import buscar_en_base_conocimiento, TOOL_DEFINITION

init(autoreset=True)


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

# evitar contexto muy largo
MAX_HISTORY_MESSAGES = 20


def validate_api_key():
    """Verifica que exista GROQ_API_KEY."""
    if not GROQ_API_KEY:
        print(f"{Fore.RED}❌ Error: GROQ_API_KEY no está configurada.{Fore.RESET}")
        print("Asegúrate de que .env contiene GROQ_API_KEY=...\n")
        sys.exit(1)


def create_groq_client():
    """Crea cliente de OpenAI configurado para Groq."""
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )


def get_system_prompt() -> str:
    """
    System prompt para responder únicamente con la información
    recuperada desde la base de conocimientos.
    """
    return """Eres un agente de atención al cliente para Parachute S.A.

Tu tarea es responder preguntas utilizando EXCLUSIVAMENTE la información
obtenida mediante la herramienta buscar_en_base_conocimiento.

REGLAS:

1. Para las preguntas sobre Parachute S.A. debes consultar la herramienta
   buscar_en_base_conocimiento antes de responder.

2. La herramienta devuelve hasta 3 FAQs candidatas.
   Que una FAQ aparezca entre los TOP 3 NO significa automáticamente
   que responda la pregunta. Debes revisar su PREGUNTA y su RESPUESTA.

IMPORTANTE SOBRE LOS TOP 3:

Debes revisar TODOS los resultados recuperados, no solamente el resultado #1.

La FAQ con mayor similarity_score puede tener una respuesta incompleta,
mientras que otra FAQ del TOP 3 puede contener explícitamente el dato solicitado.

Si varias FAQs son relevantes:
- Puedes combinar únicamente la información explícita que aparece en sus RESPUESTAS.
- No estás obligado a usar solamente la FAQ con mayor score.
- El similarity_score sirve para recuperación, no para decidir cuál respuesta es verdadera.
- Si una FAQ tiene una pregunta muy parecida pero su RESPUESTA es genérica,
  revisa las otras FAQs recuperadas para ver si alguna contiene el dato solicitado.

Ejemplo:
Si el usuario pregunta:
"¿Cuántos segundos dura la caída libre?"

y FAQ-051 tiene una respuesta genérica,
pero FAQ-053 contiene explícitamente que la caída libre dura aproximadamente
35 a 45 segundos, entonces debes responder utilizando ese dato de FAQ-053.

3. Existen tres posibles casos:

CASO A — Una o más FAQs relevantes con información concreta:
Revisa las RESPUESTAS de TODOS los resultados recuperados.

Si cualquiera de las FAQs relevantes contiene explícitamente el dato
solicitado por el usuario:
→ Utiliza ese dato para responder.
→ Puedes combinar información de varias FAQs relevantes si hablan del mismo tema.
→ Usa únicamente información explícita de sus campos RESPUESTA.
→ No agregues información externa ni inferida.
→ Sé breve y natural.

CASO B — FAQ relevante pero respuesta incompleta o genérica:
Si la PREGUNTA de una FAQ coincide claramente con lo que el usuario quiere
saber, pero el campo RESPUESTA no proporciona el dato específico:
→ NO digas simplemente que no existe información.
→ Explica brevemente qué información sí proporciona la base.
→ Aclara que el detalle solicitado no está especificado.
→ Si esa misma RESPUESTA contiene un correo, contacto o recomendación,
  puedes mencionarlo porque forma parte de la base de conocimientos.

MUY IMPORTANTE:
La PREGUNTA de una FAQ NO constituye una respuesta.

Nunca deduzcas una respuesta afirmativa o negativa únicamente a partir
del texto de la pregunta recuperada.

Ejemplo:
Si la FAQ pregunta:
"¿Puedo llevar acompañantes que no vayan a saltar?"

pero su campo RESPUESTA no dice explícitamente si se puede o no,
NO puedes responder:
"Sí, puedes llevar acompañantes."

En ese caso debes decir que la base contiene una FAQ sobre ese tema,
pero que la respuesta proporcionada no especifica claramente si está
permitido o no.

Ejemplo de estilo:
"La base de conocimientos contempla esa consulta, pero no especifica
el detalle solicitado. Indica consultar la información adicional
proporcionada por Parachute S.A."

CASO C — Ninguna FAQ es realmente relevante:
Si las preguntas recuperadas no tratan sobre lo que preguntó el usuario:
→ Responde exactamente:
"No cuento con información en la base de conocimientos para responder esa pregunta."

4. Está PROHIBIDO:
- Inventar datos.
- Completar información faltante.
- Usar conocimiento general.
- Inventar rutas, direcciones o lugares.
- Inventar precios, fechas u horarios.
- Inventar teléfonos, correos o contactos.
- Inventar políticas o procedimientos.
- Usar placeholders como [nombre], [dirección] o similares.

5. Puedes utilizar un correo, fecha, contacto, recomendación u otro dato
SOLAMENTE cuando aparezca explícitamente dentro de una FAQ recuperada y relevante.

6. La similitud vectorial ayuda a recuperar candidatos, pero NO determina por
sí sola si una FAQ responde la pregunta. Evalúa semánticamente la PREGUNTA
y la RESPUESTA recuperadas.

7. Responde siempre:
- En español.
- De manera breve.
- De forma natural.
- Únicamente con información respaldada por la base de conocimientos.

Nunca transformes una respuesta incompleta en una respuesta inventada."""


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """
    Procesa una llamada a herramienta.

    Parámetros:
    -----------
    tool_name : str
        Nombre de la herramienta
    tool_input : dict
        Argumentos de la herramienta

    Retorna:
    --------
    str
        JSON con los resultados
    """
    if tool_name == "buscar_en_base_conocimiento":
        query = tool_input.get("query", "")

        
        print(f"{Fore.CYAN}[Consultando base de conocimientos...]{Fore.RESET}")

        results = buscar_en_base_conocimiento(query)

       
        print(f"{Fore.MAGENTA}[Preguntas similares encontradas en el FAQ]{Fore.RESET}")

        for i, faq in enumerate(results[:3], 1):
            if "error" not in faq:
                score = faq.get("similarity_score", 0.0)
                faq_id = faq.get("faq_id", "?")
                pregunta = faq.get("pregunta", "?")[:50]

                print( f"{Fore.MAGENTA}  {i}. {faq_id} | " f"score {score:.4f} | {pregunta}..." f"{Fore.RESET}" )
        print()
    

        return json.dumps(results, ensure_ascii=False)
    else:
        return json.dumps({"error": f"Herramienta desconocida: {tool_name}"})


def limpiar_unicode(texto: str) -> str:
    """Elimina caracteres Unicode inválidos antes de enviarlos a la API."""
    if not isinstance(texto, str):
        return texto

    return texto.encode(
        "utf-8",
        errors="ignore"
    ).decode("utf-8")


def chat_with_agent(user_query: str, conversation_history: List[Dict]) -> tuple:
    """
    Interactúa con el agente usando tool calling.

    Parámetros:
    -----------
    user_query : str
        Pregunta del usuario
    conversation_history : list
        Historial de conversación anterior

    Retorna:
    --------
    tuple
        (respuesta_final, historial_actualizado)
    """
    client = create_groq_client()

    system_prompt = get_system_prompt()

    # mensajes: system + historial y  query actual
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    #  historial sin duplicar system
    messages.extend(conversation_history)

   
    messages.append({
        "role": "user",
        "content": user_query
    })

    iteration = 0
    max_iterations = 5

    while iteration < max_iterations:
        iteration += 1

        try:
            #  call LLM con tool
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[TOOL_DEFINITION],
                tool_choice="auto",
                temperature=0.3,  # Baja temperatura para menos creatividad
                max_tokens=512    # Respuestas breves
            )
            finish_reason = response.choices[0].finish_reason
        except Exception as e:
            return f"{Fore.RED}Error en Groq: {str(e)}{Fore.RESET}", conversation_history

        
        if finish_reason == "stop":
            # Modelo respondió después de procesar la información
            final_message = response.choices[0].message.content or ""
            final_message = limpiar_unicode(final_message)

            if not final_message.strip():
                final_message = (
                    "No cuento con información suficiente en la base de conocimientos "
                    "para responder esa pregunta."
                )

            
            conversation_history.append({
                "role": "user",
                "content": user_query
            })
            conversation_history.append({
                "role": "assistant",
                "content": final_message
            })

       
            if len(conversation_history) > MAX_HISTORY_MESSAGES:conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]

            return final_message, conversation_history

        if finish_reason == "tool_calls":
        
            assistant_message = response.choices[0].message

            tool_calls_made = False

            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_calls_made = True
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)

                    #  herramienta
                    tool_result = process_tool_call(tool_name, tool_input)

                    #  mensaje del asistente 
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    })

                    #  resultado de herramienta
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })

            if not tool_calls_made:
                # respuesta normal sin tool calls
                final_message = assistant_message.content or ""
                if not final_message.strip():
                    final_message = (
                        "No cuento con información suficiente en la base de conocimientos "
                        "para responder esa pregunta."
                    )

                conversation_history.append({"role": "user", "content": user_query})
                conversation_history.append({"role": "assistant","content": final_message})

                if len(conversation_history) > MAX_HISTORY_MESSAGES:conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]

                return final_message, conversation_history
        else:
            #  stop reason
            final_message = response.choices[0].message.content or ""
            final_message = limpiar_unicode(final_message)

            if not final_message.strip():
                final_message = (
                    "No cuento con información suficiente en la base de conocimientos "
                    "para responder esa pregunta."
                )

            conversation_history.append({
                "role": "user",
                "content": user_query
            })
            conversation_history.append({
                "role": "assistant",
                "content": final_message
            })

            if len(conversation_history) > MAX_HISTORY_MESSAGES:conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]

            return final_message, conversation_history

    # máximas iteraciones alcanzadas
    return f"{Fore.YELLOW}⚠ No se pudo obtener respuesta (máximas iteraciones).{Fore.RESET}", conversation_history


def print_welcome():
    """Muestra mensaje de bienvenida."""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.CYAN}╔{'='*68}╗{Fore.RESET}")
    print(f"{Fore.CYAN}║{Fore.YELLOW} PARACHUTE S.A. - Agente de Atención al Cliente {Fore.CYAN}║{Fore.RESET}")
    print(f"{Fore.CYAN}╚{'='*68}╝{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    print(f"{Fore.GREEN}¡Bienvenido! Soy el agente de Parachute S.A.{Fore.RESET}")
    print(f"{Fore.GREEN}Puedo responder preguntas sobre nuestro evento de paracaidismo.{Fore.RESET}\n")
    print(f"{Fore.YELLOW}Escribe 'Bye' (sin importar mayúsculas) para salir.{Fore.RESET}")
    print(f"{Fore.YELLOW}Usa Ctrl+C para salir de emergencia.{Fore.RESET}\n")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")


def main():
    """Función principal - loop interactivo del agente."""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.CYAN}=== ETAPA 8: AGENTE FINAL - PARACHUTE S.A. ==={Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")

    # validar API key
    validate_api_key()
    print(f"{Fore.GREEN}✓ GROQ_API_KEY configurada{Fore.RESET}")
    print(f"{Fore.GREEN}✓ Modelo: {MODEL}{Fore.RESET}")
    print(f"{Fore.GREEN}✓ Base de conocimientos: ready{Fore.RESET}\n")

    #  bienvenida
    print_welcome()

    # historial de conversación
    conversation_history = []

    # el loop
    try:
        while True:
            # Obtener pregunta del usuario
            user_input = input(f"{Fore.YELLOW}Pregunta: {Fore.RESET}").strip()
            user_input = limpiar_unicode(user_input)

            # ignore las líneas vacías
            if not user_input:
                continue

            # si es comando de salida
            if user_input.lower() == "bye":
                print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
                print(f"{Fore.GREEN}¡Gracias por usar Parachute S.A. Agent!{Fore.RESET}")
                print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
                break

            #  pregunta
            print()  
            response, conversation_history = chat_with_agent(
                user_input,
                conversation_history
            )

            #  respuesta
            print(f"\n{Fore.GREEN}Respuesta:{Fore.RESET}")
            print(response)
            print()  

    except KeyboardInterrupt:
        print(f"\n\n{Fore.CYAN}{'='*70}{Fore.RESET}")
        print(f"{Fore.YELLOW}Sesión interrumpida por el usuario (Ctrl+C){Fore.RESET}")
        print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Error inesperado: {str(e)}{Fore.RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":main()
