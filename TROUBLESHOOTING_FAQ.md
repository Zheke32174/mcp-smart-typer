# MCP Smart Typer - Troubleshooting FAQ

## Quick Reference

| Problem | Solution |
|---------|----------|
| [Permission denied errors](#permission-denied) | Set `ALLOW_TYPING=true` or grant runtime permissions |
| [Python helpers not working](#python-helpers-issues) | Check Python version (3.8+), run manual setup |
| [No fields detected](#field-detection-issues) | Lower confidence threshold, try different context hints |
| [Text typing incomplete](#typing-accuracy-issues) | Increase delay, clear field first, focus before typing |
| [gRPC connection fails](#connection-issues) | Check port availability, restart services |
| [Claude Desktop not working](#claude-desktop-issues) | Verify config file location and syntax |

## Installation Issues

### Q: NPM installation fails with permission errors

**Error Messages:**
```
EACCES: permission denied, mkdir '/usr/local/lib/node_modules/@mcp-smart-typer'
npm ERR! Error: EACCES: permission denied
```

**Solutions:**

1. **Use sudo (Linux/macOS):**
```bash
sudo npm install -g @mcp-smart-typer/server
```

2. **Configure npm for user directory:**
```bash
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g @mcp-smart-typer/server
```

3. **Install locally instead:**
```bash
npm install @mcp-smart-typer/server
npx mcp-server-smart-typer
```

### Q: Package not found or 404 error

**Error Messages:**
```
npm ERR! 404 Not Found - GET https://registry.npmjs.org/@mcp-smart-typer%2fserver
npm ERR! 404 '@mcp-smart-typer/server@latest' is not in this registry.
```

**Solutions:**

1. **Install from source:**
```bash
git clone https://github.com/mcp-smart-typer/mcp-smart-typer.git
cd mcp-smart-typer
npm install
cd packages/mcp-server-smart-typer
npm install
npm run build
npm link
```

2. **Use local path in Claude config:**
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "node",
      "args": ["/path/to/mcp-smart-typer/packages/mcp-server-smart-typer/dist/index.js"]
    }
  }
}
```

## Permission Denied

### Q: "Typing not allowed" error message

**Error Messages:**
```
Typing not allowed. Set ALLOW_TYPING=true environment variable or grant explicit MCP root permission.
```

**Solutions (Choose One):**

1. **Environment Variable (Recommended):**
```bash
# Windows Command Prompt
set ALLOW_TYPING=true
mcp-server-smart-typer

# Windows PowerShell
$env:ALLOW_TYPING="true"
mcp-server-smart-typer

# macOS/Linux
export ALLOW_TYPING=true
mcp-server-smart-typer
```

2. **Claude Desktop Configuration:**
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

3. **Runtime Permission Grant:**
```javascript
await mcp.callTool('security_grant_permission', {
  sessionId: 'your-session-id',
  operation: 'mcp_root',
  reason: 'User authorized typing operations'
});
```

4. **Request-level Permission:**
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text',
  securityFlags: ['mcp_root_permission']
});
```

### Q: Permission works but then stops working

**Possible Causes:**
- Session expired
- Server restarted without environment variable
- Permission was revoked

**Solutions:**

1. **Check current permissions:**
```javascript
const status = await mcp.callTool('security_status', {
  includeHistory: true
});
console.log('Current permissions:', status.permissions);
```

2. **Re-grant permissions:**
```javascript
await mcp.callTool('security_grant_permission', {
  sessionId: 'your-session-id',
  operation: 'mcp_root',
  reason: 'Re-authorizing after session reset'
});
```

3. **Use persistent environment variable:**
Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
export ALLOW_TYPING=true
```

## Python Helpers Issues

### Q: Python helpers fail to download or start

**Error Messages:**
```
Failed to connect to native client: Error: connect ECONNREFUSED 127.0.0.1:50051
Python helper service not available
grpc.aio._call.AioRpcError: <AioRpcError of RPC that terminated with: status = StatusCode.UNAVAILABLE
```

**Solutions:**

1. **Check Python Version:**
```bash
python --version  # Should be 3.8+
python3 --version # Try python3 if python doesn't work
```

2. **Manual Python Setup:**
```bash
cd packages/native-helpers
pip install -r requirements.txt

# If pip install fails, try:
pip install --user -r requirements.txt

# Or with python3:
pip3 install -r requirements.txt
```

3. **Install Missing Dependencies:**
```bash
pip install grpcio grpcio-tools pyautogui pillow numpy
```

4. **Test Python Helper Standalone:**
```bash
cd packages/native-helpers
python -m src.main --test
```

5. **Check Port Conflicts:**
```bash
# Windows
netstat -an | findstr :50051

# macOS/Linux
lsof -i :50051
netstat -tulpn | grep :50051
```

6. **Try Different Port:**
```bash
# Start Python helper on different port
python -m src.main --port 50052

# Update server config
export GRPC_PORT=50052
mcp-server-smart-typer
```

### Q: Python import errors

**Error Messages:**
```
ModuleNotFoundError: No module named 'grpc'
ImportError: No module named 'google.protobuf'
ModuleNotFoundError: No module named 'pyautogui'
```

**Solutions:**

1. **Install gRPC:**
```bash
pip install grpcio grpcio-tools
```

2. **Install PyAutoGUI:**
```bash
pip install pyautogui

# On Linux, may also need:
sudo apt-get install python3-tk python3-dev
```

3. **Install Protobuf:**
```bash
pip install protobuf
```

4. **Use Virtual Environment:**
```bash
cd packages/native-helpers
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Field Detection Issues

### Q: detect_fields returns no results

**Symptoms:**
- Empty fields array
- "No input fields detected" message
- Fields present on screen but not detected

**Solutions:**

1. **Lower Confidence Threshold:**
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  confidence: 0.3  // Much lower threshold
});
```

2. **Try Different Context Hints:**
```javascript
const contextHints = [
  'form', 'login', 'search', 'input', 'text-field', 
  'registration', 'contact', 'signup', 'textbox'
];

for (const hint of contextHints) {
  const result = await mcp.callTool('detect_fields', { 
    contextHint: hint,
    confidence: 0.5 
  });
  if (result.fields.length > 0) {
    console.log(`Success with context: ${hint}`);
    console.log('Fields found:', result.fields);
    break;
  }
}
```

3. **Include Hidden Fields:**
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  includeHidden: true
});
```

4. **Check Active Window:**
```javascript
const windowInfo = await mcp.callTool('get_window_info');
console.log('Active window:', windowInfo.activeWindow);
console.log('Available windows:');
windowInfo.windows.forEach(w => {
  console.log(`- ${w.title} (${w.isActive ? 'ACTIVE' : 'inactive'})`);
});
```

5. **Take Screenshot for Debugging:**
```javascript
const screenshot = await mcp.callTool('take_screenshot', {
  format: 'png',
  securityFlags: ['audit']
});
console.log('Screenshot saved:', screenshot.filePath);
```

6. **Focus Correct Window:**
```javascript
// Focus specific window first
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  windowTitle: 'Chrome',  // or specific window title
  confidence: 0.7
});
```

### Q: Fields detected but wrong information

**Symptoms:**
- Incorrect field types
- Wrong field names
- Missing field metadata

**Solutions:**

1. **Provide Better Context:**
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'login-form-with-username-and-password',  // More specific
  confidence: 0.8
});
```

2. **Re-detect After Page Changes:**
```javascript
// Wait for page to fully load
await new Promise(resolve => setTimeout(resolve, 2000));

