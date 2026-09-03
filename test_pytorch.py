"""
Script simple para verificar que PyTorch y sentence-transformers funcionan.
Ejecutar dentro del contenedor Docker.
"""

import sys
from colorama import Fore, init

init(autoreset=True)

print(f"\n{Fore.CYAN}=== VERIFICACIÓN DE PYTORCH Y SENTENCE-TRANSFORMERS ==={Fore.RESET}\n")

try:
    print(f"{Fore.CYAN}Importando torch...{Fore.RESET}")
    import torch
    print(f"{Fore.GREEN}✓ PyTorch cargado correctamente{Fore.RESET}")
    print(f"  Versión: {torch.__version__}")
    print(f"  CUDA disponible: {torch.cuda.is_available()}\n")
except Exception as e:
    print(f"{Fore.RED}✗ Error al cargar PyTorch: {e}{Fore.RESET}\n")
    sys.exit(1)

try:
    print(f"{Fore.CYAN}Importando sentence_transformers...{Fore.RESET}")
    from sentence_transformers import SentenceTransformer
    print(f"{Fore.GREEN}✓ sentence_transformers cargado correctamente{Fore.RESET}\n")
except Exception as e:
    print(f"{Fore.RED}✗ Error al cargar sentence_transformers: {e}{Fore.RESET}\n")
    sys.exit(1)

try:
    print(f"{Fore.CYAN}Cargando modelo: all-MiniLM-L6-v2 (primera ejecución puede tardar)...{Fore.RESET}")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"{Fore.GREEN}✓ Modelo cargado correctamente{Fore.RESET}\n")
except Exception as e:
    print(f"{Fore.RED}✗ Error al cargar modelo: {e}{Fore.RESET}\n")
    sys.exit(1)

try:
    print(f"{Fore.CYAN}Probando generación de embedding...{Fore.RESET}")
    test_sentence = "¿Cuál es el peso máximo permitido para saltar?"
    embedding = model.encode(test_sentence)
    print(f"{Fore.GREEN}✓ Embedding generado correctamente{Fore.RESET}")
    print(f"  Dimensión: {len(embedding)}")
    print(f"  Primeros valores: {embedding[:5]}\n")
except Exception as e:
    print(f"{Fore.RED}✗ Error al generar embedding: {e}{Fore.RESET}\n")
    sys.exit(1)

print(f"{Fore.GREEN}=== TODAS LAS VERIFICACIONES PASARON EXITOSAMENTE ==={Fore.RESET}\n")
