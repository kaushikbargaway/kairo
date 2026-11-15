import json

import pytest

from servers.notepad import resources, storage


@pytest.fixture
def temporary_notes_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "NOTES_DIR", tmp_path)
    monkeypatch.setattr(storage, "NOTES_DIR", tmp_path)
    return tmp_path


# ==========================================
# NOTES LIST RESOURCE TESTS
# ==========================================

def test_notes_list_when_directory_is_empty(temporary_notes_dir):
    result = resources.notes_list()

    assert json.loads(result) == []


def test_notes_list_returns_sorted_notes(temporary_notes_dir):
    (temporary_notes_dir / "zebra.txt").write_text("Z")
    (temporary_notes_dir / "apple.txt").write_text("A")
    (temporary_notes_dir / "mango.txt").write_text("M")

    result = resources.notes_list()

    assert json.loads(result) == [
        "apple.txt",
        "mango.txt",
        "zebra.txt"
    ]


def test_notes_list_returns_only_txt_files(temporary_notes_dir):
    (temporary_notes_dir / "note.txt").write_text("Text")
    (temporary_notes_dir / "document.pdf").write_text("PDF")
    (temporary_notes_dir / "data.json").write_text("{}")

    result = resources.notes_list()

    assert json.loads(result) == ["note.txt"]


def test_notes_list_skips_directories(temporary_notes_dir):
    (temporary_notes_dir / "folder.txt").mkdir()
    (temporary_notes_dir / "note.txt").write_text("Hello")

    result = resources.notes_list()

    assert json.loads(result) == ["note.txt"]


def test_notes_list_returns_valid_formatted_json(temporary_notes_dir):
    (temporary_notes_dir / "test.txt").write_text("Hello")

    result = resources.notes_list()

    assert result == json.dumps(["test.txt"], indent=2)


# ==========================================
# NOTE CONTENT RESOURCE TESTS
# ==========================================

def test_note_content_successfully(temporary_notes_dir):
    (temporary_notes_dir / "test.txt").write_text(
        "Hello KAIRO",
        encoding="utf-8"
    )

    result = resources.note_content("test.txt")

    assert result == "Hello KAIRO"


def test_note_content_preserves_unicode(temporary_notes_dir):
    content = "Hello! नमस्ते 🚀"

    (temporary_notes_dir / "unicode.txt").write_text(
        content,
        encoding="utf-8"
    )

    result = resources.note_content("unicode.txt")

    assert result == content


def test_note_content_returns_empty_file(temporary_notes_dir):
    (temporary_notes_dir / "empty.txt").write_text(
        "",
        encoding="utf-8"
    )

    result = resources.note_content("empty.txt")

    assert result == ""


def test_note_content_when_file_does_not_exist(temporary_notes_dir):
    with pytest.raises(
        FileNotFoundError,
        match="Note 'missing.txt' does not exist"
    ):
        resources.note_content("missing.txt")


def test_note_content_rejects_invalid_filename(temporary_notes_dir):
    with pytest.raises(ValueError, match="Invalid filename"):
        resources.note_content("../outside.txt")


def test_note_content_rejects_non_txt_extension(temporary_notes_dir):
    with pytest.raises(
        ValueError,
        match="Only .txt files are allowed"
    ):
        resources.note_content("document.pdf")