const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  confidence: 0.8
});
```

3. **Check Field Bounds:**
```javascript
fields.fields.forEach(field => {
  console.log(`Field: ${field.name}`);
  console.log(`  ID: ${field.id}`);
  console.log(`  Type: ${field.type}`);
  console.log(`  Bounds: ${JSON.stringify(field.metadata?.bounds)}`);
  console.log(`  Confidence: ${field.metadata?.confidence}`);
});
```

## Typing Accuracy Issues

### Q: Text is typed incorrectly or incompletely

**Symptoms:**
- Missing characters
- Wrong characters
- Typing stops mid-text
- Special characters not working

**Solutions:**

1. **Increase Typing Delay:**
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text here',
  options: {
    delay: 150  // Slower typing (default is 50ms)
  }
});
```

2. **Clear Field Before Typing:**
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text here',
  options: {
    clearFirst: true,  // Clear existing content
    delay: 100
  }
});
```

3. **Focus Field First:**
```javascript
// Focus field before typing
await mcp.callTool('focus_field', {
  fieldId: 'field_id',
  bringToFront: true,
  scrollIntoView: true
});

// Wait a moment
await new Promise(resolve => setTimeout(resolve, 500));

// Then type
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text here'
});
```

4. **Handle Special Characters:**
```javascript
// For text with special characters
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'Text with "quotes" and symbols: @#$%',
  options: {
    delay: 200,  // Extra slow for special chars
    clearFirst: true
  }
});
```

5. **Test with Simulation First:**
```javascript
// Test what would happen
const result = await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'test text',
  options: {
    simulate: true  // Dry run mode
  }
});

console.log('Would succeed:', result.success);
if (result.dryRunResult) {
  console.log('Warnings:', result.dryRunResult.warnings);
}
```

### Q: Text appears in wrong field

**Symptoms:**
- Text typed to different field than intended
- Multiple fields receiving same text
- Focus jumps between fields

**Solutions:**

1. **Verify Field ID:**
```javascript
// Re-detect fields to get current IDs
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form'
});

// Find the correct field
const targetField = fields.fields.find(f => 
  f.name.toLowerCase().includes('username') ||
  f.name.toLowerCase().includes('email')
);

if (targetField) {
  await mcp.callTool('type_text', {
    fieldId: targetField.id,
    text: 'your text'
  });
}
```

2. **Focus and Verify:**
```javascript
// Focus the field
const focusResult = await mcp.callTool('focus_field', {
  fieldId: 'field_id'
});

if (focusResult.success) {
  // Wait for focus to take effect
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // Type the text
  await mcp.callTool('type_text', {
    fieldId: 'field_id',
    text: 'your text'
  });
}
```

3. **Check Field Value After Typing:**
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'test text'
});

// Verify it was typed correctly
const value = await mcp.callTool('get_field_value', {
  fieldId: 'field_id'
});

console.log('Field now contains:', value.value);
```

## Connection Issues

### Q: gRPC connection failures

**Error Messages:**
```
Error: connect ECONNREFUSED 127.0.0.1:50051
grpc.aio._call.AioRpcError: <AioRpcError of RPC that terminated with: status = StatusCode.UNAVAILABLE
Failed to establish gRPC connection
```

**Solutions:**

1. **Check if Port is Available:**
```bash
# Windows
netstat -an | findstr :50051

# macOS/Linux
lsof -i :50051
ss -tlnp | grep :50051
```

2. **Start Python Helper Manually:**
```bash
cd packages/native-helpers
python -m src.main

# Should see output like:
# gRPC server started on port 50051
# Waiting for connections...
```

3. **Try Different Port:**
```bash
# Terminal 1: Start Python helper
cd packages/native-helpers
python -m src.main --port 50052

# Terminal 2: Start MCP server
export GRPC_PORT=50052
mcp-server-smart-typer
```

4. **Check Firewall/Antivirus:**
- Add exception for Python and Node.js
- Temporarily disable firewall to test
- Check if antivirus is blocking gRPC connections

5. **Test gRPC Connection Manually:**
```python
# Test script - save as test_grpc.py
import grpc
import sys
sys.path.append('src')
from generated import ui_automation_pb2_grpc

try:
    channel = grpc.insecure_channel('localhost:50051')
    stub = ui_automation_pb2_grpc.UIAutomationStub(channel)
    print("gRPC connection successful!")
except Exception as e:
    print(f"gRPC connection failed: {e}")
```

6. **Restart in Correct Order:**
```bash
# 1. Kill any existing processes
pkill -f "src.main"
pkill -f "mcp-server-smart-typer"

# 2. Start Python helper first
cd packages/native-helpers
python -m src.main &

# 3. Wait a moment
sleep 2

# 4. Start MCP server
mcp-server-smart-typer
```

### Q: Connection works initially but then fails

**Symptoms:**
- Works for first few operations
- Then starts failing with connection errors
- Intermittent failures

**Solutions:**

1. **Increase Timeout:**
```bash
export NATIVE_CLIENT_TIMEOUT=10000  # 10 seconds
mcp-server-smart-typer
```

2. **Check for Resource Leaks:**
```javascript
// Monitor connection status
const status = await mcp.callTool('security_status', {
  includeStats: true
});
console.log('Connection stats:', status.connectionStats);
```

3. **Restart Python Helper Periodically:**
```bash
# Create restart script
cat > restart_helper.sh << 'EOF'
#!/bin/bash
while true; do
    cd packages/native-helpers
    python -m src.main
    echo "Python helper crashed, restarting in 5 seconds..."
    sleep 5
done
EOF
chmod +x restart_helper.sh
./restart_helper.sh &
```

## Claude Desktop Issues

### Q: MCP server not appearing in Claude Desktop

**Symptoms:**
- No smart-typer tools available in Claude
- Claude shows "No MCP servers configured"
- Tools work from command line but not in Claude

