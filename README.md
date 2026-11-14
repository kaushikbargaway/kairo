# KAIRO

### Kaushik's AI for Interactive Reasoning and Orchestration

**A Personal Desktop AI Assistant powered by Ollama and the Model
Context Protocol (MCP)**

KAIRO is an extensible, locally running AI assistant designed to
understand natural-language requests and interact with external tools
through MCP.

Built with Python, Ollama, and the MCP Python SDK, KAIRO combines local
LLM inference, conversation management, agent orchestration, and an
MCP-based tool execution layer.

> Building an intelligent desktop companion, one capability at a time.

------------------------------------------------------------------------

## Project Overview

KAIRO uses a modular architecture that separates language-model
interaction, conversation management, agent orchestration, MCP client
communication, and MCP server capabilities.

The assistant currently uses **Qwen3 1.7B through Ollama** for local
inference. The `ConversationManager` maintains contextual message
history during an active session, while the `AgentOrchestrator`
discovers MCP tools, makes them available to the LLM, executes requested
tools, and feeds their results back into the conversation.

The current MCP integration includes a Notepad server with tools to
create, read, append, delete, list, and search text notes. It also
exposes MCP resources and prompts.

KAIRO includes tool argument validation, approval before note deletion,
MCP error handling, and automatic reconnection for recoverable
connection failures. Read-only tool calls can be retried after
reconnection. Potentially state-changing operations are not
automatically repeated when their execution status is uncertain.

------------------------------------------------------------------------

## Architecture

``` text
                         USER
                           |
                           v
                  KAIRO CONVERSATIONAL CLI
                           |
                           v
                  CONVERSATION MANAGER
                    Message History
                           |
                           v
                      KAIRO LLM
                        Ollama
                     Qwen3 1.7B
                           |
                           v
                  AGENT ORCHESTRATOR
             Tool Discovery and Execution Loop
                           |
                           v
                     TOOL REGISTRY
                MCP Schemas -> Ollama Tools
                           |
                           v
                     TOOL EXECUTOR
            Validation and Approval Management
                           |
                           v
                      MCP CLIENT
                  STDIO Communication
                           |
                           v
                    NOTEPAD MCP SERVER
                 +---------+---------+
                 |         |         |
               TOOLS   RESOURCES  PROMPTS
                 |         |         |
                 +---------+---------+
                           |
                           v
                     LOCAL NOTES
```

------------------------------------------------------------------------

## Current Features

### 1. Local LLM Integration

-   Local LLM inference through Ollama.
-   Qwen3 1.7B as the default language model.
-   Integration through the Ollama Python SDK.
-   Configurable model selection and generation parameters.
-   No external LLM API required for inference.

### 2. Conversational CLI

-   Interactive terminal-based interface.
-   Natural-language interaction with KAIRO.
-   Custom system prompt defining KAIRO's identity and behaviour.
-   Context-aware responses using conversation history.

**Available commands**

  Command      Description
  ------------ --------------------------------
  `/reset`     Reset the current conversation
  `/history`   Display conversation history
  `/exit`      Exit KAIRO

### 3. Conversation Management

-   Dedicated `ConversationManager`.
-   Maintains message history during an active session.
-   Supports contextual follow-up questions.
-   Configurable conversation history limit.
-   Trims history by complete user exchanges, preserving associated tool
    calls and results.
-   Conversation reset and history inspection.

*Conversation history is currently maintained in memory and is not
persisted across application restarts.*

### 4. Agent Orchestration

-   Discovers available MCP tools at runtime.
-   Converts MCP tool schemas into Ollama-compatible function
    definitions.
-   Supports LLM-driven tool selection and execution.
-   Runs a bounded tool-calling loop for multi-step interactions.
-   Returns tool results to the LLM for further reasoning.
-   Handles MCP tool errors and execution failures.

### 5. MCP Tool Execution and Safety

-   Validates tool arguments against required and supported schema
    properties.
-   Requests user approval before executing `delete_note`.
-   Prevents deletion when approval is unavailable or declined.
-   Distinguishes MCP tool errors using the SDK's `is_error` result
    field.
-   Uses conservative retry behaviour for potentially state-changing
    operations when connection status is uncertain.

### 6. MCP Connection Management

-   Establishes and closes MCP client sessions.
-   Handles MCP server startup failures with a readable error.
-   Detects connection-related failures during tool discovery and
    execution.
-   Attempts to reconnect when the MCP connection is lost.
-   Retries eligible read-only operations once after successful
    reconnection.
-   Avoids automatically repeating write or delete operations when the
    outcome may be uncertain.

### 7. Notepad MCP Server

The Notepad MCP server uses Python and STDIO transport.

  Tool             Description
  ---------------- -------------------------------------------------
  `create_note`    Create a text note
  `read_note`      Read an existing note
  `append_note`    Append content to a note
  `list_notes`     List available notes
  `delete_note`    Delete a note (requires approval through KAIRO)
  `search_notes`   Search across notes

### 8. MCP Resources

-   `notes://list` -- Discover available notes.
-   `note://{filename}` -- Access an individual note's contents.

### 9. MCP Prompts

-   `summarize_note` -- Provides instructions for summarizing a note.
-   `improve_note` -- Provides instructions for improving a note.

------------------------------------------------------------------------

