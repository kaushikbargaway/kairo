from .app import mcp
from .storage import NOTES_DIR, get_note_path


@mcp.tool()
def create_note(filename: str, content: str) -> str:
    """Create a new text note."""

    file_path = get_note_path(filename)

    if file_path.exists():
        return f"Note '{filename}' already exists."

    file_path.write_text(content, encoding="utf-8")

    return f"Successfully created note: {filename}"


@mcp.tool()
def read_note(filename: str) -> str:
    """Read an existing text note."""

    file_path = get_note_path(filename)

    if not file_path.exists():
        return f"Note '{filename}' does not exist."

    return file_path.read_text(encoding="utf-8")


@mcp.tool()
def append_note(filename: str, content: str) -> str:
    """Append content to an existing note."""

    file_path = get_note_path(filename)

    if not file_path.exists():
        return f"Note '{filename}' does not exist."

    with file_path.open("a", encoding="utf-8") as file:
        file.write("\n" + content)

    return f"Successfully updated note: {filename}"


@mcp.tool()
def list_notes() -> list[str]:
    """List all available notes."""

    return sorted(
        file.name
        for file in NOTES_DIR.glob("*.txt")
        if file.is_file()
    )


@mcp.tool()
def delete_note(filename: str) -> str:
    """Delete an existing note."""

    file_path = get_note_path(filename)

    if not file_path.exists():
        return f"Note '{filename}' does not exist."

    file_path.unlink()

    return f"Successfully deleted note: {filename}"


@mcp.tool()
def search_notes(keyword: str) -> list[str]:
    """Search for a keyword across all notes."""

    if not keyword.strip():
        raise ValueError("Search keyword cannot be empty.")

    results = []

    for file_path in NOTES_DIR.glob("*.txt"):

        if not file_path.is_file():
            continue

        content = file_path.read_text(encoding="utf-8")

        if keyword.lower() in content.lower():
            results.append(file_path.name)

    return results