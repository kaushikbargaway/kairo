# KAIRO

### Kaushik's AI for Interactive Reasoning and Orchestration

**Personal Desktop AI Assistant powered by Ollama and Model Context Protocol (MCP)**

KAIRO is an extensible personal desktop AI assistant designed to interact with local applications, manage files, automate desktop operations, and execute tasks through natural-language instructions.

Built using Python, Ollama, and the Model Context Protocol (MCP), KAIRO aims to bridge local AI reasoning with real-world desktop capabilities.

> Building an intelligent desktop companion, one capability at a time.

---

## Project Overview

KAIRO follows a modular architecture in which AI reasoning, conversation management, MCP clients, and MCP servers operate independently.

The project integrates a locally running Large Language Model (LLM) using **Ollama and Qwen3 1.7B**, enabling local inference without depending on external LLM APIs.

KAIRO also implements a Conversation Manager that maintains conversation history, supports contextual interactions, and manages session-based memory.

The MCP infrastructure currently includes a Notepad MCP server with tools for creating, reading, updating, deleting, listing, and searching notes.

The MCP implementation also demonstrates Resources, Resource Templates, Prompts, STDIO communication, and programmatic client-server interaction.

---

## Architecture

```text
                       USER
                         |
                         v
                  KAIRO AI ASSISTANT
                         |
                  CONVERSATIONAL CLI
                         |
                         v
                CONVERSATION MANAGER
                         |
                  MESSAGE HISTORY
                         |
                         v
                    KAIRO LLM
                         |
                       Ollama
                         |
                     Qwen3 1.7B
                         |
                         v
                 AGENT ORCHESTRATOR
                  (Under Development)
                         |
                    KAIRO CLIENT
                         |
                    MCP PROTOCOL
                         |
                         v
                    KAIRO SERVERS
                         |
              +----------+----------+
              |          |          |
            TOOLS     RESOURCES   PROMPTS
              |          |          |
              +----------+----------+
                         |
                    LOCAL STORAGE
```

*The LLM, Conversation Manager, and MCP infrastructure provide the foundation for KAIRO. Automated LLM-driven MCP tool execution and agent orchestration are upcoming development milestones.*

---

## Current Features

### 1. Local LLM Integration

- Integration with Ollama for local LLM inference.
- Qwen3 1.7B as the default language model.
- Python integration using the official Ollama SDK.
- Local inference without external LLM APIs.
- Configurable model selection.
- Custom generation parameters.
- Extended thinking disabled for faster responses.

### 2. AI Assistant Interface

- Interactive terminal-based conversational interface.
- Natural-language interaction with KAIRO.
- Custom system prompt defining KAIRO's identity and behaviour.
- Locally generated AI responses.
- Configurable response generation parameters.

### 3. Conversation Memory and Context Management

- Dedicated Conversation Manager module.
- Maintains conversation history during active sessions.
- Sends previous messages to the LLM for contextual understanding.
- Supports contextual follow-up questions.
- Configurable conversation history limits.
- Conversation reset functionality.
- Conversation history inspection through CLI commands.

**Available Commands**

| Command | Description |
|---|---|
| `/reset` | Reset the current conversation |
| `/history` | Display conversation history |
| `/exit` | Exit KAIRO |

*Conversation history is currently maintained in RAM. Persistent memory across application restarts is planned.*

### 4. MCP Server

- Python-based MCP server.
- STDIO transport.
- Modular server architecture.
- Automatic tool schema generation.

### 5. Notepad MCP Tools

| Tool | Description |
|---|---|
| `create_note` | Create a text note |
| `read_note` | Read an existing note |
| `append_note` | Append content to a note |
| `list_notes` | List available notes |
| `delete_note` | Delete a note |
| `search_notes` | Search across notes |

### 6. MCP Resources

- `notes://list` – Discover available notes.
- `note://{filename}` – Access individual note contents.

### 7. MCP Prompts

- `summarize_note` – Generate note summarization instructions.
- `improve_note` – Generate note improvement instructions.

### 8. MCP Client

- Establishes STDIO communication.
- Discovers server capabilities.
- Lists available tools, resources, and prompts.
- Executes MCP tools programmatically.
- Provides an interactive CLI.

---

## Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Local LLM Runtime | Ollama |
| Language Model | Qwen3 1.7B |
| LLM Integration | Ollama Python SDK |
| AI Architecture | Modular LLM-based architecture |
| Conversation Management | Custom Python Module |
| Protocol | Model Context Protocol |
| MCP SDK | Python MCP SDK |
| Communication | STDIO |
| Client | Python |
| Testing | MCP Inspector |
| Version Control | Git & GitHub |

---

## Project Structure

```text
kairo/
│
├── ai/
│   └── __init__.py
│
├── client/
│   ├── __init__.py
│   └── mcp_client.py
│
├── ollama_client/
│   ├── __init__.py
│   └── client.py
│
├── conversation/
│   ├── __init__.py
│   └── manager.py
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
├── logs/
│
├── main.py
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Git
- Ollama
- Node.js and npm (for MCP Inspector)

### 1. Clone the Repository

```bash
git clone https://github.com/kaushikbargaway/kairo.git

cd kairo
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Install Ollama

Download and install Ollama:

https://ollama.com/download

Pull the default KAIRO language model:

```powershell
ollama pull qwen3:1.7b
```

Verify the installation:

```powershell
ollama list
```

Ensure the Ollama service is running.

### 5. Launch KAIRO

Start the conversational AI interface:

```powershell
python main.py
```

KAIRO connects to the locally running Ollama instance and generates responses using Qwen3 1.7B.

### 6. Start the MCP Server

```powershell
python -m servers.notepad.server
```

The server communicates through STDIO and is designed to be launched by an MCP client.

### 7. Run the MCP Client

In another terminal:

```powershell
python -m client.mcp_client
```

The client automatically launches the MCP server and discovers its available capabilities.

---

## Testing with MCP Inspector

KAIRO's MCP server can also be tested using the official MCP Inspector.

```bash
npx -y @modelcontextprotocol/inspector
```

Configure the server:

| Setting | Value |
|---|---|
| Command | `.venv/Scripts/python.exe` |
| Arguments | `-m servers.notepad.server` |
| Working Directory | Project root |

Inspect and test the available tools, resources, and prompts.

---

## Development Roadmap

### Phase 1: MCP Foundation

- [x] Initial MCP server implementation
- [x] Notepad MCP tools
- [x] MCP Resources and Resource Templates
- [x] MCP Prompts
- [x] Modular server architecture
- [x] Custom Python MCP client
- [x] Interactive CLI

### Phase 2: Local AI Integration

- [x] Ollama installation and configuration
- [x] Local LLM integration
- [x] Qwen3 model integration
- [x] Python Ollama SDK integration
- [x] Custom KAIRO system prompt
- [x] Conversational terminal interface
- [x] Lightweight model optimisation
- [x] Conversation history and context management
- [x] Conversation reset functionality
- [x] Conversation history inspection
- [ ] Persistent conversational memory

### Phase 3: Intelligent Agent Architecture

- [ ] AI-powered MCP tool discovery
- [ ] LLM-driven MCP tool selection and execution
- [ ] Agent orchestration
- [ ] Multi-step task execution
- [ ] Context-aware tool invocation
- [ ] Tool execution feedback and error handling

### Phase 4: Desktop Capabilities

- [ ] Filesystem MCP server
- [ ] File and directory management
- [ ] Desktop automation
- [ ] Application interaction
- [ ] Voice-based interaction
- [ ] Multi-server MCP architecture

### Phase 5: User Experience and Security

- [ ] Desktop application interface
- [ ] Real-time voice interaction
- [ ] Security and permission management
- [ ] Execution approval workflows
- [ ] Logging and monitoring

---

## Project Goals

KAIRO aims to evolve into a personal desktop AI ecosystem capable of:

- Understanding natural-language instructions.
- Running local language models.
- Maintaining contextual conversations.
- Remembering useful information across sessions.
- Interacting with external tools through MCP.
- Managing files and directories.
- Automating desktop operations.
- Supporting voice-based interaction.
- Integrating multiple MCP servers.
- Executing complex multi-step tasks.
- Providing secure, permission-controlled automation.

---

## Author

**Kaushik Kumar**

B.E. Information Science and Engineering

GitHub: [@kaushikbargaway](https://github.com/kaushikbargaway)

---

*KAIRO is an actively developed personal project. Features and architecture will evolve as development progresses.*