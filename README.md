# KAIRO

### Kaushik's AI for Interactive Reasoning and Orchestration

**A personal desktop AI assistant powered by Ollama and the Model
Context Protocol (MCP).**

KAIRO is an extensible, locally running AI assistant that understands
natural-language requests and interacts with external tools through MCP.
It combines local LLM inference, conversation management, agent
orchestration, and MCP-based tool execution.

> Building an intelligent desktop companion, one capability at a time.

------------------------------------------------------------------------

## Project Overview

KAIRO uses a modular architecture that separates language-model
interaction, conversation management, agent orchestration, MCP client
communication, and MCP server capabilities.

The current implementation uses **Qwen3 1.7B through Ollama** for local
inference. The `ConversationManager` maintains contextual message
history and integrates with a SQLite-backed `ConversationStore` to
persist conversations across application restarts. KAIRO can restore the
most recently updated conversation, start new conversations, list saved
conversations, resume a conversation by ID, and delete a conversation
with user confirmation.

The `AgentOrchestrator` discovers MCP tools, exposes them to the LLM,
executes requested tools, and returns their results to the conversation.

The current MCP integration includes a Notepad server with six tools,
two resources, and two prompts. KAIRO also includes argument validation,
approval before note deletion, error handling, automatic reconnection,
and controlled retry behaviour.

### Current Test Status

The full automated test suite has passed during v0.2.0 development. The
two optional Ollama integration tests are skipped by default. They
require the `KAIRO_RUN_OLLAMA_INTEGRATION=1` environment variable and a
running local Ollama instance.

