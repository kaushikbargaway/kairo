from pathlib import Path

import pytest

from servers.notepad import storage


@pytest.fixture
def temporary_notes_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "NOTES_DIR", tmp_path)
    return tmp_path


def test_get_note_path_successfully(temporary_notes_dir):
    result = storage.get_note_path("test.txt")

    assert result == temporary_notes_dir / "test.txt"


def test_get_note_path_with_different_filename(temporary_notes_dir):
    result = storage.get_note_path("meeting_notes.txt")

    assert result == temporary_notes_dir / "meeting_notes.txt"


def test_get_note_path_rejects_empty_filename():
    with pytest.raises(ValueError, match="Invalid filename"):
        storage.get_note_path("")


def test_get_note_path_rejects_path_traversal():
    with pytest.raises(ValueError, match="Invalid filename"):
        storage.get_note_path("../outside.txt")


def test_get_note_path_rejects_nested_path():
    nested_filename = str(Path("folder") / "note.txt")

    with pytest.raises(ValueError, match="Invalid filename"):
        storage.get_note_path(nested_filename)


def test_get_note_path_rejects_absolute_path(tmp_path):
    absolute_filename = str(tmp_path / "outside.txt")

    with pytest.raises(ValueError, match="Invalid filename"):
        storage.get_note_path(absolute_filename)


def test_get_note_path_rejects_non_txt_extension():
    with pytest.raises(ValueError, match="Only .txt files are allowed"):
        storage.get_note_path("notes.pdf")


def test_get_note_path_rejects_missing_extension():
    with pytest.raises(ValueError, match="Only .txt files are allowed"):
        storage.get_note_path("notes")


def test_get_note_path_rejects_uppercase_extension():
    with pytest.raises(ValueError, match="Only .txt files are allowed"):
        storage.get_note_path("notes.TXT")


def test_get_note_path_rejects_other_extensions():
    with pytest.raises(ValueError, match="Only .txt files are allowed"):
        storage.get_note_path("notes.json")