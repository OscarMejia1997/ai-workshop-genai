import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import argparse
import base64
import mimetypes

from client import client
from config import recipe_image_path, resolve_model, validate_model_alias


def image_to_data_url(path):
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


parser = argparse.ArgumentParser()
parser.add_argument("recipe")
parser.add_argument("model", nargs="?", default=None)
args = parser.parse_args()

logical = validate_model_alias(args.model)
model = resolve_model(logical)
image_path = recipe_image_path(args.recipe)
if not image_path.exists():
    raise FileNotFoundError(image_path)

response = client.responses.create(
    model=model,
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": """Analiza la imagen proporcionada.

1. Identifica qué tipo de documento es.
2. Describe brevemente su contenido.
3. Identifica la información que puedes leer.
4. Indica qué información no puedes determinar.

No realices recomendaciones médicas.
No inventes información.
"""},
            {"type": "input_image", "image_url": image_to_data_url(image_path)},
        ],
    }],
)

print(f"MODEL: {logical}")
print(response.output_text)