Run the coverage command in the [Testing](#testing) section to generate
the current local coverage report.

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
             Argument Validation and Approval
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

### Recovery flow

KAIRO detects recoverable MCP connection failures during tool discovery
and execution. It attempts to reconnect to the server and retries
eligible read-only operations once. Operations that may modify data are
not automatically repeated when their execution status is uncertain.

The recovery tests include termination of the actual MCP server
subprocess and verification that the Orchestrator reconnects, starts a
replacement process, retries a read-only operation, and completes the
request.

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

  Command            Description
  ------------------ -----------------------------------------------------
  `/new`             Start a new conversation
  `/reset`           Alias for `/new`
  `/history`         Display the current conversation history
  `/conversations`   List saved conversations
  `/resume <id>`     Resume a saved conversation by ID
  `/delete <id>`     Delete a saved conversation (confirmation required)
  `/exit`            Exit KAIRO

### 3. Conversation Management

-   Dedicated `ConversationManager`.
-   Maintains message history and supports contextual follow-up
    questions.
-   Configurable conversation history limit.
-   Trims history by complete user exchanges, preserving associated tool
    calls and results.
-   Rolls back newly appended messages if request processing fails.
-   Starts new conversations without deleting previous conversations.
-   Automatically generates a title from the first user message.
-   Supports listing, resuming, and deleting saved conversations.
-   Automatically resumes the most recently updated conversation on
    application startup.

### 4. Persistent Conversation Storage

-   SQLite-backed `ConversationStore`.
-   Persists conversation metadata and message history across restarts.
-   Stores message payloads as JSON, preserving tool calls and metadata.
-   Reconstructs the system prompt when a conversation is restored
    rather than storing it in the conversation transcript.
-   Deletes associated messages when a conversation is deleted.
-   Keeps the local database under `data/`, which is excluded from Git.

> This feature persists conversation transcripts. Semantic long-term
> memory, automatic fact extraction, and user-preference memory are
> separate future capabilities.

### 5. Agent Orchestration

-   Discovers available MCP tools at runtime.
-   Converts MCP tool schemas into Ollama-compatible function
    definitions.
-   Supports LLM-driven tool selection and execution.
-   Runs a bounded tool-calling loop for multi-step interactions.
-   Returns tool results to the LLM for further reasoning.
-   Handles MCP tool errors and execution failures.

### 6. MCP Tool Execution and Safety

-   Validates tool arguments against required and supported schema
    properties.
-   Requests user approval before executing `delete_note`.
-   Prevents deletion when approval is unavailable or declined.
-   Handles MCP tool errors through the SDK's `is_error` result field.
-   Uses conservative retry behaviour for potentially state-changing
    operations when connection status is uncertain.

### 7. MCP Connection Management and Crash Recovery

-   Establishes and closes MCP client sessions.
-   Handles MCP server startup failures with a readable error.
-   Detects connection-related failures during tool discovery and
    execution.
-   Attempts automatic reconnection when the MCP connection is lost.
-   Retries eligible read-only operations once after successful
    reconnection.
-   Avoids automatically repeating write or delete operations when the
    outcome may be uncertain.
-   Recovers from actual MCP server subprocess termination.

### 8. Notepad MCP Server

The Notepad MCP server uses Python and STDIO transport.

  Tool             Description
  ---------------- -------------------------------------------------
  `create_note`    Create a text note
  `read_note`      Read an existing note
  `append_note`    Append content to a note
  `list_notes`     List available notes
  `delete_note`    Delete a note (requires approval through KAIRO)
  `search_notes`   Search across notes

### 9. MCP Resources

  Resource URI          Description
  --------------------- --------------------------------------
  `notes://list`        Discover available notes
  `note://{filename}`   Access an individual note's contents

### 10. MCP Prompts

  Prompt             Description
  ------------------ ----------------------------------------------
  `summarize_note`   Provides instructions for summarizing a note
  `improve_note`     Provides instructions for improving a note

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
  Testing                     pytest, pytest-asyncio, pytest-cov
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
├── data/                  # Local SQLite database (Git-ignored)
├── notes/
├── tests/
│
├── main.py
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

------------------------------------------------------------------------

## Getting Started

### Prerequisites

-   Python 3.11 or newer
-   Git
-   Ollama

### 1. Clone the Repository

``` powershell
git clone https://github.com/kaushikbargaway/kairo.git
cd kairo
```

### 2. Create and Activate a Virtual Environment

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution in the current terminal, run:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

### 3. Install Dependencies

Install runtime dependencies:

``` powershell
python -m pip install -r requirements.txt
```

To install the development and testing dependencies as well:

``` powershell
python -m pip install -r requirements-dev.txt
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
server through the MCP client using STDIO. You do not need to start the
Notepad MCP server in a separate terminal.

------------------------------------------------------------------------

## Testing

KAIRO uses `pytest` for unit and integration testing. Tests are located
in the root-level `tests/` directory.

### Run the complete test suite

``` powershell
python -m pytest -v
```

### Run tests with coverage

``` powershell
python -m pytest --cov=agent --cov=conversation --cov=ollama_client --cov=client --cov=servers.notepad --cov-report=term-missing -v
```

### Run a specific test module

``` powershell
python -m pytest tests/test_orchestrator_process_crash.py -v -s
```

### Run optional Ollama integration tests

The Ollama integration tests use a real local model and require Ollama
to be running with the configured model available.

In PowerShell:

``` powershell
$env:KAIRO_RUN_OLLAMA_INTEGRATION="1"
python -m pytest tests/test_ollama_integration.py tests/test_multiturn_integration.py -v -s
Remove-Item Env:KAIRO_RUN_OLLAMA_INTEGRATION
```

### Crash-recovery test coverage

The test suite includes:

-   MCP client disconnection and reconnection.
-   Recovery after an actual MCP server subprocess is terminated.
-   Orchestrator detection of a lost connection.
-   Automatic reconnection and retry of a read-only operation.
-   Verification that a replacement MCP server process is running.
-   Protection against automatically retrying potentially state-changing
    operations.

### Testing the MCP Server with MCP Inspector

The Notepad MCP server can also be inspected using the official MCP
Inspector.

``` powershell
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
-   [x] SQLite-backed persistent conversation storage
-   [x] Restore the most recently updated conversation on startup
-   [x] Create, list, resume, and delete conversations
-   [x] Automatic conversation titles

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
-   [x] Automated unit and integration tests
-   [x] Actual MCP server process-crash recovery testing
-   [x] 100% statement coverage across measured project modules

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
-   Restoring conversation transcripts across application sessions.
-   Remembering useful information through future semantic long-term
    memory.
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

*KAIRO v0.2.0 introduces persistent conversation storage. Semantic
long-term memory and additional desktop capabilities remain part of the
development roadmap.*
