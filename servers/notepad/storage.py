from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parents[2] / "notes"

NOTES_DIR.mkdir(parents=True, exist_ok=True)


def get_note_path(filename: str) -> Path:
    """Validate filename and return its path."""

    if not filename or Path(filename).name != filename:
        raise ValueError("Invalid filename.")

    if not filename.endswith(".txt"):
        raise ValueError("Only .txt files are allowed.")

    return NOTES_DIR / filename