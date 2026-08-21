from openai import OpenAI

from config import (
    LITELLM_PROXY_API_KEY,
    LITELLM_PROXY_URL,
)


# ============================================================
# LiteLLM Proxy client
# ============================================================

client = OpenAI(
    base_url=(
        f"{LITELLM_PROXY_URL}/v1"
    ),
    api_key=LITELLM_PROXY_API_KEY,
)