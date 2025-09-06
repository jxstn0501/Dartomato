import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULTS = {
    "parsextract_url": "https://api.parseextract.com/v1/data-extract",
    "api_key": None,
    "prompt": "Extract all dart game scores, player names, and round information from this image. Format as JSON with fields: rounds, scores, players.",
    "extra_params": {},   # dict
    "stub": False
}

def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return {**DEFAULTS, **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}
        except Exception:
            return DEFAULTS.copy()
    return DEFAULTS.copy()

def save_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    data = {**DEFAULTS, **(cfg or {})}
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
