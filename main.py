import asyncio

from ollama_client.client import KairoLLM
from conversation.manager import ConversationManager
from conversation.storage import ConversationStore

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator

from memory.store import MemoryStore
from memory.manager import MemoryManager
from memory.models import MemoryCategory


def approve_tool_execution(tool_name, arguments):

    if tool_name == "delete_note":
        filename = arguments.get("filename", "unknown file")

        print("\n[KAIRO] Permission required!")
        print(f"[KAIRO] You are about to delete: {filename}")

        confirmation = input(
            "Approve deletion? (yes/no): "
        ).strip().lower()

        return confirmation in ["yes", "y"]

    return True


def display_conversations(store):

    conversations = store.list_conversations()

    print("\n========== Saved Conversations ==========")

    if not conversations:
        print("No previous conversations found.")

    else:
        for index, conversation in enumerate(
            conversations,
            start=1
        ):

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


def display_memory(memory):

    print(f"\nID: {memory.memory_id}")
    print(f"Category: {memory.category.value}")
    print(f"Importance: {memory.importance:.2f}")
    print(f"Confidence: {memory.confidence:.2f}")
    print(f"Created: {memory.created_at}")
    print(f"Content: {memory.content}")


def display_memory_list(memories):

    print("\n========== Long-Term Memories ==========")

    if not memories:
        print("No memories found.")

    else:
        for index, memory in enumerate(memories, start=1):

            print(f"\n{index}. {memory.content}")
            print(f"   ID: {memory.memory_id}")
            print(f"   Category: {memory.category.value}")
            print(f"   Importance: {memory.importance:.2f}")

    print("\n========================================\n")


def display_memory_overview(memory_manager):

    memories = memory_manager.get_all_memories()

    print("\n========== KAIRO Memory ==========")

    print(f"Total memories: {len(memories)}")

    print("\nMemories by category:")

    for category in MemoryCategory:

        count = len(
            memory_manager.search_by_category(category)
        )

        print(f"  {category.value.capitalize():15} : {count}")

    print("\n==================================\n")

    print("Available memory commands:")
    print("/memory list")
    print("/memory search <query>")
    print("/memory category <name>")
    print("/memory delete <id>")
    print("/memory stats\n")


def display_memory_stats(memory_manager):

    memories = memory_manager.get_all_memories()

    print("\n========== Memory Statistics ==========")

    print(f"Total memories: {len(memories)}")

    if memories:

        average_importance = sum(
            memory.importance
            for memory in memories
        ) / len(memories)

        average_confidence = sum(
            memory.confidence
            for memory in memories
        ) / len(memories)

        print(f"Average importance: {average_importance:.2f}")
        print(f"Average confidence: {average_confidence:.2f}")

    print("\nCategory distribution:")

    for category in MemoryCategory:

        count = len(
            memory_manager.search_by_category(category)
        )

        print(f"{category.value.capitalize():15}: {count}")

    print("\n========================================\n")


def handle_memory_command(user_input, memory_manager):

    parts = user_input.split(maxsplit=2)

    if len(parts) == 1:

        display_memory_overview(memory_manager)
        return

    subcommand = parts[1].lower()

    # Display all memories
    if subcommand == "list":

        memories = memory_manager.get_all_memories()

        display_memory_list(memories)

    # Semantic memory search
    elif subcommand == "search":

        if len(parts) < 3:

            print("\nUsage: /memory search <query>\n")
            return

        query = parts[2]

        results = memory_manager.recall(
            query=query,
            top_k=10
        )

        print("\n========== Memory Search Results ==========")

        if not results:

            print("No relevant memories found.")

        else:

            for index, result in enumerate(results, start=1):

                memory = result["memory"]
                similarity = result["similarity"]

                print(f"\n{index}. {memory.content}")
                print(f"   ID: {memory.memory_id}")
                print(f"   Category: {memory.category.value}")
                print(f"   Similarity: {similarity:.4f}")

        print("\n============================================\n")

    # Filter memories by category
    elif subcommand == "category":

        if len(parts) < 3:

            print("\nAvailable categories:")

            for category in MemoryCategory:
                print(f"- {category.value}")

            print("\nUsage: /memory category <name>\n")
            return

        category_name = parts[2].strip().lower()

        try:

            category = MemoryCategory(category_name)

        except ValueError:

            print(f"\nInvalid category: {category_name}")

            print("\nAvailable categories:")

            for category in MemoryCategory:
                print(f"- {category.value}")

            print()
            return

        memories = memory_manager.search_by_category(category)

        display_memory_list(memories)

    # Delete a memory
    elif subcommand == "delete":

        if len(parts) < 3:

            print("\nUsage: /memory delete <memory_id>\n")
            return

        memory_id = parts[2].strip()

        memory = memory_manager.get_memory(memory_id)

        if memory is None:

            print("\nKAIRO: Memory not found.\n")
            return

        print("\nYou are about to delete this memory:")
        display_memory(memory)

        confirmation = input(
            "\nAre you sure? (yes/no): "
        ).strip().lower()

        if confirmation not in ["yes", "y"]:

            print("\nKAIRO: Memory deletion cancelled.\n")
            return

        deleted = memory_manager.delete_memory(memory_id)

        if deleted:

            print("\nKAIRO: Memory deleted successfully.\n")

        else:

            print("\nKAIRO: Could not delete memory.\n")

    # Memory statistics
    elif subcommand == "stats":

        display_memory_stats(memory_manager)

    else:

        print("\nUnknown memory command.")
        print("\nAvailable commands:")
        print("/memory")
        print("/memory list")
        print("/memory search <query>")
        print("/memory category <name>")
        print("/memory delete <id>")
        print("/memory stats\n")


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

        # Initialize persistent conversation storage
        store = ConversationStore()

        # Initialize persistent memory storage
        memory_store = MemoryStore(
            db_path=store.db_path
        )

        # Initialize memory manager
        memory_manager = MemoryManager(
            llm=ai,
            store=memory_store
        )

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
                conversation_id=latest_conversation["conversation_id"],
                memory_manager=memory_manager
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
                store=store,
                memory_manager=memory_manager
            )

            print("\n[KAIRO] Created your first conversation.")

        # Application banner
        print("\n================================")
        print("       KAIRO AI ASSISTANT")
        print("================================")

        print(f"Model: {ai.model}")
        print("Persistent Conversation Storage: Enabled")
        print("Long-Term Memory: Enabled")
        print("MCP Integration: Enabled")

        print("\nAvailable Commands:")
        print("/new                  - Start a new conversation")
        print("/reset                - Alias for /new")
        print("/history              - View current conversation history")
        print("/conversations        - List saved conversations")
        print("/resume <id>          - Resume a previous conversation")
        print("/delete <id>          - Delete a saved conversation")
        print("/memory               - Memory overview")
        print("/memory list          - List all memories")
        print("/memory search <query>- Search memories")
        print("/memory category <name> - Filter by category")
        print("/memory delete <id>   - Delete a memory")
        print("/memory stats         - Memory statistics")
        print("/exit                 - Exit KAIRO")

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

            # Memory management
            elif command == "/memory" or command.startswith("/memory "):

                try:

                    handle_memory_command(
                        user_input,
                        memory_manager
                    )

                except Exception as error:

                    print(f"\nKAIRO Memory Error: {error}\n")

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
                        conversation_id=conversation_id,
                        memory_manager=memory_manager
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

                saved_conversation = store.get_conversation(
                    conversation_id
                )

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

                deleted = store.delete_conversation(
                    conversation_id
                )

                if deleted:

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