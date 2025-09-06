from typing import Any, Dict, List

def _coerce_bool(v: Any, default: bool=False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("1","true","yes","y","on")
    return default

def _limit_players(names: List[str]) -> List[str]:
    # Multiplayer up to 7 players
    uniq = []
    for n in names:
        n = n.strip()
        if not n: 
            continue
        if n not in uniq:
            uniq.append(n)
        if len(uniq) >= 7:
            break
    if not uniq:
        uniq = ["Player 1"]
    return uniq

def infer_visits_from_text(raw: dict) -> List[dict]:
    """
    Very naive heuristic to demonstrate structure.
    Replace with a proper mapper once your ParseExtract fields are known.
    """
    visits: List[dict] = []
    tokens = raw.get("tokens")
    if isinstance(tokens, list):
        for t in tokens:
            visits.append({
                "round": int(t.get("round", len(visits)+1)),
                "scoreOfVisit": int(t.get("visit", 0)),
                "scoreAfterVisit": int(t.get("after", 0)),
                "dartsThrown": t.get("darts", []),
            })
        return visits

    # fallback: try 'text' lines "R#: 60 (441)"
    text = raw.get("text", "")
    if isinstance(text, str):
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # crude parse
            if ":" in line and "(" in line and ")" in line:
                try:
                    left, rest = line.split(":", 1)
                    visit_str, after_paren = rest.split("(", 1)
                    visit = int("".join(ch for ch in visit_str if ch.isdigit()))
                    after = int("".join(ch for ch in after_paren if ch.isdigit()))
                    visits.append({
                        "round": len(visits)+1,
                        "scoreOfVisit": visit,
                        "scoreAfterVisit": after,
                        "dartsThrown": [],
                    })
                except Exception:
                    continue
    return visits

def normalize_to_dartsmind(raw: Dict[str, Any], player_names: List[str], bust: Any=False, meta: Dict[str, Any]|None=None) -> Dict[str, Any]:
    names = _limit_players(player_names or [])
    bust_flag = _coerce_bool(bust, False)

    visits = infer_visits_from_text(raw)

    # A very basic single-leg skeleton for all players.
    leg = {
        "legNumber": 1,
        "visits": visits,
        # Summary fields can be computed later; keep placeholders here.
        "average": None,
        "checkoutPercent": None,
        "dartsThrown": sum(len(v.get("dartsThrown", [])) or 3 for v in visits) if visits else None,
        "bestVisit": max((v.get("scoreOfVisit", 0) for v in visits), default=None),
    }

    return {
        "players": [
            {
                "playerName": n,
                "bust": bust_flag,
                "legs": [leg],
            } for n in names
        ],
        "meta": meta or {}
    }
