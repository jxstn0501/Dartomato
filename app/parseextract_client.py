import os
import json
import requests
from typing import Any, Dict, Optional
from .config_store import load_config

class ParseExtractError(RuntimeError):
    pass

def _bool_env(name: str, default: bool=False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1","true","yes","y","on")

def call_parseextract(image_bytes: bytes, filename: str, mime: str="image/jpeg") -> Dict[str, Any]:
    """
    Calls the ParseExtract API using the new data-extract endpoint with clean output processing.
    """
    cfg = load_config()
    if cfg.get("stub") or _bool_env("PARSEXTRACT_STUB", False):
        return {
            "stub": True,
            "engine": "demo",
            "filename": filename,
            "data": {
                "rounds": [
                    {"round": 1, "visit": 60, "after": 441, "darts": [20, 20, 20]},
                    {"round": 2, "visit": 81, "after": 360, "darts": [25, 26, 30]},
                    {"round": 3, "visit": 45, "after": 315, "darts": [15, 15, 15]}
                ],
                "players": ["Player 1"],
                "scores": [441, 360, 315]
            }
        }

    api_key = cfg.get("api_key") or os.getenv("PARSEXTRACT_API_KEY")
    if not api_key:
        raise ParseExtractError("Kein API Key gesetzt.")
    
    if not api_key.lower().startswith("bearer "):
        api_key = f"Bearer {api_key}"

    url = cfg.get("parsextract_url") or os.getenv("PARSEXTRACT_URL") or "https://api.parseextract.com/v1/data-extract"
    
    # Get extraction prompt with schema
    prompt = cfg.get("prompt") or os.getenv("PARSEXTRACT_PROMPT") or '''Extract dart game data with this JSON schema:
{
  "rounds": [{"round": number, "visit": number, "after": number, "darts": [number, number, number]}],
  "players": ["player_name"],
  "scores": [number]
}'''

    headers = {"Authorization": api_key}
    files = {"file": (filename, image_bytes, mime)}
    data = {"prompt": prompt}
    
    # Add any extra parameters from config
    extra_params = cfg.get("extra_params")
    if isinstance(extra_params, dict):
        for k, v in extra_params.items():
            data[k] = v

    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        resp.raise_for_status()
        out = resp.json()
        
        # ---- Clean Output ----
        for key in ["output", "text", "data", "result", "extracted_data"]:  # mögliche Felder
            if key in out and isinstance(out[key], str):
                try:
                    parsed = json.loads(out[key])
                    out[key] = parsed  # ersetzt String durch echtes Objekt
                except Exception:
                    # wenn nicht parsebar → nur \n entfernen
                    out[key] = out[key].replace("\\n", " ").strip()
        
        return out
        
    except requests.RequestException as e:
        raise ParseExtractError(f"Network error calling ParseExtract: {e}") from e
    except requests.HTTPError as e:
        raise ParseExtractError(f"ParseExtract returned error: {e}") from e
    except Exception as e:
        raise ParseExtractError(f"Error processing ParseExtract response: {e}") from e
