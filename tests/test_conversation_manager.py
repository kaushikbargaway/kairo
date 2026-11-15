import pytest

from conversation.manager import ConversationManager


# --------------------------------------------------
# MOCK CLASSES
# --------------------------------------------------

class FakeLLM:

    def __init__(self):
        self.system_prompt = "You are KAIRO."


class FakeAgent:

    def __init__(self):
        self.call_count = 0

    async def process_request(self, messages):
        self.call_count += 1

        messages.append({
            "role": "assistant",
            "content": "Hello! How can I help?"
        })

        return "Hello! How can I help?"


# --------------------------------------------------
# 1. INITIALIZATION
# --------------------------------------------------

def test_conversation_manager_initialization():

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent()
    )

    assert manager.messages == [
        {
            "role": "system",
            "content": "You are KAIRO."
        }
    ]

    assert manager.max_exchanges == 10


# --------------------------------------------------
# 2. SUCCESSFUL MESSAGE HANDLING
# --------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_successfully():

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent()
    )

    response = await manager.send_message("Hello KAIRO!")

    assert response == "Hello! How can I help?"

    assert manager.agent.call_count == 1

    assert manager.messages[1] == {
        "role": "user",
        "content": "Hello KAIRO!"
    }

    assert manager.messages[2] == {
        "role": "assistant",
        "content": "Hello! How can I help?"
    }


# --------------------------------------------------
# 3. ROLLBACK ON FAILURE
# --------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_rolls_back_on_failure():

    class FailingAgent:

        async def process_request(self, messages):
            messages.append({
                "role": "assistant",
                "content": "Incomplete response"
            })

            raise RuntimeError("Agent execution failed")

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FailingAgent()
    )

    original_history = manager.get_history()

    with pytest.raises(RuntimeError, match="Agent execution failed"):
        await manager.send_message("Hello KAIRO!")

    assert manager.messages == original_history


# --------------------------------------------------
# 4. HISTORY TRIMMING
# --------------------------------------------------

def test_history_trimming():

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent(),
        max_exchanges=2
    )

    manager.messages.extend([
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},

        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},

        {"role": "user", "content": "Message 3"},
        {"role": "assistant", "content": "Response 3"}
    ])

    manager._trim_history()

    assert len(manager.messages) == 5

    assert manager.messages[0]["role"] == "system"

    assert manager.messages[1]["content"] == "Message 2"
    assert manager.messages[2]["content"] == "Response 2"

    assert manager.messages[3]["content"] == "Message 3"
    assert manager.messages[4]["content"] == "Response 3"


# --------------------------------------------------
# 5. RESET CONVERSATION
# --------------------------------------------------

def test_reset_conversation():

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent()
    )

    manager.messages.extend([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ])

    manager.reset_conversation()

    assert manager.messages == [
        {
            "role": "system",
            "content": "You are KAIRO."
        }
    ]


# --------------------------------------------------
# 6. GET CONVERSATION HISTORY
# --------------------------------------------------

def test_get_history():

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent()
    )

    manager.messages.extend([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ])

    history = manager.get_history()

    assert history == manager.messages

    assert history is not manager.messages


# --------------------------------------------------
# 7. HISTORY DEEP COPY PROTECTION
# --------------------------------------------------

def test_get_history_returns_independent_copy():

    manager = ConversationManager(
        llm=FakeLLM(),
        agent=FakeAgent()
    )

    manager.messages.append({
        "role": "user",
        "content": "Original message"
    })

    history = manager.get_history()

    history.append({
        "role": "user",
        "content": "Injected message"
    })

    history[1]["content"] = "Modified message"

    assert len(manager.messages) == 2

    assert manager.messages[1]["content"] == "Original message"