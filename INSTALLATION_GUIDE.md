# MCP Smart Typer - Complete Installation Guide

## Overview

This guide provides step-by-step instructions for installing and configuring MCP Smart Typer with Claude Desktop integration. Choose the installation method that best fits your needs.

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+ (primary support), macOS 10.15+, or Linux Ubuntu 18.04+
- **Node.js**: Version 18.0 or higher
- **Python**: Version 3.8 or higher
- **Memory**: 512MB RAM available
- **Disk Space**: 200MB free space

### Recommended Requirements

- **Operating System**: Windows 11, macOS 12+, or Linux Ubuntu 20.04+
- **Node.js**: Version 20.0 or higher
- **Python**: Version 3.10 or higher
- **Memory**: 1GB RAM available
- **Disk Space**: 500MB free space

### Additional Requirements

- **Claude Desktop**: Latest version for AI integration
- **Internet Connection**: Required for initial setup and package downloads
- **Administrator Access**: May be required for global installations

## Installation Methods

### Method 1: NPM Global Installation (Recommended)

This is the simplest method for most users.

#### Step 1: Verify Prerequisites

```bash
# Check Node.js version (should be 18+)
node --version

# Check npm version
npm --version

# Check Python version (should be 3.8+)
python --version
# or try python3 on some systems
python3 --version
```

If any tools are missing or outdated:

