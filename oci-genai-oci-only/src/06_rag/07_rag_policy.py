import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from client import client
from config import VECTOR_STORE_ID, resolve_model, validate_model_alias

QUESTION = """
Según las políticas institucionales, ¿qué debe hacer el proceso cuando la validación externa no encuentra una coincidencia compatible, encuentra múltiples candidatos o no puede corroborar todos los atributos? ¿NOT_CONFIRMED bloquea automáticamente una orden de Farmacia?
Utiliza exclusivamente las políticas recuperadas.
"""

parser = argparse.ArgumentParser()
parser.add_argument("model", nargs="?", default=None)
args = parser.parse_args()
logical = validate_model_alias(args.model)
model = resolve_model(logical)
response = client.responses.create(model=model, input=QUESTION, tools=[{"type":"file_search","vector_store_ids":[VECTOR_STORE_ID],"max_num_results":5}])
print(f"MODEL: {logical}")
print(response.output_text)
