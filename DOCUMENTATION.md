# MCP Smart Typer - Documentation & Usage Guide

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Security Considerations](#security-considerations)
- [Tool Reference](#tool-reference)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Development Guide](#development-guide)

## Installation

### Prerequisites

- **Node.js 18+** with npm or pnpm
- **Python 3.8+** with pip
- **Windows OS** (for UI automation features)
- **Claude Desktop** (for AI integration)

### Quick Installation

#### Option 1: NPM Package Installation (Recommended)

```bash
# Install the MCP server globally
npm install -g @mcp-smart-typer/server

# Verify installation
mcp-server-smart-typer --version
```

#### Option 2: From Source

```bash
# Clone repository
git clone https://github.com/mcp-smart-typer/mcp-smart-typer.git
cd mcp-smart-typer

# Install dependencies
npm install
cd packages/mcp-server-smart-typer
npm install
npm run build

# Install Python helpers (auto-downloads on first use)
cd ../native-helpers
pip install -r requirements.txt
```

### Python Helper Auto-Download

The MCP Smart Typer server automatically downloads and sets up Python helpers on first use:

1. **Automatic Detection**: Server detects if Python helpers are available
2. **Download Process**: Downloads pre-built Python binaries if needed
3. **Setup**: Automatically configures gRPC communication
4. **Verification**: Runs health checks to ensure proper setup

```bash
# Manual Python helper setup (optional)
cd packages/native-helpers
python -m src.main --setup
```

## Quick Start

### 1. Start the Server

```bash
# Development mode
npm run dev

# Production mode
npm start

# Or if installed globally
mcp-server-smart-typer
```

### 2. Basic Usage Example

```javascript
// Connect to MCP server
const mcp = new MCPClient('stdio://mcp-server-smart-typer');

// Detect input fields on screen
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'login-form',
  confidence: 0.8
});

// Type into detected field
await mcp.callTool('type_text', {
  fieldId: fields.fields[0].id,
  text: 'hello@example.com',
  options: {
    delay: 50,
    clearFirst: true
  }
});
```

### 3. Test the Installation

```bash
# Run test client
node test-mcp-server.js

# Run end-to-end tests
npm run test:e2e
```

## Claude Desktop Integration

### Configuration Setup

Add MCP Smart Typer to your Claude Desktop configuration:

#### macOS/Linux: `~/.config/claude/claude_desktop_config.json`
#### Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "args": [],
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "info",
        "SECURE_LOGGING": "true"
      }
    }
  }
}
```

### Advanced Configuration

```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "node",
      "args": [
        "/path/to/mcp-smart-typer/packages/mcp-server-smart-typer/dist/index.js"
      ],
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "debug",
        "SECURE_LOGGING": "true",
        "DRY_RUN_MODE": "false",
        "GRPC_PORT": "50051",
        "NATIVE_CLIENT_TIMEOUT": "5000"
      }
    }
  }
}
```

### Claude Desktop Usage Examples

#### Example 1: Web Form Automation

```
User: "Help me fill out the login form on this webpage. Username is john@example.com"

Claude: I'll help you fill out the login form. Let me first detect the available fields on your screen.

[Uses detect_fields tool]

I can see a login form with username and password fields. I'll fill in the username field for you.

[Uses type_text tool with the username]

The username has been entered successfully. Would you like me to help with the password field as well?
```

#### Example 2: Data Entry Assistance

```
User: "I need to fill out a contact form with multiple fields"

Claude: I'll help you fill out the contact form efficiently. Let me scan for input fields first.

[Uses detect_fields with contextHint: "contact-form"]

I found several fields:
- Name field
- Email field  
- Phone field
- Message field

Please provide the information you'd like me to enter, and I'll fill out the form for you with appropriate delays to make it appear natural.
```

## Security Considerations

### Built-in Security Features

#### 1. Permission System
- **Environment Variable Control**: `ALLOW_TYPING=true` required
- **Session-based Permissions**: Explicit permission grants per session
- **Security Flags**: Request-level security validation

#### 2. Sensitive Data Protection
- **Automatic Detection**: Recognizes password, email, and sensitive fields
- **Data Masking**: Sensitive values masked in logs (`p****d`)
- **Secure Logging**: Separate audit trail with data protection

#### 3. Audit Trail
- **Comprehensive Logging**: All operations logged with timestamps
- **Session Tracking**: Unique session IDs for operation correlation
- **Local Storage**: Audit logs stored in `~/Documents/mcp-typer-logs/`

### Security Best Practices

#### 1. Environment Configuration

```bash
# Production environment
ALLOW_TYPING=true
SECURE_LOGGING=true
LOG_LEVEL=info
DRY_RUN_MODE=false

