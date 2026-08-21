from pathlib import Path

from config import (
    MODELS,
    REGION,
)


# ============================================================
# Output file
# ============================================================

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "litellm_config.yaml"
)


# ============================================================
# OCI OpenAI-compatible endpoint
# ============================================================

OCI_BASE_URL = (
    f"https://inference.generativeai."
    f"{REGION}.oci.oraclecloud.com/openai/v1"
)


# ============================================================
# Generate LiteLLM configuration
# ============================================================

lines = [
    "model_list:",
]


for alias, model_id in MODELS.items():

    lines.extend(
        [
            f"  - model_name: {alias}",
            "    litellm_params:",
            f"      model: openai/{model_id}",
            f"      api_base: {OCI_BASE_URL}",
            "      api_key: os.environ/OCI_GENAI_API_KEY",
            "      extra_headers:",
            "        OpenAI-Project: "
            "os.environ/OCI_GENAI_PROJECT_ID",
            "",
        ]
    )


yaml_content = "\n".join(
    lines
)


# ============================================================
# Write configuration
# ============================================================

OUTPUT_FILE.write_text(
    yaml_content,
    encoding="utf-8",
)


# ============================================================
# Result
# ============================================================

print(
    f"Generated: {OUTPUT_FILE}"
)

for alias in MODELS:
    print(
        f"  - {alias}"
    )