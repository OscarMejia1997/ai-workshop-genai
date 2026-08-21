import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import json
from pathlib import Path

from config import BASE_URL, MODEL_ALIASES

OUTPUT = Path(__file__).resolve().parent / "litellm_config.yaml"

lines = ["model_list:"]
for alias, model_id in MODEL_ALIASES.items():
    lines.extend([
        f"  - model_name: {alias}",
        "    litellm_params:",
        f"      model: openai/{model_id}",
        f"      api_base: {BASE_URL}",
        "      api_key: os.environ/OCI_GENAI_API_KEY",
        "      extra_headers:",
        "        OpenAI-Project: os.environ/OCI_GENAI_PROJECT_ID",
        "",
    ])

OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated: {OUTPUT}")
for alias in MODEL_ALIASES:
    print(f"  - {alias}")
