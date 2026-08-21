import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from client import client
from config import recipe_image_path, resolve_model, validate_model_alias
from recipe_schema import Prescription

PROMPT = """
Analiza la receta médica de la imagen y extrae información visible.

- Usa null cuando un campo no esté disponible.
- Registra información ambigua en ambiguous_fields.
- No inventes datos.
- No corrijas nombres de medicamentos.
- No realices decisiones clínicas.
"""

def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"

parser = argparse.ArgumentParser()
parser.add_argument("recipe")
parser.add_argument("model", nargs="?", default=None)
args = parser.parse_args()

logical = validate_model_alias(args.model)
model = resolve_model(logical)
image = recipe_image_path(args.recipe)
if not image.exists():
    raise FileNotFoundError(image)

response = client.responses.parse(
    model=model,
    input=[{"role":"user","content":[
        {"type":"input_text","text":PROMPT},
        {"type":"input_image","image_url":image_to_data_url(image)},
    ]}],
    text_format=Prescription,
)

print(f"MODEL: {logical}")
print(json.dumps(response.output_parsed.model_dump(), indent=2, ensure_ascii=False))
