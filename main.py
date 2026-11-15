import asyncio

from ollama_client.client import KairoLLM
from conversation.manager import ConversationManager
from conversation.storage import ConversationStore

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator


def approve_tool_execution(tool_name, arguments):

    if tool_name == "delete_note":
        filename = arguments.get("filename", "unknown file")

        print("\n[KAIRO] Permission required!")
        print(f"[KAIRO] You are about to delete: {filename}")

        confirmation = input("Approve deletion? (yes/no): ").strip().lower()

        return confirmation in ["yes", "y"]

    return True


def display_conversations(store):

    conversations = store.list_conversations()

    print("\n========== Saved Conversations ==========")

    if not conversations:
        print("No previous conversations found.")
    else:
        for index, conversation in enumerate(conversations, start=1):

            print(f"\n{index}. {conversation['title']}")
            print(f"   ID: {conversation['conversation_id']}")
            print(f"   Updated: {conversation['updated_at']}")

    print("\n=========================================\n")


def display_history(conversation):

    history = conversation.get_history()

    print("\n--- Conversation History ---")

    for message in history:

        if message["role"] == "system":
            continue

        role = message["role"].upper()

        if message.get("tool_calls"):

            tool_names = [
                call["function"]["name"]
                for call in message["tool_calls"]
            ]

            print(f"\n{role}: Requested tools {tool_names}")

        else:

            print(f"\n{role}: {message['content']}")

    print("\n----------------------------\n")


async def main():

    # Initialize LLM
    ai = KairoLLM()

    # Initialize MCP Client
    mcp_client = MCPToolClient()

    try:

        # Connect to MCP Server
        await mcp_client.connect()

        # Initialize Agent Orchestrator
        agent = AgentOrchestrator(
            llm=ai,
            mcp_client=mcp_client,
            approval_callback=approve_tool_execution
        )

        # Initialize persistent storage
        store = ConversationStore()

        # Retrieve existing conversations
        saved_conversations = store.list_conversations()

        # Resume the most recently updated conversation
        if saved_conversations:

            latest_conversation = saved_conversations[0]

            conversation = ConversationManager(
                llm=ai,
                agent=agent,
                max_exchanges=10,
                store=store,
                conversation_id=latest_conversation["conversation_id"]
            )

            print(
                f"\n[KAIRO] Resumed conversation: "
                f"{latest_conversation['title']}"
            )

        else:

            # Create the first conversation
            conversation = ConversationManager(
                llm=ai,
                agent=agent,
                max_exchanges=10,
                store=store
            )

            print("\n[KAIRO] Created your first conversation.")

        # Application banner
        print("\n================================")
        print("       KAIRO AI ASSISTANT")
        print("================================")

        print(f"Model: {ai.model}")
        print("Persistent Conversation Storage: Enabled")
        print("MCP Integration: Enabled")

        print("\nAvailable Commands:")
        print("/new             - Start a new conversation")
        print("/reset           - Alias for /new")
        print("/history         - View current conversation history")
        print("/conversations   - List saved conversations")
        print("/resume <id>     - Resume a previous conversation")
        print("/delete <id>     - Delete a saved conversation")
        print("/exit            - Exit KAIRO")

        print("\nKAIRO is ready!\n")

        # Main interaction loop
        while True:

            user_input = input("You: ").strip()

            if not user_input:
                continue

            command = user_input.lower()

            # Exit
            if command == "/exit":

                print("\nKAIRO: Goodbye!")
                break

            # Start a new conversation
            elif command in ["/new", "/reset"]:

                conversation.reset_conversation()

                print("\nKAIRO: New conversation started!\n")
                continue

            # Display current conversation history
            elif command == "/history":

                display_history(conversation)
                continue

            # List saved conversations
            elif command == "/conversations":

                display_conversations(store)
                continue

            # Resume a previous conversation
            elif command.startswith("/resume"):

                parts = user_input.split(maxsplit=1)

                if len(parts) < 2:

                    print("\nUsage: /resume <conversation_id>\n")
                    continue

                conversation_id = parts[1].strip()

                try:

                    conversation = ConversationManager(
                        llm=ai,
                        agent=agent,
                        max_exchanges=10,
                        store=store,
                        conversation_id=conversation_id
                    )

                    print("\nKAIRO: Conversation resumed successfully!\n")

                except KeyError:

                    print("\nKAIRO: Conversation not found.\n")

                continue

            # Delete a saved conversation
            elif command.startswith("/delete"):

                parts = user_input.split(maxsplit=1)

                if len(parts) < 2:
                    print("\nUsage: /delete <conversation_id>\n")
                    continue

                conversation_id = parts[1].strip()

                saved_conversation = store.get_conversation(conversation_id)

                if saved_conversation is None:
                    print("\nKAIRO: Conversation not found.\n")
                    continue

                print(
                    f"\n[KAIRO] You are about to delete: "
                    f"{saved_conversation['title']}"
                )

                confirmation = input(
                    "Are you sure? (yes/no): "
                ).strip().lower()

                if confirmation not in ["yes", "y"]:
                    print("\nKAIRO: Deletion cancelled.\n")
                    continue

                deleted = store.delete_conversation(conversation_id)

                if deleted:

                    # If the active conversation was deleted,
                    # automatically start a new one.
                    if conversation.conversation_id == conversation_id:
                        conversation.reset_conversation()

                    print("\nKAIRO: Conversation deleted successfully.\n")

                else:
                    print("\nKAIRO: Could not delete conversation.\n")

                continue

            # Process normal user messages
            try:

                response = await conversation.send_message(
                    user_input
                )

                print(f"\nKAIRO: {response}\n")

            except Exception as error:

                print(f"\nKAIRO Error: {error}\n")

    except ConnectionError as error:

        print(f"\nKAIRO Error: {error}")
        print("KAIRO could not start because the MCP server is unavailable.")

    finally:

        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())