## Technology Stack

  Category                    Technology
  --------------------------- ------------------------------------
  Programming Language        Python
  Local LLM Runtime           Ollama
  Language Model              Qwen3 1.7B
  LLM Integration             Ollama Python SDK
  Agent Architecture          Custom Python agent orchestrator
  Conversation Management     Custom Python module
  Tool Integration Protocol   Model Context Protocol
  MCP SDK                     Python MCP SDK
  Communication Transport     STDIO
  Testing and Inspection      Python test scripts, MCP Inspector
  Version Control             Git and GitHub

------------------------------------------------------------------------

## Project Structure

``` text
kairo/
│
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── tool_executor.py
│   └── tool_registry.py
│
├── client/
│   ├── __init__.py
│   └── mcp_client.py
│
├── conversation/
│   ├── __init__.py
│   └── manager.py
│
├── ollama_client/
│   ├── __init__.py
│   └── client.py
│
├── servers/
│   ├── __init__.py
│   └── notepad/
│       ├── __init__.py
│       ├── app.py
│       ├── server.py
│       ├── storage.py
│       ├── tools.py
│       ├── resources.py
│       └── prompts.py
│
├── notes/
├── tests/
│
├── main.py
├── .gitignore
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## Getting Started

### Prerequisites

-   Python 3.11 or newer
-   Git
-   Ollama

### 1. Clone the Repository

``` bash
git clone https://github.com/kaushikbargaway/kairo.git
cd kairo
```

### 2. Create and Activate a Virtual Environment

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution in the current terminal, you can
run:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

### 3. Install Dependencies

``` powershell
python -m pip install -r requirements.txt
```

### 4. Install Ollama and Pull the Model

Install Ollama from the [official download
page](https://ollama.com/download).

Pull KAIRO's default model:

``` powershell
ollama pull qwen3:1.7b
```

Verify that the model is available:

``` powershell
ollama list
```

Ensure the Ollama service is running before launching KAIRO.

### 5. Launch KAIRO

From the project root, run:

``` powershell
python main.py
```

KAIRO connects to the local Ollama service and launches its Notepad MCP
server through the MCP client using STDIO. **You do not need to start
the Notepad MCP server in a separate terminal.**

------------------------------------------------------------------------

## Testing

Test scripts are kept in the root-level `tests/` directory.

Run a test module from the project root using:

``` powershell
python -m tests.test_reconnect
```

Replace `test_reconnect` with the relevant test module name. Individual
test scripts may have their own setup requirements.

### Testing the MCP Server with MCP Inspector

The Notepad MCP server can also be inspected using the official MCP
Inspector.

``` bash
npx -y @modelcontextprotocol/inspector
```

Configure the server with:

  Setting             Value
  ------------------- -----------------------------------------
  Command             Path to the project's Python executable
  Arguments           `-m servers.notepad.server`
  Working Directory   KAIRO project root

Use the Inspector to explore and test the server's tools, resources, and
prompts.

------------------------------------------------------------------------

## Development Roadmap

### Phase 1: MCP Foundation

-   [x] Initial MCP server implementation
-   [x] Notepad MCP tools
-   [x] MCP resources and resource templates
-   [x] MCP prompts
-   [x] Modular server architecture
-   [x] Custom Python MCP client
-   [x] STDIO client-server communication

### Phase 2: Local AI and Conversation

-   [x] Ollama integration
-   [x] Qwen3 model integration
-   [x] Custom KAIRO system prompt
-   [x] Conversational terminal interface
-   [x] Conversation history and context management
-   [x] Conversation reset functionality
-   [x] Conversation history inspection
-   [ ] Persistent conversational memory

### Phase 3: Intelligent Agent Architecture

-   [x] MCP tool discovery
-   [x] MCP-to-Ollama tool schema conversion
-   [x] LLM-driven tool selection and execution
-   [x] Agent orchestration
-   [x] Multi-step tool-calling loop
-   [x] Tool argument validation
-   [x] Tool execution error handling
-   [x] Approval workflow for note deletion
-   [x] MCP startup failure handling
-   [x] MCP reconnection and read-operation retry
-   [ ] Expanded automated test coverage
-   [ ] More comprehensive retry and recovery tests

### Phase 4: Desktop Capabilities

-   [ ] Filesystem MCP server
-   [ ] File and directory management
-   [ ] Desktop automation
-   [ ] Application interaction
-   [ ] Voice-based interaction
-   [ ] Multi-server MCP architecture

### Phase 5: User Experience and Security

-   [ ] Desktop application interface
-   [ ] Real-time voice interaction
-   [ ] Expanded security and permission management
-   [ ] Logging and monitoring
-   [ ] Persistent memory and user preferences

------------------------------------------------------------------------

## Project Goals

KAIRO aims to evolve into a personal desktop AI ecosystem capable of:

-   Understanding natural-language instructions.
-   Running local language models.
-   Maintaining contextual conversations.
-   Remembering useful information across sessions.
-   Interacting with tools through MCP.
-   Managing files and directories.
-   Automating desktop operations.
-   Supporting voice-based interaction.
-   Integrating multiple MCP servers.
-   Executing complex multi-step tasks.
-   Providing secure, permission-controlled automation.

------------------------------------------------------------------------

## Author

**Kaushik Kumar**

B.E. Information Science and Engineering

GitHub: [@kaushikbargaway](https://github.com/kaushikbargaway)

------------------------------------------------------------------------

*KAIRO is an actively developed personal project. Features and
architecture will evolve as development progresses.*
