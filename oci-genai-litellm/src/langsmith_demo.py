import sys
from pathlib import Path

from langsmith import traceable


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_DIR),
    )


from client import client

from config import (
    DEFAULT_MODEL,
    validate_model_alias,
)


# ============================================================
# Traced LLM call
# ============================================================

@traceable(
    name="recipe-llm-call",
    metadata={
        "application": "recipe-processing",
        "environment": "workshop",
    },
)
def run_model(
    model: str,
    prompt: str,
):

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    return {
        "model": model,
        "output": response.output_text,
    }


# ============================================================
# Main
# ============================================================

def main():

    model = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_MODEL
    )

    model = validate_model_alias(
        model
    )

    prompt = """
Explica en una frase cuál es la función
de OCI Generative AI en este workshop.
"""

    result = run_model(
        model=model,
        prompt=prompt,
    )

    print()
    print(
        "=========================================="
    )
    print(
        "LANGSMITH DEMO"
    )
    print(
        "=========================================="
    )
    print(
        f"Model: {result['model']}"
    )
    print()
    print(
        result["output"]
    )


if __name__ == "__main__":
    main()