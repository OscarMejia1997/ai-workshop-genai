import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import argparse
import json
import unicodedata
import requests

from config import (
    CIMA_BASE_URL,
    CIMA_MAX_RESULTS,
    CIMA_MAX_TO_EVALUATE,
    extracted_path,
    external_validation_path,
    recipe_image_path,
)


def norm(value):
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(c for c in value if not unicodedata.combining(c))


def search(name):
    r = requests.get(f"{CIMA_BASE_URL}/medicamentos", params={"nombre": name}, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else data.get("resultados", [])


def detail(nregistro):
    r = requests.get(f"{CIMA_BASE_URL}/medicamento", params={"nregistro": nregistro}, timeout=20)
    r.raise_for_status()
    return r.json()


def candidate(data):
    form = data.get("formaFarmaceutica") or data.get("formaFarmaceuticaSimplificada")
    if isinstance(form, dict):
        form = form.get("nombre")
    return {
        "nregistro": data.get("nregistro"),
        "name": data.get("nombre"),
        "active_ingredients": [x.get("nombre") for x in data.get("principiosActivos", []) if x.get("nombre")],
        "dose": data.get("dosis"),
        "pharmaceutical_form": form,
    }


def validate_medication(med):
    name = med.get("name")
    base = {
        "extracted_name": name,
        "extracted_concentration": med.get("concentration"),
        "extracted_pharmaceutical_form": med.get("pharmaceutical_form"),
        "extracted_quantity": med.get("prescribed_quantity"),
        "candidate_count": 0,
        "candidates": [],
        "validation_status": "NOT_CONFIRMED",
        "review_required": False,
        "review_reason": None,
    }
    if not name:
        base["review_reason"] = "No se pudo extraer el nombre del medicamento."
        return base
    try:
        results = search(name)[:CIMA_MAX_TO_EVALUATE]
        candidates = []
        for item in results:
            if not item.get("nregistro"):
                continue
            try:
                candidates.append(candidate(detail(str(item["nregistro"]))))
            except requests.RequestException:
                continue
        ranked = []
        for c in candidates:
            nmatch = norm(name) in [norm(x) for x in c.get("active_ingredients", [])]
            dmatch = None if not med.get("concentration") or not c.get("dose") else norm(med["concentration"]).replace(" ", "") == norm(c["dose"]).replace(" ", "")
            fmatch = None if not med.get("pharmaceutical_form") or not c.get("pharmaceutical_form") else norm(med["pharmaceutical_form"]) in norm(c["pharmaceutical_form"])
            compatible = nmatch and dmatch is not False and fmatch is not False
            score = (100 if nmatch else 0) + (30 if dmatch is True else 0) + (20 if fmatch is True else 0)
            ranked.append((compatible, score, c))
        ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
        compatible = [x[2] for x in ranked if x[0]]
        if len(compatible) == 1:
            base["candidate_count"] = 1
            base["candidates"] = compatible[:1]
            base["validation_status"] = "CONFIRMED"
            return base
        if len(compatible) > 1:
            base["candidate_count"] = min(len(compatible), CIMA_MAX_RESULTS)
            base["candidates"] = compatible[:CIMA_MAX_RESULTS]
            base["validation_status"] = "AMBIGUOUS"
            base["review_reason"] = "CIMA encontró múltiples candidatos compatibles."
            return base
        base["candidate_count"] = min(len(ranked), CIMA_MAX_RESULTS)
        base["candidates"] = [x[2] for x in ranked[:CIMA_MAX_RESULTS]]
        base["review_reason"] = "CIMA devolvió candidatos relacionados, pero no pudo corroborar todos los atributos."
        return base
    except requests.RequestException as exc:
        base["validation_status"] = "API_ERROR"
        base["review_reason"] = f"No fue posible consultar CIMA: {exc}"
        return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe")
    args = parser.parse_args()
    image = recipe_image_path(args.recipe)
    source = extracted_path(image)
    output = external_validation_path(image)
    recipe = json.loads(source.read_text(encoding="utf-8"))
    validations = [validate_medication(m) for m in recipe.get("medications", []) if m.get("name")]
    statuses = {x["validation_status"] for x in validations}
    overall = "API_ERROR" if "API_ERROR" in statuses else "AMBIGUOUS" if "AMBIGUOUS" in statuses else "NOT_CONFIRMED" if "NOT_CONFIRMED" in statuses else "CONFIRMED"
    result = {"recipe_id": recipe.get("recipe_id"), "medications": validations, "overall_status": overall}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