# Development/Testing environment  
ALLOW_TYPING=true
SECURE_LOGGING=true
LOG_LEVEL=debug
DRY_RUN_MODE=true
```

#### 2. Using Security Flags

```javascript
// Mark sensitive operations
await mcp.callTool('type_text', {
  fieldId: 'password-field',
  text: userPassword,
  securityFlags: ['sensitive', 'encrypted', 'audit']
});

// Grant temporary permissions
await mcp.callTool('type_text', {
  fieldId: 'admin-field',
  text: adminData,
  securityFlags: ['mcp_root_permission', 'restricted']
});
```

#### 3. Dry-Run Testing

```javascript
// Test operations safely
await mcp.callTool('security_dry_run_control', {
  operation: 'enable',
  enabled: true
});

// Perform dry-run
const result = await mcp.callTool('type_text', {
  fieldId: 'critical-field',
  text: 'test-data',
  options: { simulate: true }
});

console.log('Would succeed:', result.dryRunResult.wouldSucceed);
console.log('Warnings:', result.dryRunResult.warnings);
```

### Common Security Scenarios

#### 1. Password Field Handling
```javascript
// Passwords are automatically detected and secured
await mcp.callTool('type_text', {
  fieldId: 'login-password',
  text: userPassword,
  securityFlags: ['sensitive'] // Auto-detected as password field
});
// Log will show: "Typed text to password field: [REDACTED]"
```

#### 2. Multi-Factor Authentication
```javascript
// Handle 2FA codes securely
await mcp.callTool('type_text', {
  fieldId: 'mfa-code',
  text: authCode,
  securityFlags: ['sensitive', 'audit'],
  options: {
    clearFirst: true,
    delay: 100 // Slower for security
  }
});
```

#### 3. Financial Data Entry
```javascript
// Credit card or banking information
await mcp.callTool('type_text', {
  fieldId: 'card-number',
  text: cardNumber,
  securityFlags: ['encrypted', 'restricted', 'audit'],
  options: {
    delay: 150, // Extra slow for security
    simulate: false // Never simulate financial data
  }
});
```

## Tool Reference

### Core Tools

#### 1. `detect_fields`

Automatically detects input fields on the active window with AI-powered field recognition.

**Parameters:**
```typescript
{
  contextHint: string;        // Context for detection (e.g., "login-form")
  securityFlags?: string[];   // Security flags
  windowTitle?: string;       // Specific window to focus
  includeHidden?: boolean;    // Include hidden fields (default: false)
  confidence?: number;        // Minimum confidence (0-1, default: 0.8)
}
```

**Response:**
```typescript
{
  fields: [{
    id: string;               // Unique field identifier
    name: string;             // Field name/label
    type: string;             // Field type
    metadata: {
      description?: string;   // Field description
      inputType?: string;     // HTML input type
      required?: boolean;     // Required field
      bounds?: {              // Screen coordinates
        x: number, y: number, width: number, height: number
      };
      confidence?: number;    // Detection confidence
    }
  }];
  windowInfo?: {
    title: string;            // Window title
    className: string;        // Window class
    handle: string;           // Window handle
    bounds: { x, y, width, height };
  };
  asyncJobId?: string;
}
```

**Example:**
```javascript
const result = await mcp.callTool('detect_fields', {
  contextHint: 'registration-form',
  confidence: 0.85,
  includeHidden: false,
  securityFlags: ['audit']
});

