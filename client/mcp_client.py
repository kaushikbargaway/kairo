import asyncio
import sys

from mcp import Client, StdioServerParameters


server_params = StdioServerParameters(
    command=sys.executable,
    args=["-m", "servers.notepad.server"]
)


def display_menu():
    print("\n========== NEXORA ==========")
    print("1. Create Note")
    print("2. Read Note")
    print("3. Append Note")
    print("4. List Notes")
    print("5. Search Notes")
    print("6. Delete Note")
    print("7. Exit")
    print("============================")


async def main():

    async with Client(server_params) as client:

        print("\nConnected to NEXORA MCP Server!")

        while True:

            display_menu()

            choice = input("\nChoose an option: ").strip()

            try:

                if choice == "1":

                    filename = input("Enter filename: ").strip()
                    content = input("Enter note content: ")

                    result = await client.call_tool(
                        "create_note",
                        {
                            "filename": filename,
                            "content": content
                        }
                    )

                    print("\n", result.content)

                elif choice == "2":

                    filename = input("Enter filename: ").strip()

                    result = await client.call_tool(
                        "read_note",
                        {"filename": filename}
                    )

                    print("\nNote Content:")
                    print(result.content)

                elif choice == "3":

                    filename = input("Enter filename: ").strip()
                    content = input("Enter additional content: ")

                    result = await client.call_tool(
                        "append_note",
                        {
                            "filename": filename,
                            "content": content
                        }
                    )

                    print("\n", result.content)

                elif choice == "4":

                    result = await client.call_tool("list_notes", {})

                    print("\nAvailable Notes:")
                    print(result.content)

                elif choice == "5":

                    keyword = input("Enter search keyword: ").strip()

                    result = await client.call_tool(
                        "search_notes",
                        {"keyword": keyword}
                    )

                    print("\nSearch Results:")
                    print(result.content)

                elif choice == "6":

                    filename = input("Enter filename to delete: ").strip()

                    confirmation = input(
                        f"Are you sure you want to delete {filename}? (yes/no): "
                    ).strip().lower()

                    if confirmation == "yes":

                        result = await client.call_tool(
                            "delete_note",
                            {"filename": filename}
                        )

                        print("\n", result.content)

                    else:
                        print("\nDeletion cancelled.")

                elif choice == "7":

                    print("\nShutting down NEXORA...")
                    break

                else:

                    print("\nInvalid option. Try again.")

            except Exception as error:

                print(f"\nError: {error}")


if __name__ == "__main__":
    asyncio.run(main())