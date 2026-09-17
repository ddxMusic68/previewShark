from pathlib import Path
import re


VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def is_default_obs_name(stem: str) -> bool:
    if DATE_RE.search(stem):
        return True
    return "(recording)" in stem.lower()


def scan_folder(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    result = []
    try:
        for p in folder.iterdir():
            try:
                if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
                    result.append((p, p.stat().st_mtime))
            except OSError:
                continue
    except OSError:
        pass
    result.sort(key=lambda t: t[1], reverse=True)
    return [p for p, _ in result]


def detect_new_files(folder: Path, previous: set[str]) -> Path | None:
    current = {str(p) for p in scan_folder(folder)}
    new = current - previous
    if not new:
        return None
    candidates = []
    for x in new:
        try:
            candidates.append((Path(x), Path(x).stat().st_mtime))
        except OSError:
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda t: t[1])[0]
