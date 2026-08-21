import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import argparse

from client import client
from config import resolve_model, validate_model_alias

parser = argparse.ArgumentParser(description="Model switching")
parser.add_argument("model", nargs="?", default=None)
args = parser.parse_args()
logical = validate_model_alias(args.model)
model = resolve_model(logical)

response = client.responses.create(
    model=model,
    input=(
        "Responde únicamente:"
        "OCI Generative AI funcionando con el modelo seleccionado."
        "Explica en una frase qué ventaja ofrece una API compatible con OpenAI."
    ),
)

print(f"MODEL: {logical}")
print(response.output_text)
