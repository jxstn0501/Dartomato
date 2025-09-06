import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULTS = {
    "parsextract_url": None,
    "api_key": None,
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