**Install Node.js:**
- Download from [nodejs.org](https://nodejs.org/)
- Choose the LTS version
- Verify installation: `node --version`

**Install Python:**
- Download from [python.org](https://python.org/)
- Choose version 3.8 or higher
- During installation, check "Add Python to PATH"
- Verify installation: `python --version`

#### Step 2: Install MCP Smart Typer

```bash
# Install globally via npm
npm install -g @mcp-smart-typer/server

# Verify installation
mcp-server-smart-typer --version
```

**If installation fails with permission errors:**

**Linux/macOS:**
```bash
sudo npm install -g @mcp-smart-typer/server
```

**Windows (Run as Administrator):**
```cmd
npm install -g @mcp-smart-typer/server
```

**Alternative: Configure npm for user directory:**
```bash
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g @mcp-smart-typer/server
```

#### Step 3: Python Helper Auto-Setup

The MCP Smart Typer server will automatically download and configure Python helpers on first run. To verify:

```bash
# Start the server (this will trigger auto-setup)
mcp-server-smart-typer --setup

# You should see output like:
# ✓ Python helpers detected
# ✓ gRPC server started on port 50051
# ✓ MCP server ready
```

#### Step 4: Test Installation

```bash
# Test the installation
mcp-server-smart-typer --test

# Should output:
# ✓ MCP server initialization: OK
# ✓ Python helpers connection: OK
# ✓ Field detection: OK
# ✓ Security system: OK
# All tests passed!
```

### Method 2: From Source (Development)

This method is recommended for developers or users who want the latest features.

#### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/mcp-smart-typer/mcp-smart-typer.git
cd mcp-smart-typer

# Verify you have the files
ls -la
```

#### Step 2: Install Dependencies

```bash
# Install root dependencies
npm install

# Install MCP server dependencies
cd packages/mcp-server-smart-typer
npm install

# Build the TypeScript code
npm run build

# Return to root
cd ../..
```

#### Step 3: Setup Python Helpers

```bash
# Navigate to Python helpers
cd packages/native-helpers

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Test Python helpers
python -m src.main --test
```

#### Step 4: Build and Link

```bash
# Return to MCP server directory
cd ../mcp-server-smart-typer

# Create global link
npm link

# Verify installation
mcp-server-smart-typer --version
```

### Method 3: Local Installation (No Global Install)

This method installs MCP Smart Typer locally without global permissions.

#### Step 1: Create Project Directory

```bash
# Create directory for MCP Smart Typer
mkdir ~/mcp-smart-typer-local
cd ~/mcp-smart-typer-local

# Initialize npm
npm init -y
```

#### Step 2: Install Locally

```bash
# Install MCP Smart Typer locally
npm install @mcp-smart-typer/server

# Or install from source
git clone https://github.com/mcp-smart-typer/mcp-smart-typer.git
cd mcp-smart-typer
npm install
npm run build
```

#### Step 3: Create Startup Script

```bash
# Create startup script
cat > start-mcp-typer.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
if [ -d "node_modules/@mcp-smart-typer/server" ]; then
    # NPM install
    npx mcp-server-smart-typer "$@"
else
    # Source install
    node mcp-smart-typer/packages/mcp-server-smart-typer/dist/index.js "$@"
fi
EOF

chmod +x start-mcp-typer.sh

# Test the script
./start-mcp-typer.sh --version
```

## Python Helper Setup

### Automatic Setup (Recommended)

The MCP Smart Typer server automatically handles Python helper setup:

1. **Detection**: Checks if Python helpers are available
2. **Download**: Downloads pre-built binaries if needed
3. **Configuration**: Sets up gRPC communication
4. **Verification**: Tests the connection

```bash
# Start server with automatic setup
mcp-server-smart-typer --setup

# Check setup status
mcp-server-smart-typer --check-helpers
```

### Manual Setup

If automatic setup fails, you can set up Python helpers manually:

#### Step 1: Navigate to Python Helpers

```bash
cd packages/native-helpers
# or if you installed via npm:
cd node_modules/@mcp-smart-typer/server/packages/native-helpers
```

#### Step 2: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# If you encounter permission errors:
pip install --user -r requirements.txt

# Or use a virtual environment:
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### Step 3: Test Python Helpers

```bash
# Test the Python helper service
python -m src.main --test

# Should output:
# ✓ gRPC server test: OK
# ✓ UI automation test: OK
# ✓ Field detection test: OK
# All Python helper tests passed!
```

#### Step 4: Start Python Helper Service

```bash
# Start the gRPC server
python -m src.main

# You should see:
# gRPC server started on port 50051
# UI automation service ready
# Waiting for connections...
```

### Troubleshooting Python Setup

#### Common Python Issues

**1. Module Not Found Errors:**
```bash
# Install missing modules
pip install grpcio grpcio-tools
pip install pyautogui pillow numpy
pip install protobuf
```

**2. Permission Errors:**
```bash
# Use user installation
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Python Version Issues:**
```bash
# Check Python version
python --version

# Try python3 if python points to older version
python3 --version
python3 -m pip install -r requirements.txt
```

**4. Windows-specific Issues:**
```cmd
# Install Visual C++ Build Tools if needed
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Use Python from Microsoft Store or python.org
# Avoid Anaconda/Miniconda for this project
```

## Claude Desktop Integration

### Step 1: Locate Configuration File

The Claude Desktop configuration file location depends on your operating system:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
Full path example: `C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json`

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/claude/claude_desktop_config.json
```

### Step 2: Create Configuration Directory

If the configuration file doesn't exist, create the directory:

**Windows:**
```cmd
mkdir "%APPDATA%\Claude"
```

**macOS/Linux:**
```bash
mkdir -p ~/.config/claude
# or on macOS:
mkdir -p "~/Library/Application Support/Claude"
```

### Step 3: Basic Configuration

Create or edit the `claude_desktop_config.json` file:

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

### Step 4: Advanced Configuration

For more control over the server behavior:

```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "args": ["--enhanced-mode"],
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "info",
        "SECURE_LOGGING": "true",
        "DRY_RUN_MODE": "false",
        "GRPC_PORT": "50051",
        "NATIVE_CLIENT_TIMEOUT": "5000",
        "AUDIT_LOG_DIR": "~/Documents/mcp-typer-logs"
      }
    }
  }
}
```

### Step 5: Configuration for Local Installation

If you installed locally instead of globally:

```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "node",
      "args": [
        "/full/path/to/mcp-smart-typer/packages/mcp-server-smart-typer/dist/index.js"
      ],
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

**Windows path example:**
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "node",
      "args": [
        "C:\\Users\\YourName\\mcp-smart-typer-local\\mcp-smart-typer\\packages\\mcp-server-smart-typer\\dist\\index.js"
      ],
      "env": {
        "ALLOW_TYPING": "true"
      }
    }
  }
}
```

### Step 6: Validate Configuration

Test your JSON configuration:

**Using online validator:**
- Copy your JSON to [jsonlint.com](https://jsonlint.com/)
- Verify it's valid JSON

**Using command line:**
```bash
# Linux/macOS
cat ~/.config/claude/claude_desktop_config.json | jq .

# Windows (if you have jq installed)
type "%APPDATA%\Claude\claude_desktop_config.json" | jq .
```

### Step 7: Restart Claude Desktop

1. **Completely quit Claude Desktop**
   - Close all Claude windows
   - Check system tray/menu bar for running Claude processes
   - Force quit if necessary

2. **Wait 10 seconds**

3. **Restart Claude Desktop**

4. **Verify MCP Integration**
   - Look for MCP server status in Claude
   - Should see "smart-typer" as connected

## Environment Variables

Configure MCP Smart Typer behavior using environment variables.

### Core Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOW_TYPING` | `false` | **Required**: Enable typing operations |
| `LOG_LEVEL` | `info` | Logging level: `debug`, `info`, `warn`, `error` |
| `SECURE_LOGGING` | `true` | Enable sensitive data masking in logs |

