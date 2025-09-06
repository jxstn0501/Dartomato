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
    Calls the ParseExtract API using environment variables:
      - PARSEXTRACT_API_KEY: "Bearer ..." value (without 'Bearer ' prefix is also fine)
      - PARSEXTRACT_URL: full endpoint URL (e.g., https://api.parsextract.com/v1/vision/parse)
      - PARSEXTRACT_EXTRA_PARAMS: optional JSON of additional fields

    If PARSEXTRACT_STUB=1, returns a demo payload without network.
    """
    cfg = load_config()
    if cfg.get("stub") or _bool_env("PARSEXTRACT_STUB", False):
        return {
            "stub": True,
            "engine": "demo",
            "filename": filename,
            "text": "R1: 60 (441)\nR2: 81 (360)\nR3: 45 (315)",
            "tokens": [
                {"round":1,"visit":60,"after":441,"darts":[20,20,20]},
                {"round":2,"visit":81,"after":360,"darts":[25,26,30]},
            ]
        }

    url = cfg.get("parsextract_url") or os.getenv("PARSEXTRACT_URL")
    if not url:
        raise ParseExtractError("PARSEXTRACT_URL is not set. Put it in your .env.")

    api_key = cfg.get("api_key") or os.getenv("PARSEXTRACT_API_KEY")
    if not api_key:
        raise ParseExtractError("PARSEXTRACT_API_KEY is not set. Put it in your .env.")

    # Accept both raw key and "Bearer ..." formats
    if not api_key.lower().startswith("bearer "):
        api_key = f"Bearer {api_key}"

    extra_params: Optional[dict] = None
    if cfg.get("extra_params"):
        extra_params = cfg.get("extra_params")
    elif os.getenv("PARSEXTRACT_EXTRA_PARAMS"):
        try:
            env_val = os.getenv("PARSEXTRACT_EXTRA_PARAMS")
            if env_val:
                extra_params = json.loads(env_val)
        except Exception:
            extra_params = None

    files = {"file": (filename, image_bytes, mime)}
    data = {}
    if isinstance(extra_params, dict):
        # Send as form fields; adjust here if your API expects JSON body instead.
        for k, v in extra_params.items():
            data[k] = v

    headers = {"Authorization": api_key}
    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    except requests.RequestException as e:
        raise ParseExtractError(f"Network error calling ParseExtract: {e}") from e

    if resp.status_code >= 400:
        raise ParseExtractError(f"ParseExtract returned {resp.status_code}: {resp.text[:500]}")

    try:
        return resp.json()
    except Exception:
        # if it's not JSON, return a basic wrapper
        return {"raw": resp.text}
