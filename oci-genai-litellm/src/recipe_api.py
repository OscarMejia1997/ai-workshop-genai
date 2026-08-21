import json
import subprocess
import sys
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

SRC_DIR = PROJECT_ROOT / "src"

RECIPES_DIR = (
    PROJECT_ROOT
    / "data"
    / "recipes"
)

EXTRACTED_DIR = (
    RECIPES_DIR
    / "extracted"
)

STAGES_DIR = (
    SRC_DIR
    / "stages"
)

PYTHON = sys.executable


# ============================================================
# Scripts
# ============================================================

STAGE_01 = (
    STAGES_DIR
    / "01_extract_recipe.py"
)

STAGE_02 = (
    STAGES_DIR
    / "02_validate_cima.py"
)

STAGE_03 = (
    STAGES_DIR
    / "03_pharmacy_decision.py"
)


# ============================================================
# Configuration
# ============================================================

from config import (
    validate_model_alias,
    recipe_image_path,
    extracted_path,
    external_validation_path,
)


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="OCI GenAI + LiteLLM Recipe API",
    description=(
        "API para procesamiento de recetas "
        "utilizando LiteLLM, CIMA y RAG."
    ),
    version="1.0.0",
)


# ============================================================
# Helpers
# ============================================================

def run_stage(
    script: Path,
    recipe_name: str,
    model: str | None = None,
) -> str:

    if not script.exists():
        raise RuntimeError(
            f"Stage not found: {script}"
        )

    command = [
        PYTHON,
        str(script),
        recipe_name,
    ]

    if model:
        command.append(model)

    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="mbcs",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Stage failed: {script.name}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout or ""


def load_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise RuntimeError(
            f"Expected JSON file not found:\n"
            f"{path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}: {exc}"
        ) from exc


def extract_json(
    output: str,
) -> dict:

    """
    Parse the first top-level JSON object printed
    by a stage.

    We use raw_decode starting at the first "{"
    instead of taking the last "{" because the
    response contains nested JSON objects.
    """

    if not output:
        raise RuntimeError(
            "Stage returned no output."
        )

    start = output.find("{")

    if start == -1:
        raise RuntimeError(
            "No JSON object found in stage output."
        )

    decoder = json.JSONDecoder()

    try:
        data, _ = decoder.raw_decode(
            output[start:]
        )
        return data

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse JSON from stage output: "
            f"{exc}\n\n"
            f"Output:\n{output}"
        ) from exc


def get_recipe_paths(
    recipe_name: str,
):

    image_path = recipe_image_path(
        recipe_name
    )

    extraction_path = extracted_path(
        image_path
    )

    validation_path = (
        external_validation_path(
            image_path
        )
    )

    return (
        image_path,
        extraction_path,
        validation_path,
    )


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "OCI GenAI + LiteLLM Recipe API",
    }


# ============================================================
# Full pipeline
# ============================================================

@app.post("/process-recipe")
async def process_recipe(
    recipe: UploadFile = File(...),
    model: str = Form("gemini"),
):

    model = validate_model_alias(
        model
    )

    # --------------------------------------------------------
    # Validate upload
    # --------------------------------------------------------

    if not recipe.filename:
        raise HTTPException(
            status_code=400,
            detail="Recipe filename is required.",
        )

    filename = Path(
        recipe.filename
    ).name

    extension = Path(
        filename
    ).suffix.lower()

    allowed_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use PNG, JPG, JPEG or WEBP."
            ),
        )

    # --------------------------------------------------------
    # Save image
    # --------------------------------------------------------

    RECIPES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_path = (
        RECIPES_DIR
        / filename
    )

    content = await recipe.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    image_path.write_bytes(
        content
    )

    (
        _,
        extraction_path,
        validation_path,
    ) = get_recipe_paths(
        filename
    )

    # --------------------------------------------------------
    # Stage 01 - extraction
    # LiteLLM -> selected model
    # --------------------------------------------------------

    try:

        run_stage(
            STAGE_01,
            filename,
            model,
        )

        extraction = load_json(
            extraction_path
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "stage": "01_extract_recipe",
                "message": str(exc),
            },
        ) from exc

    # --------------------------------------------------------
    # Stage 02 - CIMA
    # No LLM here
    # --------------------------------------------------------

    try:

        run_stage(
            STAGE_02,
            filename,
        )

        external_validation = load_json(
            validation_path
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "stage": "02_validate_cima",
                "message": str(exc),
            },
        ) from exc

    # --------------------------------------------------------
    # Stage 03 - pharmacy decision
    # LiteLLM -> same selected model
    # --------------------------------------------------------

    try:

        decision_output = run_stage(
            STAGE_03,
            filename,
            model,
        )

        decision = extract_json(
            decision_output
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "stage": "03_pharmacy_decision",
                "message": str(exc),
            },
        ) from exc

    # --------------------------------------------------------
    # Validate final decision
    # --------------------------------------------------------

    if "status" not in decision:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "03_pharmacy_decision",
                "message": (
                    "The decision does not contain "
                    "a valid status."
                ),
                "response": decision,
            },
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "recipe": filename,
        "model": model,
        "execution": "full_pipeline",

        "pipeline": {
            "extraction": extraction,
            "external_validation": (
                external_validation
            ),
            "pharmacy_decision": decision,
        },
    }


# ============================================================
# Evaluate existing recipe
# ============================================================

@app.post("/evaluate-recipe")
def evaluate_recipe(
    recipe: str = Form(...),
    model: str = Form("gemini"),
):

    model = validate_model_alias(
        model
    )

    image_path, extraction_path, validation_path = (
        get_recipe_paths(recipe)
    )

    # --------------------------------------------------------
    # Existing artifacts required
    # --------------------------------------------------------

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Recipe image not found: "
                f"{image_path}"
            ),
        )

    if not extraction_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Extraction JSON not found: "
                f"{extraction_path}"
            ),
        )

    if not validation_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"External validation JSON not found: "
                f"{validation_path}"
            ),
        )

    extraction = load_json(
        extraction_path
    )

    external_validation = load_json(
        validation_path
    )

    # --------------------------------------------------------
    # Re-run only decision stage
    # --------------------------------------------------------

    try:

        decision_output = run_stage(
            STAGE_03,
            image_path.name,
            model,
        )

        decision = extract_json(
            decision_output
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "stage": "03_pharmacy_decision",
                "message": str(exc),
            },
        ) from exc

    # --------------------------------------------------------
    # Validate result
    # --------------------------------------------------------

    if "status" not in decision:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "03_pharmacy_decision",
                "message": (
                    "The decision does not contain "
                    "a valid status."
                ),
                "response": decision,
            },
        )

    return {
        "recipe": image_path.name,
        "model": model,
        "execution": "evaluation_only",

        "pipeline": {
            "extraction": extraction,
            "external_validation": (
                external_validation
            ),
            "pharmacy_decision": decision,
        },
    }


# ============================================================
# Local execution
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )