"""
ver que PyTorch y sentence-transformers funcionan.
"""

import sys
from colorama import Fore, init

init(autoreset=True)

print(f"\n{Fore.CYAN}verificar  PYTORCH y  SENTENCE-TRANSFORMERS {Fore.RESET}\n")

try:
   
    import torch
    print(f"{Fore.GREEN} PyTorch cargado correctamente{Fore.RESET}")
    print(f"  Versión: {torch.__version__}")
    print(f"  CUDA disponible: {torch.cuda.is_available()}\n")
except Exception as e:
    print(f"{Fore.RED}Error: {e}{Fore.RESET}\n")
    sys.exit(1)

try:
   
    from sentence_transformers import SentenceTransformer
    print(f"{Fore.GREEN}sentence_transformers cargado correctamente{Fore.RESET}\n")
except Exception as e:
    print(f"{Fore.RED}Error transformers: {e}{Fore.RESET}\n")
    sys.exit(1)

try:
  
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"{Fore.GREEN}Modelo cargado correctamente{Fore.RESET}\n")
except Exception as e:
    print(f"{Fore.RED}Error: {e}{Fore.RESET}\n")
    sys.exit(1)

try:
 
    test_sentence = "¿Cuál es el peso máximo permitido para saltar?"
    embedding = model.encode(test_sentence)
    print(f"{Fore.GREEN}Embedding generado correctamente{Fore.RESET}")
    print(f"  Dimensión: {len(embedding)}")
    print(f"  Primeros valores: {embedding[:5]}\n")
except Exception as e:
    print(f"{Fore.RED}Error: {e}{Fore.RESET}\n")
    sys.exit(1)