### Advanced Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN_MODE` | `false` | Enable dry-run mode by default |
| `GRPC_PORT` | `50051` | Port for Python helper gRPC server |
| `NATIVE_CLIENT_TIMEOUT` | `5000` | Timeout for native client (ms) |
| `AUDIT_LOG_DIR` | `~/Documents/mcp-typer-logs` | Directory for audit logs |
| `FIELD_DETECTION_TIMEOUT` | `3000` | Timeout for field detection (ms) |
| `TYPING_DELAY_DEFAULT` | `50` | Default delay between keystrokes (ms) |

### Setting Environment Variables

**Windows Command Prompt:**
```cmd
set ALLOW_TYPING=true
set LOG_LEVEL=debug
mcp-server-smart-typer
```

**Windows PowerShell:**
```powershell
$env:ALLOW_TYPING="true"
$env:LOG_LEVEL="debug"
mcp-server-smart-typer
```

**macOS/Linux:**
```bash
export ALLOW_TYPING=true
export LOG_LEVEL=debug
mcp-server-smart-typer
```

**Persistent Environment Variables:**

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
export ALLOW_TYPING=true
export LOG_LEVEL=info
export SECURE_LOGGING=true
```

**Windows System Environment:**
1. Open System Properties
2. Click "Environment Variables"
3. Add new system or user variables
4. Restart command prompt/Claude Desktop

## Security Configuration

### Permission Setup

MCP Smart Typer requires explicit permission to perform typing operations. Set up permissions using one of these methods:

#### Method 1: Environment Variable (Recommended)
```bash
export ALLOW_TYPING=true
```

#### Method 2: Claude Desktop Configuration
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

#### Method 3: Runtime Permission Grant
```javascript
// Grant permission through Claude
await mcp.callTool('security_grant_permission', {
  sessionId: 'your-session-id',
  operation: 'mcp_root',
  reason: 'User authorized typing operations'
});
```

### Audit Logging Setup

Enable comprehensive audit logging:

```bash
# Enable secure logging
export SECURE_LOGGING=true

# Set custom audit log directory (optional)
export AUDIT_LOG_DIR=/path/to/secure/logs

# Set log retention (optional)
export AUDIT_LOG_RETENTION_DAYS=30
```

Audit logs will be created in:
- **Windows**: `%USERPROFILE%\Documents\mcp-typer-logs\`
- **macOS/Linux**: `~/Documents/mcp-typer-logs/`

### Security Best Practices

1. **Use Secure Logging**: Always enable `SECURE_LOGGING=true`
2. **Monitor Audit Logs**: Regularly review audit logs for security
3. **Use Dry-Run Mode**: Test operations with `DRY_RUN_MODE=true`
4. **Limit Permissions**: Only grant permissions when needed
5. **Secure Log Storage**: Ensure audit log directory has proper permissions

## Verification and Testing

### Basic Functionality Test

```bash
# Test MCP server
mcp-server-smart-typer --test

# Expected output:
# ✓ MCP server initialization: OK
# ✓ Python helpers connection: OK
# ✓ Field detection: OK
# ✓ Security system: OK
# ✓ Audit logging: OK
# All tests passed!
```

### Python Helper Test

```bash
# Test Python helpers separately
cd packages/native-helpers
python -m src.main --test

# Expected output:
# ✓ gRPC server: OK
# ✓ UI automation: OK
# ✓ Field detection: OK
# ✓ Screenshot capture: OK
# All Python helper tests passed!
```

### Claude Desktop Integration Test

1. **Start Claude Desktop**
2. **Check MCP Server Status**:
   - Look for "smart-typer" in connected servers
   - Should show as "Connected" or "Active"

3. **Test Basic Tool**:
   Ask Claude: "Please check the MCP Smart Typer status using the security_status tool."

4. **Test Field Detection**:
   - Open a web page with a form
   - Ask Claude: "Please detect input fields on this page."

### End-to-End Test

```bash
# Run comprehensive test suite
npm run test:e2e

# This will test:
# - Field detection accuracy
# - Typing functionality
# - Security features
# - Audit logging
# - Error handling
```

## Troubleshooting Installation

### Common Installation Issues

#### 1. Permission Denied Errors

**Problem**: `npm install -g` fails with permission errors

**Solutions**:
```bash
# Option 1: Use sudo (Linux/macOS)
sudo npm install -g @mcp-smart-typer/server

