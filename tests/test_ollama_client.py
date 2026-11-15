from unittest.mock import MagicMock, patch

import pytest

from ollama_client.client import KairoLLM


@pytest.fixture
def mock_ollama_client():
    with patch("ollama_client.client.Client") as mock_client:
        yield mock_client


def test_initialization_with_default_model(mock_ollama_client):
    llm = KairoLLM()

    assert llm.model == "qwen3:1.7b"

    mock_ollama_client.assert_called_once_with(
        host="http://localhost:11434"
    )


def test_initialization_with_custom_model(mock_ollama_client):
    llm = KairoLLM(model="qwen3:4b")

    assert llm.model == "qwen3:4b"

    mock_ollama_client.assert_called_once_with(
        host="http://localhost:11434"
    )


def test_system_prompt_is_initialized(mock_ollama_client):
    llm = KairoLLM()

    assert "KAIRO" in llm.system_prompt
    assert "Model Context Protocol" in llm.system_prompt


def test_generate_response_successfully(mock_ollama_client):
    mock_client_instance = mock_ollama_client.return_value

    expected_message = MagicMock()
    mock_client_instance.chat.return_value.message = expected_message

    llm = KairoLLM()

    messages = [
        {"role": "user", "content": "Hello KAIRO"}
    ]

    result = llm.generate_response(messages)

    assert result == expected_message

    mock_client_instance.chat.assert_called_once_with(
        model="qwen3:1.7b",
        messages=messages,
        tools=[],
        think=False,
        options={
            "temperature": 0.7,
            "num_predict": 512
        }
    )


def test_generate_response_with_tools(mock_ollama_client):
    mock_client_instance = mock_ollama_client.return_value
    mock_client_instance.chat.return_value.message = MagicMock()

    llm = KairoLLM()

    messages = [
        {"role": "user", "content": "Create a note"}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "create_note"
            }
        }
    ]

    llm.generate_response(messages, tools=tools)

    mock_client_instance.chat.assert_called_once_with(
        model="qwen3:1.7b",
        messages=messages,
        tools=tools,
        think=False,
        options={
            "temperature": 0.7,
            "num_predict": 512
        }
    )


def test_generate_response_with_empty_tools(mock_ollama_client):
    mock_client_instance = mock_ollama_client.return_value
    mock_client_instance.chat.return_value.message = MagicMock()

    llm = KairoLLM()

    messages = [
        {"role": "user", "content": "Hello"}
    ]

    llm.generate_response(messages, tools=[])

    assert mock_client_instance.chat.call_args.kwargs["tools"] == []


def test_generate_response_propagates_api_exception(mock_ollama_client):
    mock_client_instance = mock_ollama_client.return_value

    mock_client_instance.chat.side_effect = ConnectionError(
        "Ollama server is unavailable"
    )

    llm = KairoLLM()

    messages = [
        {"role": "user", "content": "Hello"}
    ]

    with pytest.raises(ConnectionError, match="Ollama server is unavailable"):
        llm.generate_response(messages)