console.log(`Found ${result.fields.length} fields`);
result.fields.forEach(field => {
  console.log(`- ${field.name} (${field.type}): ${field.id}`);
});
```

#### 2. `type_text`

Types text into specified fields with advanced timing and security features.

**Parameters:**
```typescript
{
  fieldId: string;            // Target field ID from detect_fields
  text: string;               // Text to type
  options?: {
    delay?: number;           // Keystroke delay (0-5000ms, default: 50)
    clearFirst?: boolean;     // Clear field first (default: false)
    pressEnter?: boolean;     // Press Enter after typing (default: false)
    simulate?: boolean;       // Dry-run mode (default: false)
  };
  securityFlags?: string[];   // Security flags
}
```

**Response:**
```typescript
{
  success: boolean;           // Operation success
  charactersTyped?: number;   // Characters successfully typed
  timeTaken?: number;         // Operation duration (ms)
  asyncJobId?: string;        // Job tracking ID
  errorCode?: string;         // Error code if failed
  errorMessage?: string;      // Error description
}
```

**Examples:**

Basic typing:
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_email_001',
  text: 'user@example.com'
});
```

Advanced typing with options:
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_description_003',
  text: 'This is a long description that needs careful typing.',
  options: {
    delay: 75,        // Slower typing
    clearFirst: true, // Clear existing content
    pressEnter: false
  },
  securityFlags: ['audit']
});
```

Password field (automatically secured):
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_password_002',
  text: userPassword,
  options: {
    delay: 100,       // Slower for security
    clearFirst: true
  },
  securityFlags: ['sensitive', 'encrypted']
});
```

#### 3. `get_field_value`

Retrieves the current value from specified fields.

**Parameters:**
```typescript
{
  fieldId: string;            // Field ID to read from
  securityFlags?: string[];   // Security flags
  maxLength?: number;         // Max characters to retrieve (default: 10000)
}
```

**Response:**
```typescript
{
  value: string;              // Current field value
  fieldInfo?: {               // Updated field information
    id: string;
    name: string;
    type: string;
    metadata?: object;
  };
  isSecure?: boolean;         // Whether field contains sensitive data
  asyncJobId?: string;
  errorCode?: string;
  errorMessage?: string;
}
```

**Example:**
```javascript
const result = await mcp.callTool('get_field_value', {
  fieldId: 'field_username_001',
  maxLength: 500,
  securityFlags: ['audit']
});

console.log('Current value:', result.value);
console.log('Is secure field:', result.isSecure);
```

#### 4. `focus_field`

Focuses specified fields and brings windows to front.

**Parameters:**
```typescript
{
  fieldId: string;            // Field ID to focus
  securityFlags?: string[];   // Security flags
  bringToFront?: boolean;     // Bring window to front (default: true)
  scrollIntoView?: boolean;   // Scroll field into view (default: true)
}
```

**Response:**
```typescript
{
  success: boolean;           // Focus operation success
  previousFocus?: string;     // Previously focused element
  windowBroughtToFront?: boolean; // Whether window was activated
  asyncJobId?: string;
  errorCode?: string;
  errorMessage?: string;
}
```

**Example:**
```javascript
await mcp.callTool('focus_field', {
  fieldId: 'field_search_001',
  bringToFront: true,
  scrollIntoView: true
});
```

### Security Management Tools

#### 5. `security_grant_permission`

Grants or revokes typing permissions for sessions.

**Parameters:**
```typescript
{
  sessionId: string;          // Session identifier
  operation: string;          // 'mcp_root' or 'revoke_mcp_root'
  reason?: string;            // Reason for permission change
}
```

**Example:**
```javascript
// Grant permission
await mcp.callTool('security_grant_permission', {
  sessionId: 'session-123',
  operation: 'mcp_root',
  reason: 'Administrative data entry task'
});

// Revoke permission
await mcp.callTool('security_grant_permission', {
  sessionId: 'session-123',
  operation: 'revoke_mcp_root',
  reason: 'Task completed'
});
```

#### 6. `security_status`

Gets comprehensive security status and audit information.

**Parameters:**
```typescript
{
  includeHistory?: boolean;   // Include operation history
  includeStats?: boolean;     // Include usage statistics
}
```

**Example:**
```javascript
const status = await mcp.callTool('security_status', {
  includeHistory: true,
  includeStats: true
});

console.log('Permissions:', status.permissions);
console.log('Audit session:', status.auditSession);
console.log('Recent operations:', status.recentOperations);
```

#### 7. `security_rollback`

Rollback recent typing operations (Ctrl+Z functionality).

