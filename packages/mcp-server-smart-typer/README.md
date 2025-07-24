# MCP Smart Typer

AI-powered typing automation with Windows UI integration using comprehensive Zod schemas and the Model Context Protocol (MCP).

## Overview

MCP Smart Typer is a sophisticated automation server that enables AI models to intelligently interact with Windows applications through form field detection, smart typing, and UI context understanding. Built with TypeScript and comprehensive Zod schema validation, it provides a secure and robust interface for automating text input across different applications.

## Features

### 🎯 **Smart Field Detection**
- **Context-aware field analysis**: Automatically detects input fields with rich metadata
- **Intelligent field typing**: Recognizes email, password, phone, URL, and other field types
- **Confidence scoring**: Provides reliability metrics for detected elements
- **Window context**: Understands application context and window boundaries

### 🔐 **Security & Safety**
- **Security flags**: Built-in protection for sensitive data handling
- **Validation schemas**: Comprehensive Zod validation for all inputs/outputs
- **Async job tracking**: Monitor long-running operations with unique job IDs
- **Error handling**: Robust error reporting with detailed error codes

### 🚀 **Advanced Typing Features**
- **Configurable delays**: Adjustable keystroke timing for natural typing
- **Simulation mode**: Test automation without actual input for development
- **Field clearing**: Smart field clearing before typing
- **Enter key support**: Automatic form submission capabilities

### 📊 **Rich Metadata & Analytics**
- **Field metadata**: Comprehensive information about detected fields
- **Performance metrics**: Timing and success rate tracking
- **Window information**: Detailed window and application context
- **Job management**: Background job tracking and cleanup

## Installation

```bash
# Clone the repository
git clone https://github.com/mcp-smart-typer/mcp-smart-typer.git
cd mcp-smart-typer

# Install dependencies
npm install

# Build the project
cd packages/mcp-server-smart-typer
npm install
npm run build
```

## Quick Start

### Running the Server

```bash
# Development mode with hot reload
npm run dev

# Production mode
npm start

# Test the server
node test-mcp-server.js
```

### Basic Usage

The MCP Smart Typer server exposes four main tools:

#### 1. Detect Fields
Analyzes the active window to detect input fields with rich metadata.

```json
{
  "method": "call_tool",
  "params": {
    "name": "detect_fields",
    "arguments": {
      "contextHint": "login-form",
      "windowTitle": "My Application",
      "includeHidden": false,
      "confidence": 0.8,
      "securityFlags": ["authenticated"]
    }
  }
}
```

**Response:**
```json
{
  "fields": [
    {
      "id": "field_username_001",
      "name": "username",
      "type": "input",
      "metadata": {
        "description": "Username input field",
        "inputType": "text",
        "required": true,
        "bounds": { "x": 100, "y": 200, "width": 200, "height": 30 },
        "confidence": 0.95
      }
    }
  ],
  "windowInfo": {
    "title": "My Application - Login",
    "className": "Chrome_WidgetWin_1",
    "handle": "0x001234AB",
    "bounds": { "x": 0, "y": 0, "width": 1920, "height": 1080 }
  },
  "asyncJobId": "job_1234567890_abcd1234"
}
```

#### 2. Type Text
Types text into a specified field with advanced options.

```json
{
  "method": "call_tool",
  "params": {
    "name": "type_text",
    "arguments": {
      "fieldId": "field_username_001",
      "text": "john.doe@example.com",
      "options": {
        "delay": 50,
        "clearFirst": true,
        "pressEnter": false,
        "simulate": false
      },
      "securityFlags": ["encrypted"]
    }
  }
}
```

#### 3. Get Field Value
Retrieves the current value from a specified field.

```json
{
  "method": "call_tool",
  "params": {
    "name": "get_field_value",
    "arguments": {
      "fieldId": "field_username_001",
      "maxLength": 10000,
      "securityFlags": ["sensitive"]
    }
  }
}
```

#### 4. Focus Field
Focuses a specified field and optionally brings its window to front.

```json
{
  "method": "call_tool",
  "params": {
    "name": "focus_field",
    "arguments": {
      "fieldId": "field_password_002",
      "bringToFront": true,
      "scrollIntoView": true
    }
  }
}
```

## Architecture

### Schema-Driven Design

MCP Smart Typer uses comprehensive Zod schemas for all tool inputs and outputs:

```typescript
// Example: Type Text Request Schema
export const typeTextRequest = z.object({
  fieldId: z.string().describe('Target field identifier'),
  text: z.string().describe('Text to type'),
  options: z.object({
    delay: z.number().min(0).max(5000).default(50),
    clearFirst: z.boolean().default(false),
    pressEnter: z.boolean().default(false),
    simulate: z.boolean().default(false),
  }).optional(),
  securityFlags: z.array(z.string()).optional(),
});
```

