from pathlib import Path

from mcp.server import MCPServer


# Initialize MCP Server
mcp = MCPServer("nexora-notepad")

# Define the notes directory
NOTES_DIR = Path(__file__).resolve().parent.parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)


def get_note_path(filename: str) -> Path:
    """Validate filename and return its path."""

    if not filename.endswith(".txt"):
        raise ValueError("Only .txt files are allowed.")

    if Path(filename).name != filename:
        raise ValueError("Invalid filename.")

    return NOTES_DIR / filename


@mcp.tool()
def create_note(filename: str, content: str) -> str:
    """Create a new text note with the provided content."""

    file_path = get_note_path(filename)

    if file_path.exists():
        return f"Note '{filename}' already exists."

    file_path.write_text(content, encoding="utf-8")

    return f"Successfully created note: {filename}"


@mcp.tool()
def read_note(filename: str) -> str:
    """Read the contents of an existing text note."""

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

    return [
        file.name
        for file in NOTES_DIR.glob("*.txt")
        if file.is_file()
    ]


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

    results = []

    for file_path in NOTES_DIR.glob("*.txt"):
        if not file_path.is_file():
            continue

        content = file_path.read_text(encoding="utf-8")

        if keyword.lower() in content.lower():
            results.append(file_path.name)

    return results


if __name__ == "__main__":
    mcp.run()