import argparse
import json
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from client import client

from config import (
    DEFAULT_MODEL,
    VECTOR_STORE_ID,
    validate_model_alias,
    resolve_model,
    recipe_image_path,
    extracted_path,
    external_validation_path,
)

from pharmacy_decision_schema import PharmacyFulfillmentDecision


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def item_is_complete(item):
    return all([
        item.medication,
        item.concentration,
        item.pharmaceutical_form,
        item.quantity,
    ])


def normalize_status(decision):
    """
    Minimal business guardrail.

    If every order item contains the four fields needed by
    Pharmacy, external corroboration issues do not block
    fulfillment.
    """

    complete_order = (
        bool(decision.order_items)
        and all(
            item_is_complete(item)
            for item in decision.order_items
        )
    )

    if complete_order:
        decision.non_blocking_issues.extend(
            decision.blocking_issues
        )

        decision.blocking_issues = []
        decision.status = "READY_FOR_PHARMACY"

    elif decision.blocking_issues:
        if decision.status == "READY_FOR_PHARMACY":
            decision.status = "PHARMACY_REVIEW"

    return decision


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("recipe")
    parser.add_argument("model", nargs="?", default=None)

    args = parser.parse_args()

    model_alias = validate_model_alias(
        args.model or DEFAULT_MODEL
    )

    model = resolve_model(model_alias)

    image_path = recipe_image_path(args.recipe)

    recipe = load_json(
        extracted_path(image_path)
    )

    external_validation = load_json(
        external_validation_path(image_path)
    )

    prompt = f"""
Eres un asistente administrativo encargado de preparar
una orden de atención para Farmacia.

Tu objetivo NO es realizar una auditoría clínica.

Determina si la receta contiene información suficiente para
identificar:

- medicamento;
- concentración;
- presentación;
- cantidad.

Utiliza:

1. La receta extraída como fuente primaria.
2. CIMA únicamente como fuente externa de corroboración.
3. Las políticas institucionales recuperadas mediante File Search.

REGLAS:

- No inventes información.
- No calcules cantidades usando dosis, frecuencia o duración.
- No corrijas automáticamente la receta utilizando CIMA.
- NOT_CONFIRMED no bloquea automáticamente.
- AMBIGUOUS no bloquea automáticamente.
- API_ERROR no bloquea automáticamente.
- Una discrepancia con CIMA no debe bloquear si la propia
  receta contiene medicamento, concentración, presentación
  y cantidad suficientes para preparar la orden.
- Las discrepancias externas que no bloquean deben registrarse
  como non_blocking_issues.
- La falta de dosis, frecuencia, duración o instrucciones no
  bloquea por sí sola la orden de Farmacia.
- Conserva las políticas utilizadas en policy y sources.

Estados permitidos:

READY_FOR_PHARMACY
PHARMACY_REVIEW
INSUFFICIENT_INFORMATION


EXTRACCIÓN DE LA RECETA:

{json.dumps(
    recipe,
    indent=2,
    ensure_ascii=False,
)}


VALIDACIÓN EXTERNA CIMA:

{json.dumps(
    external_validation,
    indent=2,
    ensure_ascii=False,
)}
"""

    response = client.responses.parse(
        model=model,
        input=prompt,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [
                    VECTOR_STORE_ID
                ],
                "max_num_results": 5,
            }
        ],
        text_format=PharmacyFulfillmentDecision,
    )

    decision = normalize_status(
        response.output_parsed
    )

    print(
        decision.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()