import json
import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = PROJECT_ROOT / "data"

RECIPES_DIR = (
    DATA_DIR
    / "recipes"
)

EXTRACTED_DIR = (
    RECIPES_DIR
    / "extracted"
)

KNOWLEDGE_DIR = (
    DATA_DIR
    / "knowledge"
)


# ============================================================
# Environment
# ============================================================

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def require_env(
    name: str,
) -> str:

    value = os.getenv(name)

    if not value:

        raise RuntimeError(
            f"Missing environment variable: {name}\n"
            f"Check your .env file: {ENV_FILE}"
        )

    return value


# ============================================================
# OCI Generative AI
# ============================================================

API_KEY = require_env(
    "OCI_GENAI_API_KEY"
)

PROJECT_ID = require_env(
    "OCI_GENAI_PROJECT_ID"
)

REGION = require_env(
    "OCI_GENAI_REGION"
)

VECTOR_STORE_ID = require_env(
    "OCI_GENAI_VECTOR_STORE_ID"
)


# ============================================================
# Model configuration
# ============================================================

MODELS_JSON = require_env(
    "OCI_GENAI_MODELS_JSON"
)

try:

    MODELS = json.loads(
        MODELS_JSON
    )

except json.JSONDecodeError as exc:

    raise RuntimeError(
        "OCI_GENAI_MODELS_JSON is not valid JSON.\n"
        'Example: {"gemini":"google.gemini-2.5-flash",'
        '"grok":"xai.grok-4.3"}'
    ) from exc


if not isinstance(MODELS, dict):

    raise RuntimeError(
        "OCI_GENAI_MODELS_JSON must contain "
        "a JSON object."
    )


if not MODELS:

    raise RuntimeError(
        "OCI_GENAI_MODELS_JSON cannot be empty."
    )


DEFAULT_MODEL = os.getenv(
    "OCI_GENAI_DEFAULT_MODEL",
    next(iter(MODELS)),
)


# ============================================================
# Model alias validation
# ============================================================

def validate_model_alias(
    alias: str | None,
) -> str:

    """
    Validate and normalize a logical model alias.

    Example:

        gemini -> gemini
        grok   -> grok

    The actual OCI model ID is resolved separately.
    """

    if alias is None:
        alias = DEFAULT_MODEL

    normalized = alias.strip().lower()

    if normalized not in MODELS:

        available = ", ".join(
            sorted(MODELS.keys())
        )

        raise ValueError(
            f"Unknown model alias '{alias}'. "
            f"Available models: {available}"
        )

    return normalized


def resolve_model(
    alias: str | None,
) -> str:

    """
    Resolve a logical alias to the actual OCI model ID.

    Example:

        gemini -> google.gemini-2.5-flash

        grok -> xai.grok-4.3
    """

    model_alias = validate_model_alias(
        alias
    )

    return MODELS[
        model_alias
    ]


# ============================================================
# LiteLLM Proxy
# ============================================================

LITELLM_PROXY_URL = os.getenv(
    "LITELLM_PROXY_URL",
    "http://localhost:4000",
).rstrip("/")


LITELLM_PROXY_PORT = int(
    os.getenv(
        "LITELLM_PROXY_PORT",
        "4000",
    )
)


LITELLM_PROXY_API_KEY = os.getenv(
    "LITELLM_PROXY_API_KEY",
    "anything",
)


LITELLM_DEFAULT_MODEL = os.getenv(
    "LITELLM_DEFAULT_MODEL",
    DEFAULT_MODEL,
)


# ============================================================
# CIMA
# ============================================================

CIMA_BASE_URL = os.getenv(
    "CIMA_BASE_URL",
    "https://cima.aemps.es/cima/rest",
).rstrip("/")


CIMA_MAX_RESULTS = int(
    os.getenv(
        "CIMA_MAX_RESULTS",
        "2",
    )
)


CIMA_MAX_TO_EVALUATE = int(
    os.getenv(
        "CIMA_MAX_TO_EVALUATE",
        "4",
    )
)


# ============================================================
# Recipe paths
# ============================================================

def recipe_image_path(
    recipe_name: str,
) -> Path:

    return (
        RECIPES_DIR
        / Path(recipe_name).name
    )


def extracted_path(
    image_path: Path,
) -> Path:

    return (
        EXTRACTED_DIR
        / f"{image_path.stem}_extracted.json"
    )


def external_validation_path(
    image_path: Path,
) -> Path:

    return (
        EXTRACTED_DIR
        / (
            f"{image_path.stem}"
            "_external_validation.json"
        )
    )