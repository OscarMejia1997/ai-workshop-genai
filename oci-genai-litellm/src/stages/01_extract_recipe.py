import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import argparse
import base64
import json
import mimetypes

from client import client
from config import extracted_path, recipe_image_path, validate_model_alias
from recipe_schema import Prescription

PROMPT = """
Analiza la receta médica de la imagen y extrae solo información visible.
No inventes ni corrijas información. La cantidad total prescrita solo debe contener una cantidad explícita.
requires_human_review debe permanecer en false; la decisión de negocio se toma después con RAG.
"""


def image_url(path):
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe")
    parser.add_argument("model", nargs="?", default=None)
    args = parser.parse_args()
    model = validate_model_alias(args.model)
    image = recipe_image_path(args.recipe)
    if not image.exists(): raise FileNotFoundError(image)
    response = client.responses.parse(
        model=model,
        input=[{"role":"user","content":[{"type":"input_text","text":PROMPT},{"type":"input_image","image_url":image_url(image)}]}],
        text_format=Prescription,
    )
    out = extracted_path(image)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(response.output_parsed.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(response.output_parsed.model_dump(), indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
