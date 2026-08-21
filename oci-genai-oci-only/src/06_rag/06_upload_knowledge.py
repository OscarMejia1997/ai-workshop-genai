import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pathlib import Path

from client import client
from config import KNOWLEDGE_DIR, VECTOR_STORE_ID

FILES = [KNOWLEDGE_DIR / "politica_datos_receta.md", KNOWLEDGE_DIR / "politica_procesamiento_recetas.md", KNOWLEDGE_DIR / "politica_revision_humana.md"]

for path in FILES:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("rb") as file:
        uploaded = client.files.create(file=file, purpose="assistants")
    client.vector_stores.files.create(vector_store_id=VECTOR_STORE_ID, file_id=uploaded.id)
    print(f"Uploaded and attached: {path.name}")

print("Knowledge base synchronization completed.")