**Solutions:**

1. **Verify Config File Location:**

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/claude/claude_desktop_config.json
```

2. **Check Config File Syntax:**
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "args": [],
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

3. **Validate JSON:**
```bash
# Test if JSON is valid
cat claude_desktop_config.json | jq .
# or use online JSON validator
```

4. **Use Full Path if Global Install Failed:**
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "node",
      "args": [
        "C:\\path\\to\\mcp-smart-typer\\packages\\mcp-server-smart-typer\\dist\\index.js"
      ],
      "env": {
        "ALLOW_TYPING": "true"
      }
    }
  }
}
```

5. **Restart Claude Desktop:**
- Completely quit Claude Desktop
- Wait 10 seconds
- Restart Claude Desktop
- Check for MCP server in status

6. **Check Claude Desktop Logs:**

**Windows:**
```
%APPDATA%\Claude\logs\
```

**macOS:**
```
~/Library/Logs/Claude/
```

Look for error messages related to MCP or smart-typer.

### Q: Claude Desktop connects but tools don't work

**Symptoms:**
- Claude shows smart-typer is connected
- Tools appear in Claude's tool list
- But get errors when trying to use tools

**Solutions:**

1. **Check Environment Variables in Config:**
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "debug",
        "SECURE_LOGGING": "true"
      }
    }
  }
}
```

2. **Test Tools Directly:**
Ask Claude to run:
```
Please test the MCP Smart Typer connection by running the security_status tool.
```

3. **Enable Debug Logging:**
```json
{
  "mcpServers": {
    "smart-typer": {
      "command": "mcp-server-smart-typer",
      "args": ["--verbose"],
      "env": {
        "ALLOW_TYPING": "true",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

4. **Grant Permissions Through Claude:**
Ask Claude to run:
```
Please grant MCP root permissions for this session using the security_grant_permission tool.
```

## Performance Issues

### Q: Field detection is very slow

**Solutions:**

1. **Increase Confidence Threshold:**
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  confidence: 0.9  // Higher threshold = faster detection
});
```

2. **Use Specific Window:**
```javascript
const fields = await mcp.callTool('detect_fields', {
  contextHint: 'form',
  windowTitle: 'Chrome',  // Focus specific window
  confidence: 0.8
});
```

3. **Cache Results:**
```javascript
let cachedFields = null;
let cacheTime = 0;
const CACHE_DURATION = 30000; // 30 seconds

async function getFields(contextHint) {
  const now = Date.now();
  if (cachedFields && (now - cacheTime) < CACHE_DURATION) {
    return cachedFields;
  }
  
  cachedFields = await mcp.callTool('detect_fields', {
    contextHint,
    confidence: 0.8
  });
  cacheTime = now;
  return cachedFields;
}
```

### Q: Typing is too slow

**Solutions:**

1. **Reduce Typing Delay:**
```javascript
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'your text',
  options: {
    delay: 20  // Faster typing (default is 50ms)
  }
});
```

2. **Batch Operations:**
```javascript
// Type multiple fields quickly
const typingTasks = [
  { fieldId: 'field1', text: 'value1' },
  { fieldId: 'field2', text: 'value2' },
  { fieldId: 'field3', text: 'value3' }
];

for (const task of typingTasks) {
  await mcp.callTool('type_text', {
    ...task,
    options: { delay: 25 }
  });
}
```

## Security and Audit Issues

### Q: Audit logs not being created

**Symptoms:**
- No log files in `~/Documents/mcp-typer-logs/`
- Security operations not being logged
- Missing audit trail

**Solutions:**

1. **Enable Secure Logging:**
```bash
export SECURE_LOGGING=true
mcp-server-smart-typer
```

2. **Check Log Directory Permissions:**
```bash
# Create directory if it doesn't exist
mkdir -p ~/Documents/mcp-typer-logs
chmod 755 ~/Documents/mcp-typer-logs
```

3. **Set Custom Log Directory:**
```bash
export AUDIT_LOG_DIR=/path/to/custom/logs
mcp-server-smart-typer
```

4. **Check Current Audit Status:**
```javascript
const status = await mcp.callTool('security_status', {
  includeHistory: true
});
console.log('Audit status:', status.auditSession);
console.log('Log directory:', status.logDirectory);
```

### Q: Sensitive data appearing in logs

**Solutions:**

1. **Ensure Secure Logging is Enabled:**
```bash
export SECURE_LOGGING=true
```

2. **Use Proper Security Flags:**
```javascript
await mcp.callTool('type_text', {
  fieldId: 'password_field',
  text: 'sensitive_data',
  securityFlags: ['sensitive', 'encrypted']
});
```

3. **Check Log Masking:**
```bash
# Logs should show masked values like:
# "text": "[REDACTED]" for password fields
# "text": "us****@example.com" for email fields
tail -f ~/Documents/mcp-typer-logs/latest.log
```

## Emergency Recovery

### Q: Server is completely stuck or unresponsive

**Solutions:**

1. **Force Kill All Processes:**
```bash
# Windows
taskkill /f /im node.exe
taskkill /f /im python.exe