### Generated Documentation

The project automatically generates:
- **JSON Schema files**: Individual schemas for each tool
- **OpenAPI specification**: Complete API documentation
- **TypeScript types**: Type-safe development experience

```bash
# Generate schemas and documentation
npm run generate-schemas
```

### Mock Native Client

For development and testing, the server includes a mock native client that simulates Windows UI automation:

```typescript
const mockFields = [
  {
    id: 'field_username_001',
    name: 'username',
    type: 'input',
    inputType: 'text',
    bounds: { x: 100, y: 200, width: 200, height: 30 },
    confidence: 0.95,
  },
  // ... more fields
];
```

## Security Features

### Security Flags
- `authenticated`: Requires user authentication
- `encrypted`: Handles encrypted/sensitive data
- `sensitive`: Contains personally identifiable information
- `readonly`: Read-only operations only

### Data Protection
- Password fields automatically redacted in logs
- Sensitive field values protected with `[REDACTED]` placeholder
- Security flag validation for all operations
- Comprehensive error handling without data leakage

## Configuration

### Environment Variables
```bash
# Server configuration
MCP_SERVER_NAME=mcp-smart-typer
MCP_SERVER_VERSION=1.0.0

# Logging level
LOG_LEVEL=info

# Native client configuration
NATIVE_CLIENT_TIMEOUT=5000
```

### Server Options
```typescript
const server = new Server({
  name: 'mcp-smart-typer',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {},
  },
});
```

## Development

### Project Structure
```
mcp-smart-typer/
├── packages/
│   ├── mcp-server-smart-typer/       # Main MCP server
│   │   ├── src/
│   │   │   ├── schemas/              # Zod schema definitions
│   │   │   ├── tools/                # MCP tool implementations
│   │   │   ├── utils/                # Utilities and mock client
│   │   │   └── simple-server.ts      # Main server implementation
│   │   ├── scripts/
│   │   │   └── generate-json-schemas.ts  # Schema generation
│   │   ├── docs/schemas/             # Generated JSON schemas
│   │   └── test-mcp-server.js        # Test client
│   └── native-helpers/               # Native Windows automation
└── README.md
```

### Adding New Tools

1. **Define Zod schemas** in `src/schemas/index.ts`
2. **Add tool implementation** in the main switch statement
3. **Update tool list** in the `list_tools` handler
4. **Generate schemas** with `npm run generate-schemas`
5. **Test** with the test client

### Testing

```bash
# Run the test suite
node test-mcp-server.js

# Development server with hot reload
npm run dev

# Type checking
npm run typecheck

# Linting
npm run lint
```

## API Reference

### Tools

#### `detect_fields`
Detects input fields in the active window with rich metadata and context awareness.

**Parameters:**
- `contextHint` (string, required): Context hint for field detection
- `securityFlags` (string[], optional): Security flags for operation validation
- `windowTitle` (string, optional): Specific window title to focus on
- `includeHidden` (boolean, optional): Whether to include hidden fields
- `confidence` (number, optional): Minimum confidence threshold (0-1)

#### `type_text`
Types text into a specified field with advanced options and security features.

**Parameters:**
- `fieldId` (string, required): Target field identifier
- `text` (string, required): Text to type
- `options` (object, optional): Typing options (delay, clearFirst, pressEnter, simulate)
- `securityFlags` (string[], optional): Security flags for operation validation

#### `get_field_value`
Retrieves the current value from a specified field with security considerations.

**Parameters:**
- `fieldId` (string, required): Field identifier to read from
- `securityFlags` (string[], optional): Security flags for operation validation
- `maxLength` (number, optional): Maximum length of value to retrieve

#### `focus_field`
Focuses a specified field and optionally brings its window to front.

**Parameters:**
- `fieldId` (string, required): Field identifier to focus
- `securityFlags` (string[], optional): Security flags for operation validation
- `bringToFront` (boolean, optional): Whether to bring window to front
- `scrollIntoView` (boolean, optional): Whether to scroll field into view

### Response Format

All responses include:
- `asyncJobId`: Unique job identifier for tracking
- `errorCode`: Error code if operation failed
- `errorMessage`: Human-readable error message

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Use TypeScript for all code
- Follow the existing Zod schema patterns
- Add comprehensive error handling
- Include tests for new features
- Update documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/mcp-smart-typer/mcp-smart-typer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mcp-smart-typer/mcp-smart-typer/discussions)
- **Documentation**: [API Documentation](docs/api.md)

## Acknowledgments

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/typescript-sdk) for the foundational framework
- [Zod](https://github.com/colinhacks/zod) for schema validation
- The open-source community for inspiration and contributions
