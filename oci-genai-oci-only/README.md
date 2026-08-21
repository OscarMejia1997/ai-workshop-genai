# Project 1 — OCI Generative AI Recipe Processing

This project is the baseline solution. It uses OCI Generative AI directly through the OpenAI-compatible endpoint, adds CIMA external validation, and applies institutional policies through RAG to produce a Pharmacy Fulfillment Decision.

## Sequence

1. Basic Responses API
2. Model switching
3. Multimodal vision
4. Structured output
5. External validation with CIMA
6. RAG + Pharmacy Fulfillment Decision

## Configuration

Copy `.env.example` to `.env` and set all values. No OCI OCID, API key, model identifier, endpoint, or Vector Store ID is stored in Python source.

`OCI_GENAI_MODELS_JSON` is a JSON map of logical names to OCI model identifiers, for example:

```text
OCI_GENAI_DEFAULT_MODEL=gemini
OCI_GENAI_MODELS_JSON={"gemini":"<gemini-model-id>","grok":"<grok-model-id>"}
```

## Run examples

```powershell
python .\src\01_basic\01_hello_response.py
python .\src\02_model_switching\02_hello_response.py grok
python .\src\03_multimodal\03_vision_recipe.py recipe_01.png
python .\src\04_structured_output\05a_structured_recipe_validated.py recipe_04.png
python .\src\05_external_validation\05b_validate_recipe_external.py recipe_04.png
python .\src\06_rag\08_recipe_with_rag.py recipe_04.png
```

Before running the RAG step, upload/sync the three policy files to the Vector Store with `06_upload_knowledge.py`.
