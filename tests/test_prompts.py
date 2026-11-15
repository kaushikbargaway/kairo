import pytest

from servers.notepad import prompts


# ==========================================
# SUMMARIZE NOTE PROMPT TESTS
# ==========================================

def test_summarize_note_returns_string():
    result = prompts.summarize_note("Sample note")

    assert isinstance(result, str)


def test_summarize_note_contains_instructions():
    result = prompts.summarize_note("Sample note")

    assert "Summarize the following note" in result
    assert "Main points" in result
    assert "Important information" in result
    assert "Action items" in result


def test_summarize_note_includes_note_content():
    content = "Project deadline is December 15."

    result = prompts.summarize_note(content)

    assert content in result


def test_summarize_note_handles_empty_content():
    result = prompts.summarize_note("")

    assert isinstance(result, str)
    assert "Summarize the following note" in result


# ==========================================
# IMPROVE NOTE PROMPT TESTS
# ==========================================

def test_improve_note_returns_string():
    result = prompts.improve_note("Sample note")

    assert isinstance(result, str)


def test_improve_note_contains_instructions():
    result = prompts.improve_note("Sample note")

    assert "Improve the following note" in result
    assert "Clear" in result
    assert "Grammatically correct" in result
    assert "Well structured" in result
    assert "Concise" in result
    assert "Preserve the original meaning" in result


def test_improve_note_includes_note_content():
    content = "this is an example note"

    result = prompts.improve_note(content)

    assert content in result


def test_improve_note_handles_empty_content():
    result = prompts.improve_note("")

    assert isinstance(result, str)
    assert "Improve the following note" in result


# ==========================================
# SPECIAL INPUT TESTS
# ==========================================

@pytest.mark.parametrize(
    "content",
    [
        "Hello KAIRO!",
        "नमस्ते",
        "Python, Java and C++",
        "Line 1\nLine 2\nLine 3",
        "Special characters: @#$%^&*()"
    ]
)
def test_prompts_preserve_input_content(content):
    summarize_result = prompts.summarize_note(content)
    improve_result = prompts.improve_note(content)

    assert content in summarize_result
    assert content in improve_result