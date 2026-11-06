import json

from .app import mcp
from .storage import NOTES_DIR, get_note_path


@mcp.resource("notes://list")
def notes_list() -> str:
    """Provide a list of all available notes."""

    notes = sorted(
        file.name
        for file in NOTES_DIR.glob("*.txt")
        if file.is_file()
    )

    return json.dumps(notes, indent=2)


@mcp.resource("note://{filename}")
def note_content(filename: str) -> str:
    """Provide the contents of a specific note."""

    file_path = get_note_path(filename)

    if not file_path.exists():
        raise FileNotFoundError(f"Note '{filename}' does not exist.")

    return file_path.read_text(encoding="utf-8")