import pytest

from conversation.manager import ConversationManager
from conversation.storage import ConversationStore


class FakeLLM:
    system_prompt = "You are KAIRO."


class FakeAgent:

    async def process_request(self, messages):

        response = {
            "role": "assistant",
            "content": "Test response"
        }

        messages.append(response)

        return response["content"]


@pytest.fixture
def store(tmp_path):
    return ConversationStore(tmp_path / "kairo.db")


@pytest.fixture
def manager(store):
    return ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent(),
        store=store
    )


@pytest.mark.asyncio
async def test_title_generated_from_first_message(manager, store):

    await manager.send_message(
        "My favourite programming language is Java"
    )

    conversation = store.get_conversation(
        manager.conversation_id
    )

    assert conversation["title"] == (
        "My favourite programming language is Java"
    )


@pytest.mark.asyncio
async def test_title_does_not_change_after_first_message(manager, store):

    await manager.send_message("Learning Python")

    await manager.send_message("Learning Java")

    conversation = store.get_conversation(
        manager.conversation_id
    )

    assert conversation["title"] == "Learning Python"


@pytest.mark.asyncio
async def test_title_is_truncated(manager, store):

    message = "A" * 60

    await manager.send_message(message)

    conversation = store.get_conversation(
        manager.conversation_id
    )

    assert conversation["title"] == ("A" * 45) + "..."
    assert len(conversation["title"]) == 48


def test_generate_title_collapses_whitespace():

    title = ConversationManager._generate_title(
        "Learning    Python\nand    Java"
    )

    assert title == "Learning Python and Java"


def test_update_title_successfully(store):

    conversation_id = store.create_conversation()

    store.update_title(
        conversation_id,
        "Learning Python"
    )

    conversation = store.get_conversation(conversation_id)

    assert conversation["title"] == "Learning Python"


def test_update_title_rejects_empty_title(store):

    conversation_id = store.create_conversation()

    with pytest.raises(ValueError):
        store.update_title(conversation_id, "   ")


def test_update_title_rejects_unknown_conversation(store):

    with pytest.raises(KeyError):
        store.update_title("invalid-id", "Test title")