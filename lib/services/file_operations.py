import shutil
from pathlib import Path
from send2trash import send2trash


def keep_file(path: Path, folder: Path) -> Path:
    keep_dir = folder / "Keep"
    keep_dir.mkdir(exist_ok=True)
    target = keep_dir / path.name
    if target.exists():
        raise FileExistsError(f"File already exists in Keep folder: {target.name}")
    shutil.move(str(path), str(target))
    return target


def delete_file(path: Path) -> None:
    send2trash(str(path))


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
