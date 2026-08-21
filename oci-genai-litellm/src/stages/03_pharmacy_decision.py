import argparse
import json
import sys
from pathlib import Path


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ============================================================
# Shared modules
# ============================================================

from client import client

from config import (
    VECTOR_STORE_ID,
    DEFAULT_MODEL,
    validate_model_alias,
    recipe_image_path,
    extracted_path,
    external_validation_path,
)

from pharmacy_decision_schema import (
    PharmacyFulfillmentDecision,
)


# ============================================================
# Arguments
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a pharmacy fulfillment decision "
            "using LiteLLM and RAG."
        )
    )

    parser.add_argument(
        "recipe",
        help="Recipe image filename.",
    )

    parser.add_argument(
        "model",
        nargs="?",
        default=None,
        help="Model alias, for example gemini or grok.",
    )

    return parser.parse_args()


# ============================================================
# Helpers
# ============================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def has_value(value) -> bool:
    return (
        value is not None
        and str(value).strip() != ""
    )


def normalize_decision(
    decision: PharmacyFulfillmentDecision,
) -> PharmacyFulfillmentDecision:
    """
    Deterministic business guardrail.

    The LLM explains the evidence.
    This function determines the operational status.
    """

    missing_medication = []
    missing_quantity = []
    incomplete_product = []

    for index, item in enumerate(
        decision.order_items
    ):

        if not has_value(
            item.medication
        ):
            missing_medication.append(
                index
            )

        if not has_value(
            item.quantity
        ):
            missing_quantity.append(
                index
            )

        if (
            not has_value(item.concentration)
            or not has_value(item.pharmaceutical_form)
        ):
            incomplete_product.append(
                index
            )

    # --------------------------------------------------------
    # No actionable medication data
    # --------------------------------------------------------

    if missing_medication or missing_quantity:

        decision.status = (
            "INSUFFICIENT_INFORMATION"
        )

        return decision

    # --------------------------------------------------------
    # Product partially identified
    # --------------------------------------------------------

    if incomplete_product:

        decision.status = (
            "PHARMACY_REVIEW"
        )

        return decision

    # --------------------------------------------------------
    # Core pharmacy information is complete.
    #
    # CIMA discrepancies remain evidence, but do not
    # change the operational status by themselves.
    # --------------------------------------------------------

    decision.status = (
        "READY_FOR_PHARMACY"
    )

    # NOT_CONFIRMED should remain non-blocking.
    if decision.blocking_issues:

        decision.non_blocking_issues.extend(
            decision.blocking_issues
        )

        decision.blocking_issues = []

    return decision


# ============================================================
# Main
# ============================================================

def main():

    args = parse_args()

    model_alias = validate_model_alias(
        args.model or DEFAULT_MODEL
    )

    image_path = recipe_image_path(
        args.recipe
    )

    recipe = load_json(
        extracted_path(image_path)
    )

    external_validation = load_json(
        external_validation_path(image_path)
    )

    prompt = f"""
Eres un asistente administrativo encargado de preparar
una orden de atención para Farmacia.

NO estás realizando una auditoría clínica.

La receta extraída es la fuente primaria.

CIMA es una fuente externa de corroboración.

Las políticas institucionales recuperadas mediante File Search
son la autoridad para interpretar discrepancias.

Reglas:

- No inventes datos.
- No inventes cantidades.
- No calcules cantidades usando dosis, frecuencia o duración.
- No corrijas automáticamente la receta usando CIMA.
- NOT_CONFIRMED no bloquea automáticamente.
- AMBIGUOUS no bloquea automáticamente.
- API_ERROR no bloquea automáticamente.
- Las discrepancias de CIMA deben conservarse como evidencia.
- La ausencia de dosis, frecuencia, duración o instrucciones
  no bloquea por sí sola una orden de Farmacia.
- Un problema solo debe considerarse bloqueante si la información
  de la propia receta impide identificar el producto o cantidad.

Para cada medicamento considera como datos fundamentales:

- medicamento;
- concentración;
- forma farmacéutica;
- cantidad.

Devuelve únicamente PharmacyFulfillmentDecision.

RECETA EXTRAÍDA:

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

    print(
        "=========================================="
    )
    print(
        "PHARMACY DECISION"
    )
    print(
        "=========================================="
    )
    print(
        f"MODEL: {model_alias}"
    )
    print()

    response = client.responses.parse(
        model=model_alias,
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

    decision = normalize_decision(
        response.output_parsed
    )

    print(
        decision.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()