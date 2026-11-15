import pytest

from servers.notepad import tools, storage


@pytest.fixture
def temporary_notes_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "NOTES_DIR", tmp_path)
    monkeypatch.setattr(tools, "NOTES_DIR", tmp_path)
    return tmp_path


# ==========================================
# CREATE NOTE TESTS
# ==========================================

def test_create_note_successfully(temporary_notes_dir):
    result = tools.create_note("test.txt", "Hello KAIRO")

    assert result == "Successfully created note: test.txt"
    assert (temporary_notes_dir / "test.txt").read_text(
        encoding="utf-8"
    ) == "Hello KAIRO"


def test_create_note_already_exists(temporary_notes_dir):
    note = temporary_notes_dir / "test.txt"
    note.write_text("Existing content", encoding="utf-8")

    result = tools.create_note("test.txt", "New content")

    assert result == "Note 'test.txt' already exists."
    assert note.read_text(encoding="utf-8") == "Existing content"


def test_create_note_rejects_invalid_filename(temporary_notes_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        tools.create_note("../outside.txt", "Hello")


# ==========================================
# READ NOTE TESTS
# ==========================================

def test_read_note_successfully(temporary_notes_dir):
    note = temporary_notes_dir / "test.txt"
    note.write_text("Hello KAIRO", encoding="utf-8")

    result = tools.read_note("test.txt")

    assert result == "Hello KAIRO"


def test_read_note_when_file_does_not_exist(temporary_notes_dir):
    result = tools.read_note("missing.txt")

    assert result == "Note 'missing.txt' does not exist."


def test_read_note_rejects_invalid_filename(temporary_notes_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        tools.read_note("../outside.txt")


# ==========================================
# APPEND NOTE TESTS
# ==========================================

def test_append_note_successfully(temporary_notes_dir):
    note = temporary_notes_dir / "test.txt"
    note.write_text("Hello", encoding="utf-8")

    result = tools.append_note("test.txt", "KAIRO")

    assert result == "Successfully updated note: test.txt"
    assert note.read_text(encoding="utf-8") == "Hello\nKAIRO"


def test_append_note_when_file_does_not_exist(temporary_notes_dir):
    result = tools.append_note("missing.txt", "New content")

    assert result == "Note 'missing.txt' does not exist."


# ==========================================
# LIST NOTES TESTS
# ==========================================

def test_list_notes_successfully(temporary_notes_dir):
    (temporary_notes_dir / "zebra.txt").write_text("Z")
    (temporary_notes_dir / "apple.txt").write_text("A")
    (temporary_notes_dir / "mango.txt").write_text("M")

    result = tools.list_notes()

    assert result == [
        "apple.txt",
        "mango.txt",
        "zebra.txt"
    ]


def test_list_notes_returns_only_txt_files(temporary_notes_dir):
    (temporary_notes_dir / "note.txt").write_text("Text")
    (temporary_notes_dir / "document.pdf").write_text("PDF")
    (temporary_notes_dir / "data.json").write_text("{}")

    result = tools.list_notes()

    assert result == ["note.txt"]


def test_list_notes_skips_directories(temporary_notes_dir):
    (temporary_notes_dir / "folder.txt").mkdir()
    (temporary_notes_dir / "note.txt").write_text("Hello")

    result = tools.list_notes()

    assert result == ["note.txt"]


def test_list_notes_when_directory_is_empty(temporary_notes_dir):
    result = tools.list_notes()

    assert result == []


# ==========================================
# DELETE NOTE TESTS
# ==========================================

def test_delete_note_successfully(temporary_notes_dir):
    note = temporary_notes_dir / "test.txt"
    note.write_text("Delete me", encoding="utf-8")

    result = tools.delete_note("test.txt")

    assert result == "Successfully deleted note: test.txt"
    assert not note.exists()


def test_delete_note_when_file_does_not_exist(temporary_notes_dir):
    result = tools.delete_note("missing.txt")

    assert result == "Note 'missing.txt' does not exist."


# ==========================================
# SEARCH NOTE TESTS
# ==========================================

def test_search_notes_successfully(temporary_notes_dir):
    (temporary_notes_dir / "first.txt").write_text(
        "Python programming",
        encoding="utf-8"
    )

    (temporary_notes_dir / "second.txt").write_text(
        "Java programming",
        encoding="utf-8"
    )

    (temporary_notes_dir / "third.txt").write_text(
        "Database management",
        encoding="utf-8"
    )

    result = tools.search_notes("programming")

    assert set(result) == {"first.txt", "second.txt"}
    assert len(result) == 2


def test_search_notes_is_case_insensitive(temporary_notes_dir):
    (temporary_notes_dir / "test.txt").write_text(
        "Hello KAIRO",
        encoding="utf-8"
    )

    result = tools.search_notes("kairo")

    assert result == ["test.txt"]


def test_search_notes_returns_empty_list_when_no_match(
    temporary_notes_dir
):
    (temporary_notes_dir / "test.txt").write_text(
        "Hello world",
        encoding="utf-8"
    )

    result = tools.search_notes("Python")

    assert result == []


def test_search_notes_rejects_empty_keyword():
    with pytest.raises(
        ValueError,
        match="Search keyword cannot be empty"
    ):
        tools.search_notes("")


def test_search_notes_rejects_whitespace_keyword():
    with pytest.raises(
        ValueError,
        match="Search keyword cannot be empty"
    ):
        tools.search_notes("   ")


def test_search_notes_skips_directories(temporary_notes_dir):
    folder = temporary_notes_dir / "folder.txt"
    folder.mkdir()

    (temporary_notes_dir / "note.txt").write_text(
        "Python programming",
        encoding="utf-8"
    )

    result = tools.search_notes("Python")

    assert result == ["note.txt"]