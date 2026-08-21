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
from config import extracted_path, recipe_image_path, resolve_model, validate_model_alias
from recipe_schema import Prescription

PROMPT = """
Analiza la receta médica de la imagen.

Extrae información explícitamente visible.
No tomes decisiones clínicas.
No inventes información.
Si un campo no aparece, utiliza null.
Si un campo es ambiguo o ilegible, utiliza null y agrégalo a ambiguous_fields.
No corrijas nombres de medicamentos.
prescribed_quantity solo debe contener una cantidad explícita.
requires_human_review debe permanecer en false.
"""


def image_to_data_url(path):
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe")
    parser.add_argument("model", nargs="?", default=None)
    args = parser.parse_args()
    logical = validate_model_alias(args.model)
    model = resolve_model(logical)
    image_path = recipe_image_path(args.recipe)
    output_path = extracted_path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    response = client.responses.parse(
        model=model,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": PROMPT},
            {"type": "input_image", "image_url": image_to_data_url(image_path)},
        ]}],
        text_format=Prescription,
    )
    recipe = response.output_parsed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(recipe.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"MODEL: {logical}")
    print(f"Recipe extracted and saved to: {output_path}")
    print(json.dumps(recipe.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
