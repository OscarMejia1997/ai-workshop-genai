import argparse
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from client import client
from config import VECTOR_STORE_ID, extracted_path, external_validation_path, recipe_image_path, resolve_model, validate_model_alias
from pharmacy_decision_schema import PharmacyFulfillmentDecision

PROMPT = """
Eres un asistente administrativo encargado de preparar órdenes de atención para Farmacia.

Tu objetivo NO es auditar clínicamente la receta.
Determina si existe información suficiente para identificar medicamento, concentración, presentación y cantidad.

Reglas:
- No inventes datos ni cantidades.
- No calcules cantidades a partir de dosis, frecuencia o duración.
- No corrijas automáticamente los datos extraídos usando CIMA.
- La ausencia de frecuencia, duración, dosis por administración, diagnóstico o instrucciones clínicas no bloquea por sí sola.
- NOT_CONFIRMED, AMBIGUOUS y API_ERROR de CIMA no bloquean automáticamente.
- Usa exclusivamente las políticas institucionales recuperadas mediante File Search.
- Conserva discrepancias externas relevantes como non_blocking_issue cuando no impidan generar la orden.

Estados permitidos:
READY_FOR_PHARMACY
PHARMACY_REVIEW
INSUFFICIENT_INFORMATION

Devuelve únicamente PharmacyFulfillmentDecision.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe")
    parser.add_argument("model", nargs="?", default=None)
    args = parser.parse_args()
    logical = validate_model_alias(args.model)
    model = resolve_model(logical)
    image = recipe_image_path(args.recipe)
    extraction = json.loads(extracted_path(image).read_text(encoding="utf-8"))
    external = json.loads(external_validation_path(image).read_text(encoding="utf-8"))
    prompt = PROMPT + "\n\nEXTRACCIÓN:\n" + json.dumps(extraction, ensure_ascii=False, indent=2) + "\n\nCIMA:\n" + json.dumps(external, ensure_ascii=False, indent=2)
    response = client.responses.parse(
        model=model,
        input=prompt,
        tools=[{"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID], "max_num_results": 5}],
        text_format=PharmacyFulfillmentDecision,
    )
    print(response.output_parsed.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
