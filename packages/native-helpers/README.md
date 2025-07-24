# MCP Smart Typer Native Helpers

Python gRPC service for Windows UI Automation used by the MCP Smart Typer project.

## Overview

The MCP Smart Typer Native Helpers package provides a bridge between Node.js and the Windows system for performing UI automation tasks, including typing text, sending key strokes, retrieving information about active windows, and interacting with screen elements.

## Features

- **Type Text**: Type strings into the active window
- **Send Keys**: Simulate key presses including key combinations
- **Get Active Window**: Retrieve details of the currently active window
- **Find Element**: Locate UI elements using text, class, or id
- **Click Element**: Simulate mouse clicks and interactions

## Requirements

- Python 3.8+
- Windows operating system for PyAutoGUI-based UI automation

## Installation

```bash
pip install -r requirements.txt
```

## Development

### Set up Protobuf

From the root directory, run:

```bash
python -m grpc_tools.protoc -I ./proto --python_out=./src/generated --grpc_python_out=./src/generated ./proto/ui_automation.proto
```

### Running the Service

To start the gRPC server:

```bash
python -m src.main
```

## Code Style

- **Black**: Auto-format code style
- **isort**: Organize imports
- **mypy**: Type-checking

```bash
black .
isort .
mypy src/
```

### Logging

Enable verbose logging by using the `--verbose` flag when running the server:

```bash
python -m src.main --verbose
```

## Testing

Unit tests can be implemented with the `unittest` framework or similar and run via:

```bash
python -m unittest discover -s tests
```

## Contributing

If you wish to contribute, fork the project and submit a pull request or open an issue.

## License

MIT License - see LICENSE file for details.

