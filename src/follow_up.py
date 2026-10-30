import json
from pathlib import Path

FOLLOW_UP_FILE = Path(__file__).parent.parent / "data" / "demo" / "follow_up_actions.json"


def load_actions():
    """
    Loads saved follow-up actions.
    If the file does not exist or is invalid, returns an empty dictionary.
    """
    if not FOLLOW_UP_FILE.exists():
        return {}
    try:
        with open(FOLLOW_UP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_action(student_id: str, action_type: str, note: str, recorded_by: str = None):
    """
    Saves a follow-up action for a given student ID.
    Persists data into data/demo/follow_up_actions.json.
    """
    actions = load_actions()
    record = {
        "action_type": action_type,
        "note": note,
    }
    if recorded_by:
        record["recorded_by"] = recorded_by

    actions[student_id] = record

    FOLLOW_UP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FOLLOW_UP_FILE, "w", encoding="utf-8") as f:
        json.dump(actions, f, indent=2, ensure_ascii=False)
    return actions
