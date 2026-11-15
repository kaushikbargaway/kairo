import pytest

from conversation.manager import ConversationManager
from conversation.storage import ConversationStore


class FakeLLM:
    system_prompt = "You are KAIRO."


class FakeAgent:

    async def process_request(self, messages):
        response = {
            "role": "assistant",
            "content": f"Response to: {messages[-1]['content']}"
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


def test_manager_creates_new_conversation(manager, store):
    assert manager.conversation_id is not None

    conversation = store.get_conversation(
        manager.conversation_id
    )

    assert conversation is not None


@pytest.mark.asyncio
async def test_message_is_persisted(manager, store):
    await manager.send_message("Hello KAIRO")

    saved_messages = store.load_messages(
        manager.conversation_id
    )

    assert len(saved_messages) == 2
    assert saved_messages[0]["content"] == "Hello KAIRO"
    assert saved_messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_system_prompt_is_not_persisted(manager, store):
    await manager.send_message("Hello")

    saved_messages = store.load_messages(
        manager.conversation_id
    )

    assert all(
        message["role"] != "system"
        for message in saved_messages
    )


@pytest.mark.asyncio
async def test_conversation_can_be_restored(store, manager):
    await manager.send_message("Remember this message")

    conversation_id = manager.conversation_id

    restored_manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent(),
        store=store,
        conversation_id=conversation_id
    )

    history = restored_manager.get_history()

    assert history[0]["role"] == "system"
    assert history[1]["content"] == "Remember this message"
    assert history[2]["role"] == "assistant"


@pytest.mark.asyncio
async def test_restored_conversation_can_continue(store, manager):
    await manager.send_message("First message")

    conversation_id = manager.conversation_id

    restored_manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent(),
        store=store,
        conversation_id=conversation_id
    )

    await restored_manager.send_message("Second message")

    history = store.load_messages(conversation_id)

    assert len(history) == 4
    assert history[2]["content"] == "Second message"


def test_reset_starts_new_conversation(manager, store):
    old_id = manager.conversation_id

    manager.reset_conversation()

    new_id = manager.conversation_id

    assert new_id != old_id
    assert manager.get_history() == [
        {"role": "system", "content": "You are KAIRO."}
    ]

    assert store.get_conversation(old_id) is not None
    assert store.get_conversation(new_id) is not None


@pytest.mark.asyncio
async def test_reset_preserves_previous_messages(manager, store):
    await manager.send_message("Previous conversation")

    old_id = manager.conversation_id

    manager.reset_conversation()

    old_messages = store.load_messages(old_id)

    assert len(old_messages) == 2
    assert old_messages[0]["content"] == "Previous conversation"


def test_loading_nonexistent_conversation_raises_error(store):
    with pytest.raises(KeyError, match="Conversation not found"):
        ConversationManager(
            llm=FakeLLM(),
            agent=FakeAgent(),
            store=store,
            conversation_id="invalid-id"
        )


def test_manager_without_store_remains_compatible():
    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent()
    )

    assert manager.store is None
    assert manager.conversation_id is None