# macOS/Linux
pkill -f mcp-server-smart-typer
pkill -f "src.main"
pkill -f python
```

2. **Clean Restart:**
```bash
# 1. Kill processes
pkill -f mcp-server-smart-typer
pkill -f python

# 2. Wait
sleep 5

# 3. Clean temporary files
rm -rf /tmp/mcp-smart-typer-*

# 4. Restart Python helper
cd packages/native-helpers
python -m src.main &

# 5. Wait for it to start
sleep 3

# 6. Start MCP server
mcp-server-smart-typer
```

3. **Reset Configuration:**
```bash
# Backup current config
cp ~/.config/claude/claude_desktop_config.json ~/.config/claude/claude_desktop_config.json.backup

# Use minimal config
cat > ~/.config/claude/claude_desktop_config.json << 'EOF'
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
EOF
```

### Q: Rollback operations not working

**Solutions:**

1. **Check Rollback History:**
```javascript
const status = await mcp.callTool('security_status', {
  includeHistory: true
});
console.log('Available rollbacks:', status.rollbackHistory);
```

2. **Manual Field Restoration:**
```javascript
// Get current field value
const current = await mcp.callTool('get_field_value', {
  fieldId: 'field_id'
});

// Clear the field
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: '',
  options: { clearFirst: true }
});

// Type correct value
await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'correct_value'
});
```

3. **Use Dry-Run to Test Before Rollback:**
```javascript
await mcp.callTool('security_dry_run_control', {
  operation: 'enable',
  enabled: true
});

const rollbackResult = await mcp.callTool('security_rollback', {
  rollbackLast: true
});

console.log('Rollback would succeed:', rollbackResult.success);
```

## Getting Additional Help

### Creating a Bug Report

When reporting issues, include:

1. **System Information:**
```bash
# Operating System
uname -a  # Linux/macOS
systeminfo  # Windows

# Node.js version
node --version

# Python version
python --version

# MCP Smart Typer version
mcp-server-smart-typer --version
```

2. **Configuration:**
```bash
# Environment variables
env | grep -E "(ALLOW_TYPING|LOG_LEVEL|GRPC_PORT)"

# Claude Desktop config (remove sensitive data)
cat ~/.config/claude/claude_desktop_config.json
```

3. **Error Logs:**
```bash
# Recent audit logs
ls -la ~/Documents/mcp-typer-logs/
tail -50 ~/Documents/mcp-typer-logs/$(ls -t ~/Documents/mcp-typer-logs/ | head -1)

# System logs (if available)
```

4. **Reproduction Steps:**
- Exact sequence of actions
- Expected vs actual behavior
- Screenshots if helpful

### Support Channels

- **GitHub Issues**: [Create new issue](https://github.com/mcp-smart-typer/mcp-smart-typer/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/mcp-smart-typer/mcp-smart-typer/discussions)
- **Documentation**: Check README.md for updates

### Self-Help Resources

1. **Enable Maximum Debugging:**
```bash
export LOG_LEVEL=debug
export SECURE_LOGGING=true
export DRY_RUN_MODE=true
mcp-server-smart-typer --verbose
```

2. **Run Built-in Diagnostics:**
```bash
# Test installation
npm run test:e2e

# Test individual components
node test-mcp-server.js
```

3. **Use Dry-Run Mode:**
```javascript
// Test operations safely
await mcp.callTool('security_dry_run_control', {
  operation: 'enable',
  enabled: true
});

// All subsequent operations will be simulated
const result = await mcp.callTool('type_text', {
  fieldId: 'field_id',
  text: 'test_text'
});

console.log('Would succeed:', result.dryRunResult?.wouldSucceed);
console.log('Warnings:', result.dryRunResult?.warnings);
```

This comprehensive FAQ should help resolve most common issues with MCP Smart Typer. If you encounter an issue not covered here, please check the GitHub repository for updates or create a new issue with detailed information.
