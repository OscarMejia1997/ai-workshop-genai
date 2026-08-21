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
    sys.path.insert(
        0,
        str(SRC_DIR),
    )


# ============================================================
# Shared modules
# ============================================================

from client import client

from config import (
    VECTOR_STORE_ID,
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
            "Generate the pharmacy fulfillment decision "
            "using LiteLLM and institutional RAG."
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
        help=(
            "Model alias configured in .env. "
            "Example: gemini or grok."
        ),
    )

    return parser.parse_args()


# ============================================================
# Load JSON
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            f"JSON file not found:\n{path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}:\n{exc}"
        ) from exc


# ============================================================
# Main
# ============================================================

def main():

    args = parse_args()

    model_alias = validate_model_alias(
        args.model
    )

    image_path = recipe_image_path(
        args.recipe
    )

    extraction_path = extracted_path(
        image_path
    )

    validation_path = (
        external_validation_path(
            image_path
        )
    )

    # --------------------------------------------------------
    # Validate required artifacts
    # --------------------------------------------------------

    if not extraction_path.exists():
        raise FileNotFoundError(
            f"Extraction JSON not found:\n"
            f"{extraction_path}\n\n"
            "Run stage 01 first."
        )

    if not validation_path.exists():
        raise FileNotFoundError(
            f"External validation JSON not found:\n"
            f"{validation_path}\n\n"
            "Run stage 02 first."
        )

    # --------------------------------------------------------
    # Load extraction
    # --------------------------------------------------------

    extraction = load_json(
        extraction_path
    )

    # --------------------------------------------------------
    # Load CIMA validation
    # --------------------------------------------------------

    external_validation = load_json(
        validation_path
    )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = f"""
Eres un asistente administrativo encargado de preparar
una orden de atención para Farmacia.

Tu objetivo NO es realizar una auditoría clínica.

Tu objetivo es determinar si la receta contiene suficiente
información para que Farmacia pueda identificar y atender:

- medicamento;
- concentración;
- presentación;
- cantidad.

============================================================
JERARQUÍA DE FUENTES
============================================================

FUENTE 1 - EXTRACCIÓN DE LA RECETA
Es la fuente primaria para construir la orden.

FUENTE 2 - CIMA
Es una fuente externa de corroboración.
No debe utilizarse para corregir automáticamente la receta.

FUENTE 3 - KNOWLEDGE BASE
Las políticas institucionales recuperadas mediante File Search
son la autoridad para decidir si una discrepancia bloquea o no
la atención.

============================================================
REGLAS DE NEGOCIO
============================================================

1. La información de order_items debe provenir de la receta
   extraída.

2. No inventes medicamentos.

3. No inventes cantidades.

4. No calcules cantidades a partir de dosis, frecuencia o duración.

5. No corrijas automáticamente nombres de medicamentos,
   concentraciones o presentaciones utilizando CIMA.

6. NOT_CONFIRMED no bloquea automáticamente.

7. AMBIGUOUS no bloquea automáticamente.

8. API_ERROR no bloquea automáticamente.

9. Una discrepancia externa solo debe convertirse en
   blocking_issue cuando, junto con la información extraída
   de la receta, impida identificar suficientemente qué
   producto o cantidad debe atender Farmacia.

10. La ausencia de dose_per_administration, frequency,
    duration o instructions NO bloquea por sí sola una orden
    de Farmacia cuando medicamento, concentración, presentación
    y cantidad ya son suficientes para identificar la orden.

11. Campos administrativos del profesional que no sean
    necesarios para identificar qué debe dispensar Farmacia
    no deben bloquear la orden.

12. Cuando una discrepancia de CIMA no bloquea, debe registrarse
    como non_blocking_issue.

============================================================
DECISIÓN
============================================================

Usa:

READY_FOR_PHARMACY
cuando la receta permite identificar suficientemente la orden.

PHARMACY_REVIEW
cuando existe información parcial o ambigua que requiere
intervención humana antes de atender la orden.

INSUFFICIENT_INFORMATION
cuando la propia receta no contiene información suficiente
para identificar qué medicamento o cantidad debe atender Farmacia.

============================================================
TRAZABILIDAD
============================================================

La respuesta debe conservar la trazabilidad de la decisión.

En "sources" incluye únicamente las fuentes efectivamente
utilizadas:

- "EXTRACCIÓN DE LA RECETA"
- "CIMA"
- "politica_procesamiento_recetas.md"
- "politica_datos_receta.md"
- "politica_revision_humana.md"

Cuando un issue sea consecuencia de una política institucional,
indica en "policy" el nombre de la política correspondiente.

No inventes una política que no haya sido recuperada.

============================================================
EXTRACCIÓN DE LA RECETA
============================================================

{json.dumps(
    extraction,
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

============================================================
RESPUESTA
============================================================

Devuelve exclusivamente un objeto válido de:

PharmacyFulfillmentDecision
"""

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    print()
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

    # --------------------------------------------------------
    # LiteLLM + File Search
    # --------------------------------------------------------

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

        text_format=(
            PharmacyFulfillmentDecision
        ),
    )

    # --------------------------------------------------------
    # Structured result
    # --------------------------------------------------------

    decision = response.output_parsed

    # --------------------------------------------------------
    # Ensure extraction/CIMA sources are visible
    # --------------------------------------------------------

    sources = list(
        decision.sources or []
    )

    if "EXTRACCIÓN DE LA RECETA" not in sources:
        sources.insert(
            0,
            "EXTRACCIÓN DE LA RECETA",
        )

    if "CIMA" not in sources:
        sources.insert(
            1,
            "CIMA",
        )

    decision.sources = sources

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    print(
        decision.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()