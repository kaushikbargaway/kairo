import json

import pytest

from conversation.storage import ConversationStore


@pytest.fixture
def store(tmp_path):

    database_path = tmp_path / "test_kairo.db"

    return ConversationStore(database_path)


def test_database_initialization(store):

    with store._connection() as connection:

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    table_names = [row["name"] for row in tables]

    assert "conversations" in table_names
    assert "messages" in table_names


def test_create_conversation(store):

    conversation_id = store.create_conversation()

    conversation = store.get_conversation(
        conversation_id
    )

    assert conversation is not None

    assert conversation["conversation_id"] == conversation_id

    assert conversation["title"] == "New conversation"

    assert conversation["created_at"] is not None
    assert conversation["updated_at"] is not None


def test_create_conversation_with_custom_title(store):

    conversation_id = store.create_conversation(
        "Learning Python"
    )

    conversation = store.get_conversation(
        conversation_id
    )

    assert conversation["title"] == "Learning Python"


def test_save_and_load_messages(store):

    conversation_id = store.create_conversation()

    messages = [
        {
            "role": "user",
            "content": "Hello KAIRO!"
        },
        {
            "role": "assistant",
            "content": "Hello! How can I help?"
        }
    ]

    store.save_messages(
        conversation_id,
        messages
    )

    loaded_messages = store.load_messages(
        conversation_id
    )

    assert loaded_messages == messages


def test_preserve_tool_calls_and_metadata(store):

    conversation_id = store.create_conversation()

    messages = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "read_note",
                        "arguments": {
                            "filename": "test.txt"
                        }
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_name": "read_note",
            "content": "Note contents"
        }
    ]

    store.save_messages(
        conversation_id,
        messages
    )

    assert store.load_messages(
        conversation_id
    ) == messages


def test_preserve_unicode_messages(store):

    conversation_id = store.create_conversation()

    messages = [
        {
            "role": "user",
            "content": "नमस्ते KAIRO! 🚀"
        }
    ]

    store.save_messages(
        conversation_id,
        messages
    )

    assert store.load_messages(
        conversation_id
    ) == messages


def test_save_messages_replaces_previous_history(store):

    conversation_id = store.create_conversation()

    store.save_messages(
        conversation_id,
        [
            {"role": "user", "content": "Old message"}
        ]
    )

    updated_messages = [
        {"role": "user", "content": "New message"}
    ]

    store.save_messages(
        conversation_id,
        updated_messages
    )

    assert store.load_messages(
        conversation_id
    ) == updated_messages


def test_save_empty_messages(store):

    conversation_id = store.create_conversation()

    store.save_messages(
        conversation_id,
        [
            {"role": "user", "content": "Hello"}
        ]
    )

    store.save_messages(
        conversation_id,
        []
    )

    assert store.load_messages(
        conversation_id
    ) == []


def test_reject_invalid_messages(store):

    conversation_id = store.create_conversation()

    original_messages = [
        {"role": "user", "content": "Original"}
    ]

    store.save_messages(
        conversation_id,
        original_messages
    )

    with pytest.raises(
        ValueError,
        match="dictionary"
    ):
        store.save_messages(
            conversation_id,
            ["invalid message"]
        )

    assert store.load_messages(
        conversation_id
    ) == original_messages


def test_reject_non_list_messages(store):

    conversation_id = store.create_conversation()

    with pytest.raises(
        ValueError,
        match="list"
    ):
        store.save_messages(
            conversation_id,
            {"role": "user"}
        )


def test_unknown_conversation_raises_error(store):

    with pytest.raises(
        KeyError,
        match="Conversation not found"
    ):
        store.save_messages(
            "unknown-id",
            []
        )


def test_list_conversations(store):

    first_id = store.create_conversation("First")
    second_id = store.create_conversation("Second")

    conversations = store.list_conversations()

    conversation_ids = [
        conversation["conversation_id"]
        for conversation in conversations
    ]

    assert len(conversations) == 2

    assert first_id in conversation_ids
    assert second_id in conversation_ids


def test_delete_conversation(store):

    conversation_id = store.create_conversation()

    assert store.delete_conversation(
        conversation_id
    ) is True

    assert store.get_conversation(
        conversation_id
    ) is None


def test_delete_conversation_cascades_messages(store):

    conversation_id = store.create_conversation()

    store.save_messages(
        conversation_id,
        [
            {"role": "user", "content": "Hello"}
        ]
    )

    store.delete_conversation(conversation_id)

    assert store.load_messages(
        conversation_id
    ) == []


def test_delete_nonexistent_conversation(store):

    assert store.delete_conversation(
        "unknown-id"
    ) is False