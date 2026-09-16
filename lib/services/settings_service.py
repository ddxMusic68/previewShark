import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "settings.json"


def _read() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_folder() -> Path:
    folder = _read().get("folder")
    if folder:
        return Path(folder)
    return Path.home() / "Videos"


def save_folder(path: Path) -> None:
    data = _read()
    data["folder"] = str(path)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)