import json
from pathlib import Path
from datetime import datetime

BUSINESS_FILE = Path("business_connections.json")
if not BUSINESS_FILE.exists():
    BUSINESS_FILE.write_text("{}")


def load_connections():
    try:
        return json.loads(BUSINESS_FILE.read_text())
    except Exception:
        return {}


def save_connections(data: dict):
    BUSINESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def is_connected(chat_id: int) -> bool:
    data = load_connections()
    return str(chat_id) in data


def get_connection_entry(chat_id: int) -> dict | None:
    data = load_connections()
    return data.get(str(chat_id))


def get_connection_id(chat_id: int) -> str | None:
    entry = get_connection_entry(chat_id)
    if not entry:
        return None
    return entry.get("business_connection_id")


def add_connection(chat_id: int, business_connection_id: str, added_by: int | None = None):
    data = load_connections()
    data[str(chat_id)] = {
        "business_connection_id": business_connection_id,
        "added_by": added_by,
        "created_at": datetime.utcnow().isoformat()
    }
    save_connections(data)


def remove_connection(chat_id: int):
    data = load_connections()
    if str(chat_id) in data:
        data.pop(str(chat_id))
        save_connections(data)