# Option 2: Configure npm for user directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Option 3: Install locally
npm install @mcp-smart-typer/server
npx mcp-server-smart-typer
```

#### 2. Python Import Errors

**Problem**: `ModuleNotFoundError` when starting Python helpers

**Solutions**:
```bash
# Install missing Python packages
pip install grpcio grpcio-tools pyautogui

# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Try python3 instead of python
python3 -m pip install -r requirements.txt
```

#### 3. gRPC Connection Failures

**Problem**: `ECONNREFUSED` errors when connecting to Python helpers

**Solutions**:
```bash
# Check if port is in use
netstat -an | grep 50051  # Linux/macOS
netstat -an | findstr 50051  # Windows

# Try different port
export GRPC_PORT=50052
python -m src.main --port 50052

# Check firewall settings
# Add exceptions for Python and Node.js
```

#### 4. Claude Desktop Not Detecting Server

**Problem**: MCP server doesn't appear in Claude Desktop

**Solutions**:
1. **Verify config file location**:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/claude/claude_desktop_config.json`

2. **Validate JSON syntax**:
   ```bash
   cat claude_desktop_config.json | jq .
   ```

3. **Use full path for local installation**:
   ```json
   {
     "mcpServers": {
       "smart-typer": {
         "command": "node",
         "args": ["/full/path/to/dist/index.js"]
       }
     }
   }
   ```

4. **Restart Claude Desktop completely**

### Getting Help

If you encounter issues not covered in this guide:

1. **Check the Troubleshooting FAQ**: See `TROUBLESHOOTING_FAQ.md`
2. **Enable Debug Logging**:
   ```bash
   export LOG_LEVEL=debug
   mcp-server-smart-typer --verbose
   ```
3. **Create GitHub Issue**: Include system info, error logs, and reproduction steps
4. **Check GitHub Discussions**: Search for similar issues

## Platform-Specific Instructions

### Windows Installation

1. **Install Prerequisites**:
   - Download Node.js from [nodejs.org](https://nodejs.org/)
   - Download Python from [python.org](https://python.org/)
   - During Python installation, check "Add Python to PATH"

2. **Install MCP Smart Typer**:
   ```cmd
   npm install -g @mcp-smart-typer/server
   ```

3. **Configure Claude Desktop**:
   - Config file: `%APPDATA%\Claude\claude_desktop_config.json`
   - Use forward slashes or double backslashes in paths

4. **Set Environment Variables**:
   ```cmd
   setx ALLOW_TYPING true
   setx LOG_LEVEL info
   ```

### macOS Installation

1. **Install Prerequisites**:
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Node.js and Python
   brew install node python
   ```

2. **Install MCP Smart Typer**:
   ```bash
   npm install -g @mcp-smart-typer/server
   ```

3. **Configure Claude Desktop**:
   - Config file: `~/Library/Application Support/Claude/claude_desktop_config.json`

4. **Set Environment Variables**:
   ```bash
   echo 'export ALLOW_TYPING=true' >> ~/.zshrc
   source ~/.zshrc
   ```

### Linux Installation

1. **Install Prerequisites**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install nodejs npm python3 python3-pip python3-tk

   # CentOS/RHEL/Fedora
   sudo dnf install nodejs npm python3 python3-pip python3-tkinter
   ```

2. **Install MCP Smart Typer**:
   ```bash
   npm install -g @mcp-smart-typer/server
   ```

3. **Configure Claude Desktop**:
   - Config file: `~/.config/claude/claude_desktop_config.json`

4. **Set Environment Variables**:
   ```bash
   echo 'export ALLOW_TYPING=true' >> ~/.bashrc
   source ~/.bashrc
   ```

## Next Steps

After successful installation:

1. **Read the Documentation**: Check `DOCUMENTATION.md` for comprehensive usage guide
2. **Review Security**: Read `SECURITY.md` for security features and best practices
3. **Try Examples**: Test with simple form filling tasks
4. **Configure Preferences**: Adjust environment variables as needed
5. **Set Up Monitoring**: Review audit logs regularly for security

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/mcp-smart-typer/mcp-smart-typer/issues)
- **GitHub Discussions**: [Ask questions and share experiences](https://github.com/mcp-smart-typer/mcp-smart-typer/discussions)
- **Documentation**: Latest updates in README.md

This completes the installation guide. Your MCP Smart Typer should now be ready for use with Claude Desktop!
