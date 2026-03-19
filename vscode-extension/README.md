# KeepContext AI — VS Code Extension

> Browse memories, query context, and run AI agent workflows directly from VS Code.

## Features

| Feature | Description |
|---------|-------------|
| 🧠 **Memory Sidebar** | Browse stored memories by type with icons |
| ➕ **Store Memory** | Save text or selected code as project memory |
| 🔍 **Query Context** | Semantic search across all stored knowledge |
| 💬 **Ask Question** | Get LLM-powered answers enriched with project context |
| 🤖 **Run Agent** | Full plan → develop → review workflow from a goal |
| 📊 **Status Bar** | Live connection status indicator |
| 📋 **Right-Click Menu** | Store selected code as memory from any editor |

## Prerequisites

- **KeepContext AI backend** running (default: `http://localhost:8003`)
- Node.js 18+

## Quick Start

### 1. Start the backend

```bash
cd keepcontext-ai
docker-compose up -d
```

### 2. Install the extension

**From source (development):**

```bash
cd vscode-extension
npm install
npm run compile
```

Then press `F5` in VS Code to launch the Extension Development Host.

**From VSIX (production):**

```bash
cd vscode-extension
npm run package
code --install-extension keepcontext-ai-0.1.0.vsix
```

### 3. Configure

Open VS Code Settings and search for "KeepContext":

| Setting | Default | Description |
|---------|---------|-------------|
| `keepcontext.apiUrl` | `http://localhost:8003` | Backend API URL |
| `keepcontext.defaultMemoryType` | `code` | Default type for new memories |
| `keepcontext.agentMaxIterations` | `3` | Max agent review loop iterations |

For a deployed backend, set `keepcontext.apiUrl` to your server URL (example: `http://13.232.100.178`).

## Usage

### Store a Memory

1. **Command Palette** → `KeepContext: Store Memory`
2. Enter content and select type
3. Memory appears in the sidebar

### Store Selected Code

1. Select code in any file
2. **Right-click** → `KeepContext: Store Selection as Memory`
3. Select type — stored with source file metadata

### Query Context

1. **Command Palette** → `KeepContext: Query Context`
2. Enter a natural language query
3. Browse results ranked by relevance

### Ask a Question

1. **Command Palette** → `KeepContext: Ask Question`
2. Get an LLM-powered answer using your project's stored knowledge
3. Answer opens in a new Markdown tab

### Run Agent Workflow

1. **Command Palette** → `KeepContext: Run Agent Workflow`
2. Describe what you want to build
3. Agent generates plan → code → review in a rich panel

## Commands

| Command | ID |
|---------|-----|
| Store Memory | `keepcontext.storeMemory` |
| Store Selection | `keepcontext.storeSelection` |
| Query Context | `keepcontext.queryContext` |
| Ask Question | `keepcontext.askQuestion` |
| Run Agent | `keepcontext.runAgent` |
| Refresh Memories | `keepcontext.refreshMemories` |
| Delete Memory | `keepcontext.deleteMemory` |

## Development

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode
npm run watch

# Lint
npm run lint

# Package as VSIX
npm run package
```

## Architecture

```
vscode-extension/
├── src/
│   ├── extension.ts          # Entry point — activate/deactivate
│   ├── apiClient.ts          # HTTP client for backend API
│   ├── commands.ts           # Command implementations
│   ├── memoryTreeProvider.ts # Sidebar tree view
│   ├── statusBar.ts          # Connection status indicator
│   ├── agentResultPanel.ts   # Webview for agent results
│   ├── types.ts              # TypeScript type definitions
│   └── test/                 # Test suite
├── media/                    # Icons
├── package.json              # Extension manifest
└── tsconfig.json             # TypeScript config
```

## License

MIT