**Parameters:**
```typescript
{
  rollbackLast?: boolean;     // Rollback last operation
  operationId?: string;       // Specific operation to rollback
}
```

**Example:**
```javascript
// Rollback last operation
await mcp.callTool('security_rollback', {
  rollbackLast: true
});

// Rollback specific operation
await mcp.callTool('security_rollback', {
  operationId: 'job_1234567890_abcd'
});
```

### Utility Tools

#### 8. `get_window_info`

Gets information about available windows.

**Example:**
```javascript
const windows = await mcp.callTool('get_window_info', {
  windowTitle: 'Chrome'
});

windows.windows.forEach(window => {
  console.log(`${window.title} - ${window.isActive ? 'Active' : 'Inactive'}`);
});
```

#### 9. `take_screenshot`

Takes screenshots for debugging and field detection.

**Example:**
```javascript
const screenshot = await mcp.callTool('take_screenshot', {
  format: 'png',
  quality: 90,
  securityFlags: ['audit']
});

console.log('Screenshot saved:', screenshot.filePath);
```

## Troubleshooting

### Common Issues

#### 1. Installation Problems

**Issue**: `npm install -g @mcp-smart-typer/server` fails

**Solutions:**
```bash
# Try with elevated permissions
sudo npm install -g @mcp-smart-typer/server

# Or install locally
npm install @mcp-smart-typer/server

# Clear npm cache if needed
npm cache clean --force
```

**Issue**: Python helpers not downloading automatically

**Solutions:**
```bash
# Manual Python setup
cd packages/native-helpers
pip install -r requirements.txt
python -m src.main --setup

# Check Python version
python --version  # Should be 3.8+

# Install missing dependencies
pip install grpcio grpcio-tools pyautogui
```

#### 2. Permission Errors

**Issue**: `Typing not allowed. Set ALLOW_TYPING=true environment variable`

**Solutions:**

Option 1 - Environment Variable:
```bash
# Windows
set ALLOW_TYPING=true
mcp-server-smart-typer

# macOS/Linux
export ALLOW_TYPING=true
mcp-server-smart-typer
```

Option 2 - Claude Desktop Config:
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "env": {
        "ALLOW_TYPING": "true"
      }
    }
  }
}
```

Option 3 - Runtime Permission:
```javascript
await mcp.callTool('security_grant_permission', {
  sessionId: 'my-session',
  operation: 'mcp_root',
  reason: 'User authorized typing'
});
```

#### 3. Field Detection Issues

**Issue**: `detect_fields` returns empty results

**Solutions:**

1. **Check Window Focus**:
```javascript
// Ensure correct window is active
const windows = await mcp.callTool('get_window_info');
console.log('Active window:', windows.activeWindow);
```

2. **Lower Confidence Threshold**:
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  confidence: 0.5  // Lower threshold
});
```

3. **Include Hidden Fields**:
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  includeHidden: true
});
```

4. **Try Different Context Hints**:
```javascript
// Try various context hints
const hints = ['form', 'login', 'search', 'input', 'text-field'];
for (const hint of hints) {
  const result = await mcp.callTool('detect_fields', { contextHint: hint });
  if (result.fields.length > 0) {
    console.log(`Found fields with context: ${hint}`);
    break;
  }
}
```

#### 4. Connection Issues

**Issue**: gRPC connection to Python helpers fails

**Solutions:**

1. **Check Port Availability**:
```bash
# Check if port 50051 is in use
netstat -an | grep 50051  # macOS/Linux
netstat -an | findstr 50051  # Windows
```

2. **Restart Python Helpers**:
```bash
cd packages/native-helpers
python -m src.main --port 50052  # Try different port
```

3. **Check Logs**:
```bash
# Enable debug logging
export LOG_LEVEL=debug
mcp-server-smart-typer
```

4. **Manual gRPC Test**:
```bash
# Test gRPC connection
cd packages/native-helpers
python -c "
import grpc
from src.generated import ui_automation_pb2_grpc
channel = grpc.insecure_channel('localhost:50051')
stub = ui_automation_pb2_grpc.UIAutomationStub(channel)
print('gRPC connection successful')
"
```

#### 5. Typing Accuracy Issues

**Issue**: Text is typed incorrectly or incompletely

**Solutions:**

1. **Increase Typing Delay**:
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text here',
  options: {
    delay: 150  // Slower typing
  }
});
```

