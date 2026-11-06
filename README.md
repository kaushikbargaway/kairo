# NEXORA

### Personal Desktop AI Assistant powered by Model Context Protocol (MCP)

NEXORA is an extensible personal desktop AI assistant designed to interact with local applications, manage files, automate desktop operations, and execute tasks through natural-language instructions.

Built using Python and the Model Context Protocol (MCP), NEXORA aims to bridge AI reasoning with real-world desktop capabilities.

> Building an intelligent desktop companion, one capability at a time.

---

## Project Overview

NEXORA follows a modular architecture in which AI reasoning, MCP clients, and MCP servers operate independently.

The project currently implements a Notepad MCP server with tools for creating, reading, updating, deleting, listing, and searching notes.

It also demonstrates MCP Resources, Resource Templates, Prompts, STDIO communication, and programmatic client-server interaction.

## Architecture

```text
                 USER
                   |
                   v
          NEXORA AI ASSISTANT
                   |
             AI Reasoning
                   |
                   v
            NEXORA CLIENT
                   |
              MCP Protocol
                   |
                   v
            NEXORA SERVERS
                   |
          +--------+--------+
          |        |        |
        TOOLS   RESOURCES  PROMPTS
          |        |        |
          +--------+--------+
                   |
             LOCAL STORAGE
```

*AI reasoning and desktop automation integration are planned development milestones.*

## Current Features

### MCP Server

- Python-based MCP server.
- STDIO transport.
- Modular server architecture.
- Automatic tool schema generation.

### Notepad MCP Tools

| Tool | Description |
|---|---|
| `create_note` | Create a text note |
| `read_note` | Read an existing note |
| `append_note` | Append content to a note |
| `list_notes` | List available notes |
| `delete_note` | Delete a note |
| `search_notes` | Search across notes |

### MCP Resources

- `notes://list` – Discover available notes.
- `note://{filename}` – Access individual note contents.

### MCP Prompts

- `summarize_note` – Generate note summarization instructions.
- `improve_note` – Generate note improvement instructions.

### MCP Client

- Establishes STDIO communication.
- Discovers server capabilities.
- Lists available tools, resources, and prompts.
- Executes MCP tools programmatically.
- Provides an interactive CLI.

## Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Protocol | Model Context Protocol |
| MCP SDK | Python MCP SDK |
| Communication | STDIO |
| Client | Python |
| Testing | MCP Inspector |
| Version Control | Git & GitHub |

## Project Structure

```text
nexora/
│
├── ai/
│   └── __init__.py
│
├── client/
│   ├── __init__.py
│   └── mcp_client.py
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
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Git
- Node.js and npm (for MCP Inspector)

### 1. Clone the repository

```bash
git clone https://github.com/kaushikbargaway/nexora.git

cd nexora
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the MCP server

```bash
python -m servers.notepad.server
```

The server communicates through STDIO and is designed to be launched by an MCP client.

### 5. Run the MCP client

In another terminal:

```powershell
python -m client.mcp_client
```

The client automatically launches the MCP server and discovers its available capabilities.

## Testing with MCP Inspector

NEXORA's MCP server can also be tested using the official MCP Inspector.

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

## Development Roadmap

- [x] Initial MCP server implementation
- [x] Notepad MCP tools
- [x] MCP Resources and Resource Templates
- [x] MCP Prompts
- [x] Modular server architecture
- [x] Custom Python MCP client
- [x] Interactive CLI
- [ ] Local LLM integration using Ollama
- [ ] AI-powered MCP tool selection and execution
- [ ] Filesystem MCP server
- [ ] Desktop automation
- [ ] Voice interaction
- [ ] Multi-server MCP architecture
- [ ] Desktop application interface
- [ ] Security and permission management

## Project Goals

NEXORA aims to evolve into a personal desktop AI ecosystem capable of:

- Understanding natural-language instructions.
- Interacting with local applications.
- Managing files and directories.
- Executing approved desktop operations.
- Supporting voice-based interaction.
- Integrating multiple MCP servers.
- Running local AI models.

## Author

**Kaushik Kumar**

B.E. Information Science and Engineering

GitHub: [@kaushikbargaway](https://github.com/kaushikbargaway)

---

* NEXORA is an actively developed personal project. Features and architecture will evolve as development progresses.*