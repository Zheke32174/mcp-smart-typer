# MCP Smart Typer

AI-powered typing automation with Windows UI integration via Model Context Protocol (MCP).

## Overview

MCP Smart Typer is a monorepo containing two main packages that work together to provide intelligent typing automation:

1. **mcp-server-smart-typer** - TypeScript/Node.js MCP server exposing typing automation tools
2. **native-helpers** - Python gRPC service for Windows UI automation using PyAutoGUI

## Architecture

```
┌─────────────────┐    MCP Protocol    ┌──────────────────────┐
│   AI Client     │◄──────────────────►│ mcp-server-smart-    │
│   (Claude/etc)  │                    │ typer (TypeScript)   │
└─────────────────┘                    └──────────┬───────────┘
                                                  │
                                               gRPC │
                                                  │
                                       ┌──────────▼───────────┐
                                       │ native-helpers       │
                                       │ (Python)             │
                                       └──────────┬───────────┘
                                                  │
                                            Windows UI │
                                                  │
                                       ┌──────────▼───────────┐
                                       │ Target Applications  │
                                       │ (Any Windows App)    │
                                       └──────────────────────┘
```

## Features

- **MCP Protocol Integration**: Standard protocol for AI model context and tool usage
- **Cross-Language Architecture**: TypeScript server with Python UI automation backend
- **Windows UI Automation**: Native Windows UI interaction via PyAutoGUI
- **gRPC Communication**: High-performance inter-service communication
- **Type Safety**: Full TypeScript support with proper type definitions
- **Monorepo Structure**: Organized workspace with shared configurations

## Quick Start

### Prerequisites

- Node.js 18+ and pnpm 8+
- Python 3.8+ with pip
- Windows OS (for UI automation)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-smart-typer

# Install dependencies
pnpm install

# Set up Python environment for native helpers
cd packages/native-helpers
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd ../..

# Build all packages
pnpm build
```

### Development

```bash
# Start all services in development mode
pnpm dev

# Or start individual services
cd packages/mcp-server-smart-typer
pnpm dev

# In another terminal
cd packages/native-helpers
python -m src.main
```

### Testing

```bash
# Run all tests
pnpm test

# Run linting
pnpm lint

# Format code
pnpm format
```

## Package Structure

```
mcp-smart-typer/
├── packages/
│   ├── mcp-server-smart-typer/     # Main MCP server (TypeScript)
│   │   ├── src/
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── native-helpers/             # UI automation service (Python)
│       ├── src/
│       ├── requirements.txt
│       └── pyproject.toml
├── package.json                    # Root workspace config
├── pnpm-workspace.yaml
├── tsconfig.json
└── README.md
```

## Configuration

### Environment Variables

- `GRPC_PORT`: Port for gRPC communication (default: 50051)
- `MCP_PORT`: Port for MCP server (default: 3000)
- `LOG_LEVEL`: Logging level (debug, info, warn, error)

### MCP Server Configuration

The MCP server can be configured via `packages/mcp-server-smart-typer/config.json`.

## Usage

### As MCP Server

Connect your AI client to the MCP server endpoint to access typing automation tools.

### Available Tools

- `type_text`: Types text into the active window
- `send_keys`: Sends specific key combinations
- `get_active_window`: Gets information about the current active window
- `find_element`: Locates UI elements for interaction
- `click_element`: Clicks on UI elements

## Development

### Adding New Tools

1. Define the tool in `packages/mcp-server-smart-typer/src/tools/`
2. Add corresponding gRPC method in `packages/native-helpers/src/`
3. Update protobuf definitions if needed
4. Add tests for both packages

### Code Style

- TypeScript: ESLint + Prettier configuration
- Python: Black + isort + mypy for formatting and type checking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Troubleshooting

### Common Issues

1. **gRPC Connection Failed**: Ensure native-helpers service is running
2. **UI Automation Not Working**: Check Windows permissions and security settings
3. **TypeScript Compilation Errors**: Verify Node.js version and dependencies

### Debug Mode

Set `LOG_LEVEL=debug` to enable detailed logging across all services.

## Roadmap

- [ ] Linux/macOS support via platform-specific automation
- [ ] Visual element recognition and AI-guided interaction
- [ ] Advanced text processing and context awareness
- [ ] Plugin system for custom automation workflows
- [ ] Web-based configuration interface
