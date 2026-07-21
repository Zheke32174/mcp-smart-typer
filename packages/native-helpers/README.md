# MCP Smart Typer Native Helpers

Python gRPC service for Windows UI Automation used by the MCP Smart Typer project.

## Overview

The MCP Smart Typer Native Helpers package provides a bridge between Node.js and the Windows system for performing UI automation tasks, including typing text, sending key strokes, retrieving information about active windows, and interacting with screen elements.

## Features

- **Type Text**: Type strings into the active window
- **Send Keys**: Simulate key presses including key combinations
- **Get Active Window**: Retrieve details about the currently active window
- **Find Element**: Locate UI elements using text, class, or id
- **Click Element**: Simulate mouse clicks and interactions

## Requirements

- Python 3.10–3.12
- Windows for the UI Automation runtime
- A Playwright browser installation only when browser-automation features are used
- A system Tesseract executable only when OCR features are used

`pyproject.toml` is the authoritative package and dependency declaration. `requirements.txt` is retained only as a compatibility mirror and must remain synchronized with it.

## Installation

From `packages/native-helpers`:

```bash
python -m pip install .
```

For an editable development environment:

```bash
python -m pip install -e .
python -m pip install black isort mypy pytest
```

## Development

### Set up Protobuf

From `packages/native-helpers`, create the generated package and compile the protocol definition:

```bash
python -c "from pathlib import Path; p=Path('src/generated'); p.mkdir(parents=True, exist_ok=True); (p/'__init__.py').touch()"
python -m grpc_tools.protoc -I ./proto --python_out=./src/generated --grpc_python_out=./src/generated ./proto/ui_automation.proto
```

### Running the Service

To start the gRPC server:

```bash
python -m src.main
```

## Code Style

- **Black**: format Python sources
- **isort**: organize imports
- **mypy**: type-check the owned source tree

```bash
python -m black src test_*.py
python -m isort src test_*.py
python -m mypy src/ --ignore-missing-imports
```

### Logging

Enable verbose logging with:

```bash
python -m src.main --verbose
```

## Testing

Run the repository's Python tests with:

```bash
python -m pytest -xvs .
```

A run that collects no tests is treated as a failure by CI rather than rewritten as success.

## Contributing

Submit changes through a review branch and keep package metadata, generated-code instructions, formatting, type checks, tests, and candidate receipts aligned.

## License

MIT License - see LICENSE for details.
