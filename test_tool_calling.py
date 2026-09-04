"""
Prueba de tool calling con Groq SDK y búsqueda vectorial.

1. pregunta
2. LLM decide llamar a la herramienta
3. tool call
4. buscar_en_base_conocimiento()
5. resultados de vuelta al LLM
6. LLM genera respuesta final

prueba que el ciclo completo funciona correctamente.
"""

import json
import os
import sys

from colorama import Fore, init
from dotenv import load_dotenv
from openai import OpenAI

from knowledge_tool import buscar_en_base_conocimiento, TOOL_DEFINITION

init(autoreset=True)


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"


def validate_api_key():
    """Verifica que exista GROQ_API_KEY."""
    if not GROQ_API_KEY:
        print(f"{Fore.RED}Error: GROQ_API_KEY no está configurada.{Fore.RESET}")
        print("Asegúrate de que .env contiene GROQ_API_KEY=...\n")
        sys.exit(1)


def create_groq_client():
    """Crea cliente de OpenAI configurado para Groq."""
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """
    Procesa una llamada a herramienta.
    
    Parámetros:
    -----------
    tool_name : str
        Nombre de la herramienta a ejecutar
    tool_input : dict
        Argumentos de la herramienta
    
    Retorna:
    --------
    str
        JSON con los resultados de la herramienta
    """
    if tool_name == "buscar_en_base_conocimiento":
        query = tool_input.get("query", "")
        print(f"{Fore.CYAN}  → Ejecutando: buscar_en_base_conocimiento('{query}'){Fore.RESET}")
        
        results = buscar_en_base_conocimiento(query)
        
        # Mostrar resultados recuperados
        print(f"{Fore.GREEN}  → Recuperados {len(results)} resultados:{Fore.RESET}")
        for i, faq in enumerate(results, 1):
            if "error" not in faq:
                print(f"    [{i}] {faq['faq_id']} - Score: {faq['similarity_score']:.4f}")
        
        return json.dumps(results, ensure_ascii=False)
    else:
        return json.dumps({"error": f"Herramienta desconocida: {tool_name}"})


def agentic_loop(user_query: str):
    """
    Implementa el loop agentico completo.
    
    Parámetros:
    -----------
    user_query : str
        Pregunta del usuario
    """
    client = create_groq_client()
    
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}Pregunta del usuario:{Fore.RESET} {user_query}\n")
    
   
    system_prompt = """Eres un agente de preguntas frecuentes para Parachute S.A.
Cuando el usuario pregunte algo sobre el evento de paracaidismo, SIEMPRE usa la herramienta buscar_en_base_conocimiento para consultar la base de conocimientos.
Basándote en los resultados, proporciona una respuesta clara y útil.
Si los resultados no contienen información relevante (scores muy bajos), indica que no tienes esa información en la base de conocimientos.
Sé conciso y natural en tu respuesta."""
    
    # comenzar con system prompt y luego user query
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_query
        }
    ]
    
    iteration = 0
    max_iterations = 5  
    
    while iteration < max_iterations:
        iteration += 1
        print(f"{Fore.CYAN}[Iteración {iteration}]{Fore.RESET}")
        
        # llamar al LLM con la herramienta disponible
        # IMPORTANTE: system prompt va DENTRO de messages, NO como parámetro
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[TOOL_DEFINITION],
            tool_choice="auto"
        )
        
        finish_reason = response.choices[0].finish_reason

        
        if finish_reason == "tool_calls":
            
            assistant_message = response.choices[0].message
            
           
            tool_calls_made = False
            
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_calls_made = True
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)
                    
                    print(f"{Fore.CYAN}Herramienta solicitada:{Fore.RESET} {tool_name}")
                    
                    #  herramienta
                    tool_result = process_tool_call(tool_name, tool_input)
                    
                  
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
                    
                    # el resultado de la herramienta al historial
                   
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })
            
            if not tool_calls_made:
                # sin tool calls, mostrar respuesta normal
                final_message = assistant_message.content
                print(f"{Fore.GREEN}Respuesta del modelo:{Fore.RESET}\n{final_message}\n")
                break
        else:
            print(f"{Fore.YELLOW}Finish reason: {finish_reason}{Fore.RESET}")
            final_message = response.choices[0].message.content
            print(f"{Fore.GREEN}Respuesta del modelo:{Fore.RESET}\n{final_message}\n")
            break
    
    if iteration >= max_iterations:print(f"{Fore.YELLOW}Alcanzado número máximo de iteraciones{Fore.RESET}\n")


def main():
    """Función principal."""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.CYAN}=== PRUEBA DE TOOL CALLING CON GROQ ==={Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    # API key
    validate_api_key()
    print(f"{Fore.GREEN}✓ GROQ_API_KEY configurada{Fore.RESET}\n")
    
    # preguntas  de prueba
    test_queries = [
        "¿Cuál es el peso máximo permitido para saltar?",
        "¿Cómo llego al evento desde Guatemala?",
        "¿Se permiten mascotas en el evento?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{Fore.CYAN}[PRUEBA {i}/{len(test_queries)}]{Fore.RESET}\n")
        try:
            agentic_loop(query)
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Fore.RESET}\n")
            import traceback
            traceback.print_exc()
    
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.GREEN}=== PRUEBAS COMPLETADAS ==={Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")


if __name__ == "__main__":main()
