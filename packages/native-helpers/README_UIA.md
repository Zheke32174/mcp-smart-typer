# MCP Smart Typer - Native Helpers (Windows UIA)

Advanced Windows desktop automation with comprehensive UIA (UI Automation) support.

## Features

- **Windows UIA Automation**: Full support for Windows UI Automation using `pywinauto` and `uiautomation`
- **Element Enumeration**: Automatically discover and filter Edit, Document, and RichEdit controls
- **Advanced Text Input**: Multiple typing methods with intelligent fallbacks:
  - UIA `ValuePattern.SetValue()` (preferred)
  - UIA `SendKeys()` with focus management
  - `pyautogui` fallback for compatibility
- **Element Information**: Capture comprehensive element metadata:
  - Bounds, control patterns (`ValuePattern`, `TextPattern`, etc.)
  - Name, HelpText, LabeledBy relationships
  - Window context and process information
- **gRPC Interface**: High-performance, cross-language communication
- **Single-File Executable**: PyInstaller-based distribution for easy deployment

## Quick Start

### Option 1: Build and Run Executable (Recommended)

```bash
# Build the single-file executable
build.bat

# Run the server
dist\mcp-uia-server.exe --port 50051
```

### Option 2: Run from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Generate protobuf files
python -m grpc_tools.protoc --proto_path=proto --python_out=src/generated --grpc_python_out=src/generated proto/ui_automation.proto

# Start the UIA server
python src/main.py --port 50051
```

## Testing

Run the comprehensive test suite:

```bash
python test_uia_functionality.py
```

This will test:
- UIA element enumeration
- gRPC service implementation  
- Complete server functionality

## gRPC API Reference

### EnumerateUIAElements
Discover UIA elements of specified types:

```protobuf
message EnumerateUIAElementsRequest {
  optional string window_title = 1;        // Filter by window title
  repeated string element_types = 2;       // "Edit", "Document", "RichEdit"
  optional bool include_invisible = 3;     // Include hidden elements
}
```

### TypeIntoUIAElement
Type text into a specific element with intelligent method selection:

```protobuf
message TypeIntoUIAElementRequest {
  string element_id = 1;          // Element ID from enumeration
  string text = 2;                // Text to type
  optional bool clear_first = 3;  // Clear existing text
  optional bool use_fallback = 4; // Use pyautogui if UIA fails
}
```

### Response Details
All responses include:
- Success status
- Method used ("uia_set_value", "uia_send_keys", "pyautogui")
- Detailed error messages

## Element Information Captured

For each discovered element:

```json
{
  "element_id": "uia_abc123_1234567890",
  "name": "Search",
  "automation_id": "SearchBox",
  "class_name": "Edit",
  "control_type": "Edit",
  "bounds": {"x": 100, "y": 200, "width": 300, "height": 25},
  "is_visible": true,
  "is_enabled": true,
  "is_focusable": true,
  "value": "current text content",
  "help_text": "Enter search terms",
  "labeled_by": "Search Label",
  "control_patterns": ["ValuePattern", "TextPattern"],
  "window_title": "My Application",
  "process_id": 1234
}
```

## Architecture

### Core Components

- **`windows_uia_automation.py`**: Main UIA automation engine with element caching
- **`uia_grpc_server.py`**: gRPC service implementation with comprehensive error handling
- **`ui_automation.proto`**: Protocol buffer definitions for all RPC methods
- **`main.py`**: Server entry point with command-line interface

### Key Features

1. **Element Caching**: Maintains references to discovered elements for reliable interaction
2. **Method Fallbacks**: Automatically tries multiple typing methods for maximum compatibility
3. **Thread Safety**: Concurrent access protection for element cache
4. **Memory Management**: Automatic cleanup of old cached elements

## Building the Executable

The build process creates a single-file executable containing all dependencies:

```bash
# Automated build with verification
build.bat

# Manual build steps
pip install -r requirements.txt
python -m grpc_tools.protoc --proto_path=proto --python_out=src/generated --grpc_python_out=src/generated proto/ui_automation.proto
pyinstaller build_uia_server.spec --clean --noconfirm
```

The resulting `dist/mcp-uia-server.exe` includes:
- Python runtime
- All Python dependencies (pywinauto, uiautomation, grpc, etc.)
- Generated protobuf code
- UIA automation modules

## Usage Examples

### Command Line
```bash
# Start server with default settings
mcp-uia-server.exe

# Custom port and verbose logging
mcp-uia-server.exe --port 50051 --verbose

# Show help
mcp-uia-server.exe --help
```

### Client Integration
See the test script for example gRPC client usage.

## Requirements

- Windows 10/11 (UIA support required)
- Python 3.8+ (for development)
- Windows UI Automation APIs
- Administrator privileges may be required for some applications

## Contributing

Please follow the existing code style and ensure all tests pass:

```bash
python test_uia_functionality.py
```

## License

MIT License - see LICENSE file for details.
