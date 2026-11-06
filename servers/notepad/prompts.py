from .app import mcp


@mcp.prompt()
def summarize_note(note_content: str) -> str:
    """Generate instructions to summarize a note."""

    return f"""
    Summarize the following note.

    Highlight:
    1. Main points
    2. Important information
    3. Action items

    Note:

    {note_content}
    """


@mcp.prompt()
def improve_note(note_content: str) -> str:
    """Generate instructions to improve a note."""

    return f"""
    Improve the following note.

    Make it:
    - Clear
    - Grammatically correct
    - Well structured
    - Concise

    Preserve the original meaning.

    Note:

    {note_content}
    """