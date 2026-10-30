import json
from datetime import datetime
from pathlib import Path

FOLLOW_UP_FILE = Path(__file__).parent.parent / "data" / "demo" / "follow_up_actions.json"


def load_actions():
    """
    Returns {student_id: [entry, ...]} with every logged action in order.
    Older single-record files are upgraded on read.
    """
    if not FOLLOW_UP_FILE.exists():
        return {}
    try:
        with open(FOLLOW_UP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}

    normalised = {}
    for sid, value in data.items():
        if isinstance(value, list):
            normalised[sid] = [v for v in value if isinstance(v, dict)]
        elif isinstance(value, dict):
            normalised[sid] = [value]
    return normalised


def save_action(student_id: str, action_type: str, note: str, recorded_by: str = None):
    """Appends a timestamped action to the student's history."""
    actions = load_actions()
    entry = {
        "action_type": action_type,
        "note": note,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    if recorded_by:
        entry["recorded_by"] = recorded_by
    actions.setdefault(student_id, []).append(entry)

    FOLLOW_UP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FOLLOW_UP_FILE, "w", encoding="utf-8") as f:
        json.dump(actions, f, indent=2, ensure_ascii=False)
    return actions


def flatten_actions(actions):
    """Flat list of rows, newest first."""
    rows = []
    for sid, entries in actions.items():
        for e in entries:
            rows.append({"student_id": sid, **e})
    rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return rows