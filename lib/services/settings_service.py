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


def _write(data: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_path(key: str, default: Path) -> Path:
    value = _read().get(key)
    return Path(value) if value else default


def load_folder() -> Path:
    return _load_path("folder", Path.home() / "Videos")


def save_folder(path: Path) -> None:
    data = _read()
    data["folder"] = str(path)
    _write(data)


def load_projects_folder() -> Path:
    return _load_path("projects_folder", Path.home() / "Projects")


def save_projects_folder(path: Path) -> None:
    data = _read()
    data["projects_folder"] = str(path)
    _write(data)