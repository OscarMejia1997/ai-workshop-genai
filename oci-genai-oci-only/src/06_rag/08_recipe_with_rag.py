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

from pharmacy_decision_schema import (
    PharmacyFulfillmentDecision,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a pharmacy fulfillment decision "
            "using extraction, CIMA and RAG."
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
        help="Optional model alias.",
    )

    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def normalize_status(
    decision: PharmacyFulfillmentDecision,
) -> PharmacyFulfillmentDecision:
    """
    Minimal consistency guardrail.

    The RAG + LLM decides the issues.
    Python only keeps the final status consistent
    with the structured result.
    """

    if decision.blocking_issues:
        if decision.status == "READY_FOR_PHARMACY":
            decision.status = "PHARMACY_REVIEW"

    else:
        if decision.status == "PHARMACY_REVIEW":
            decision.status = "READY_FOR_PHARMACY"

    return decision


def main():
    args = parse_args()

    model_alias = validate_model_alias(
        args.model or DEFAULT_MODEL
    )

    model = resolve_model(
        model_alias
    )

    image_path = recipe_image_path(
        args.recipe
    )

    recipe = load_json(
        extracted_path(
            image_path
        )
    )

    external_validation = load_json(
        external_validation_path(
            image_path
        )
    )

    prompt = f"""
Eres un asistente administrativo encargado de preparar
una orden de atención para Farmacia.

Tu objetivo NO es realizar una auditoría clínica.

Determina si existe información suficiente para que Farmacia
pueda identificar:

- medicamento;
- concentración;
- presentación;
- cantidad.

Utiliza:

1. la extracción de la receta como fuente primaria;
2. CIMA como fuente externa de corroboración;
3. las políticas institucionales recuperadas mediante File Search.

REGLAS:

- No inventes datos.
- No inventes cantidades.
- No calcules cantidades usando dosis, frecuencia o duración.
- No corrijas automáticamente la receta usando CIMA.
- NOT_CONFIRMED no bloquea automáticamente.
- AMBIGUOUS no bloquea automáticamente.
- API_ERROR no bloquea automáticamente.
- Una discrepancia externa solo debe ser blocking_issue cuando,
  junto con la receta, impide identificar qué producto o cantidad
  debe atender Farmacia.
- Si una discrepancia no impide generar la orden, regístrala como
  non_blocking_issue.
- La ausencia de dosis, frecuencia, duración o instrucciones no
  bloquea por sí sola una orden cuando medicamento, concentración,
  presentación y cantidad son suficientes.
- Conserva en policy y sources las políticas institucionales
  utilizadas.

Estados permitidos:

READY_FOR_PHARMACY
PHARMACY_REVIEW
INSUFFICIENT_INFORMATION

Devuelve exclusivamente PharmacyFulfillmentDecision.


============================================================
EXTRACCIÓN DE LA RECETA
============================================================

{json.dumps(
    recipe,
    indent=2,
    ensure_ascii=False,
)}

============================================================
VALIDACIÓN EXTERNA CIMA
============================================================

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

        text_format=(
            PharmacyFulfillmentDecision
        ),
    )

    decision = response.output_parsed

    decision = normalize_status(
        decision
    )

    print(
        decision.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()