2. **Clear Field First**:
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text here',
  options: {
    clearFirst: true  // Clear existing content
  }
});
```

3. **Focus Field Before Typing**:
```javascript
// Focus first, then type
await mcp.callTool('focus_field', {
  fieldId: 'field_id',
  bringToFront: true
});

await new Promise(resolve => setTimeout(resolve, 500)); // Wait

await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text here'
});
```

### Debug Mode

Enable comprehensive debugging:

```bash
# Environment variables
export LOG_LEVEL=debug
export SECURE_LOGGING=true
export DRY_RUN_MODE=true

# Start with debug output
mcp-server-smart-typer --verbose
```

Debug output will include:
- Field detection details
- gRPC communication logs
- Security validation steps
- Timing information
- Error stack traces

### Log Analysis

Check audit logs for operation history:

**Windows**: `%USERPROFILE%\Documents\mcp-typer-logs\`
**macOS/Linux**: `~/Documents/mcp-typer-logs/`

```bash
# View recent logs
ls -la ~/Documents/mcp-typer-logs/

# Analyze specific log file
cat ~/Documents/mcp-typer-logs/2024-01-15_103045.log | jq .
```

### Performance Optimization

#### 1. Field Detection Performance
```javascript
// Cache field detection results
let cachedFields = null;

async function getFields(contextHint) {
  if (!cachedFields) {
    cachedFields = await mcp.callTool('detect_fields', {
      contextHint,
      confidence: 0.8
    });
  }
  return cachedFields;
}
```

#### 2. Batch Operations
```javascript
// Batch multiple typing operations
const fields = await mcp.callTool('detect_fields', { contextHint: 'form' });

const typingTasks = [
  { fieldId: fields.fields[0].id, text: 'John Doe' },
  { fieldId: fields.fields[1].id, text: 'john@example.com' },
  { fieldId: fields.fields[2].id, text: '555-0123' }
];

// Execute with minimal delay between operations
for (const task of typingTasks) {
  await mcp.callTool('type_text', {
    ...task,
    options: { delay: 30 } // Faster typing
  });
}
```

### Getting Help

#### 1. Enable Verbose Logging
```bash
mcp-server-smart-typer --verbose --log-level=debug
```

#### 2. Generate Diagnostic Report
```javascript
// Get comprehensive status
const status = await mcp.callTool('security_status', {
  includeHistory: true,
  includeStats: true
});

console.log('Diagnostic Report:', JSON.stringify(status, null, 2));
```

#### 3. Test Installation
```bash
# Run built-in tests
npm run test:e2e

# Test specific functionality
node test-mcp-server.js
```

#### 4. Community Support
- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and share usage patterns
- **Documentation**: Check latest updates in README.md

## Advanced Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOW_TYPING` | `false` | Enable typing operations globally |
| `SECURE_LOGGING` | `true` | Enable sensitive data masking |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warn, error) |
| `DRY_RUN_MODE` | `false` | Enable dry-run mode by default |
| `GRPC_PORT` | `50051` | gRPC server port |
| `NATIVE_CLIENT_TIMEOUT` | `5000` | Native client timeout (ms) |
| `AUDIT_LOG_DIR` | `~/Documents/mcp-typer-logs` | Audit log directory |

### Claude Desktop Advanced Config

```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "args": ["--enhanced-mode"],
      "env": {
        "ALLOW_TYPING": "true",
        "SECURE_LOGGING": "true",
        "LOG_LEVEL": "info",
        "DRY_RUN_MODE": "false",
        "GRPC_PORT": "50051",
        "NATIVE_CLIENT_TIMEOUT": "10000",
        "FIELD_DETECTION_TIMEOUT": "3000",
        "TYPING_DELAY_DEFAULT": "50",
        "AUDIT_LOG_RETENTION_DAYS": "30"
      },
      "capabilities": {
        "tools": true,
        "resources": false,
        "prompts": false
      }
    }
  }
}
```

This comprehensive documentation provides everything needed to install, configure, and use MCP Smart Typer effectively with Claude Desktop and other MCP clients.
