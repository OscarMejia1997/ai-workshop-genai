# Project 2 — OCI Generative AI + LiteLLM

This is a separate project. It does not modify Project 1. It demonstrates how the same recipe workflow can use LiteLLM as a model gateway. The selected logical model is passed once at the beginning and is used by the extraction and pharmacy-decision stages. CIMA remains an external REST integration.

## Sequence

1. Configure the LiteLLM Proxy from `.env`.
2. Start the Proxy.
3. Send a recipe and a logical model to the API.
4. Vision/structured extraction goes through LiteLLM.
5. CIMA validates the extracted medication data.
6. RAG + Pharmacy Decision goes through LiteLLM.

## Dynamic configuration

All deployment-specific values live in `.env`: API key, Project OCID, region, OCI endpoint, Vector Store ID, model IDs, CIMA endpoint, and LiteLLM endpoint/port. `OCI_GENAI_MODELS_JSON` controls the logical model aliases.

## Build the LiteLLM config

```powershell
python .\src\00_generate_litellm_config.py
```

The generated YAML contains environment references for credentials and is not a place to paste secrets.

Start the Proxy using your installed LiteLLM command and the generated `src/litellm_config.yaml`.

## Test from Python

```powershell
python .\src\stages\01_extract_recipe.py recipe_04.png gemini
python .\src\stages\02_validate_cima.py recipe_04.png
python .\src\stages\03_pharmacy_decision.py recipe_04.png gemini
```

## Test from Postman

POST `http://127.0.0.1:<your-api-port>/process-recipe` using `multipart/form-data` with:

- `recipe`: File
- `model`: Text, matching one of the aliases in `OCI_GENAI_MODELS_JSON`

The API returns the selected model and the full pipeline result.
