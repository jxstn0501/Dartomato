import json
from typing import List, Optional, Any, Dict
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .storage import init_db, insert_ingest, list_ingests, get_ingest, delete_ingest
from .parseextract_client import call_parseextract, ParseExtractError
from .normalizer import normalize_to_dartsmind
from .config_store import load_config, save_config

app = FastAPI(title="DartsMind Test Backend", version="0.2.0")

# Allow localhost dev tools by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve minimal web UI
BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / 'web'
app.mount('/static', StaticFiles(directory=str(WEB_DIR)), name='static')

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/")
def index():
    index_file = WEB_DIR / 'index.html'
    if not index_file.exists():
        return {"hint":"UI nicht gefunden. Lade das ZIP vollständig hoch."}
    return FileResponse(str(index_file))

@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Config endpoints ----
class ConfigIn(BaseModel):
    parsextract_url: Optional[str] = None
    api_key: Optional[str] = None
    extra_params: Optional[dict] = None
    stub: Optional[bool] = None

@app.get('/config')
def get_config():
    return load_config()

@app.post('/config')
def set_config(cfg: ConfigIn):
    data = load_config()
    inc = cfg.model_dump(exclude_unset=True)
    for k, v in inc.items():
        data[k] = v
    return save_config(data)

# ---- Ingest listing ----
class IngestOut(BaseModel):
    id: int
    created_at: str
    filename: str
    player_names: List[str]
    bust: bool

@app.get("/ingests", response_model=List[IngestOut])
def api_list_ingests(limit: int = 50):
    return list_ingests(limit=limit)

@app.get("/ingests/{ingest_id}")
def api_get_ingest(ingest_id: int):
    item = get_ingest(ingest_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@app.delete("/ingests/{ingest_id}")
def api_delete_ingest(ingest_id: int):
    ok = delete_ingest(ingest_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}

# ---- Upload ----
@app.post("/upload")
async def upload_image(
    image: UploadFile = File(...),
    player_names: Optional[str] = Form(None, description="Comma separated up to 7 players"),
    bust: Optional[str] = Form("false"),
    meta: Optional[str] = Form(None, description="JSON string, optional"),
):
    # Parse form fields
    players: List[str] = []
    if player_names:
        players = [p.strip() for p in player_names.split(",") if p.strip()]
    bust_flag = str(bust).lower() in ("1","true","yes","y","on")

    meta_dict: Dict[str, Any] = {}
    if meta:
        try:
            meta_dict = json.loads(meta)
        except Exception:
            pass

    # Read file
    contents = await image.read()
    filename = image.filename or "image.jpg"
    mime = image.content_type or "image/jpeg"

    # Call ParseExtract
    try:
        raw = call_parseextract(contents, filename, mime=mime)
    except ParseExtractError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Normalize
    normalized = normalize_to_dartsmind(raw, players, bust_flag, meta=meta_dict)

    # Persist
    new_id = insert_ingest(filename, players, bust_flag, meta_dict, raw, normalized)

    return {
        "id": new_id,
        "filename": filename,
        "raw": raw,
        "normalized": normalized,
    }
