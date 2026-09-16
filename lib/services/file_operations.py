import shutil
from pathlib import Path
from send2trash import send2trash


def delete_file(path: Path) -> None:
    send2trash(str(path))


def save_to_project(path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / path.name
    counter = 1
    while target.exists():
        target = destination / f"{path.stem} ({counter}){path.suffix}"
        counter += 1
    shutil.move(str(path), str(target))
    return target


def rename_file(path: Path, new_stem: str) -> Path:
    invalid = '<>:"/\\|?*'
    if any(c in new_stem for c in invalid):
        raise ValueError(f"Windows filenames cannot contain: {invalid}")
    target = path.with_name(new_stem + path.suffix)
    if target == path:
        return path
    if target.exists():
        raise FileExistsError("A file with that name already exists.")
    path.rename(target)
    return target
