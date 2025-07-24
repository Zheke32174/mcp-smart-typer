# MCP Smart Typer - Security, Permission & Sandbox Controls

This document describes the comprehensive security features implemented in the MCP Smart Typer server to ensure safe and controlled typing operations.

## Overview

The security system consists of four main components:

1. **Permission Manager** - Controls when typing is allowed
2. **Security Manager** - Detects and masks sensitive data
3. **Audit Logger** - Maintains comprehensive operation logs
4. **Rollback Manager** - Provides dry-run mode and rollback functionality

## Environment Variables

Configure security behavior using these environment variables:

```bash
# Core permission control
ALLOW_TYPING=true          # Allow typing operations globally

# Security features  
SECURE_LOGGING=true        # Enable sensitive data masking in logs
DRY_RUN_MODE=true         # Enable dry-run mode by default

# Logging configuration
LOG_LEVEL=info            # Set logging level (debug, info, warn, error)
```

## Permission System

### Permission Requirements

Typing operations require **one** of the following:

1. `ALLOW_TYPING=true` environment variable
2. Explicit MCP root permission granted for the session
3. `mcp_root_permission` security flag in the request

### Granting Permissions

Use the `security_grant_permission` tool:

```json
{
  "name": "security_grant_permission",
  "arguments": {
    "sessionId": "session-123",
    "operation": "mcp_root",
    "reason": "Administrative typing operations"
  }
}
```

### Revoking Permissions

```json
{
  "name": "security_grant_permission", 
  "arguments": {
    "sessionId": "session-123",
    "operation": "revoke_mcp_root",
    "reason": "Session ended"
  }
}
```

## Sensitive Data Protection

### Automatic Detection

The system automatically detects sensitive fields based on:

- Field names containing: `password`, `passwd`, `pwd`, `pass`, `secret`, `key`, `token`
- Field types: `password`, `email`, `phone`, `ssn`, `credit_card`, `api_key`
- Content patterns: emails, phone numbers, credit cards, SSNs

### Data Masking

Sensitive values are automatically masked in logs:

- Short values (≤2 chars): `**`
- Medium values (≤8 chars): `p****d`
- Long values: `pa****rd`

### Security Flags

Use security flags to indicate data sensitivity:

```json
{
  "securityFlags": ["sensitive", "encrypted", "audit"]
}
```

Valid flags:
- `sensitive` - Contains sensitive information
- `encrypted` - Data should be encrypted
- `audit` - Requires audit logging  
- `restricted` - Restricted access required
- `public` - Public information (default)
- `mcp_root_permission` - Grants temporary permission

## Audit Logging

### Log Location

Audit logs are saved to:
```
%USERPROFILE%\Documents\mcp-typer-logs\yyyy-mm-dd_HHMMSS.log
```

### Log Format

Each log file contains:
- Session metadata header
- JSON Lines format (one JSON object per line)
- Masked sensitive data
- Operation timestamps and results

### Sample Log Entry

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "sessionId": "mcp-typer-1705312245123-abc123def",
  "operation": "TYPE_TEXT",
  "toolName": "type_text", 
  "fieldId": "login-password",
  "success": true,
  "metadata": {
    "charactersTyped": 12,
    "timeTaken": 450,
    "clearFirst": false,
    "hasSensitiveData": true
  },
  "hasSensitiveData": true
}
```

### Audit Operations

The system logs these operations:
- `TYPE_TEXT` - Text typing operations
- `DETECT_FIELDS` - Field detection
- `FOCUS_FIELD` - Field focusing  
- `GET_FIELD_VALUE` - Value retrieval
- `PERMISSION_CHECK` - Permission validations
- `SECURITY_VALIDATION` - Security flag validation
- `ROLLBACK` - Rollback operations
- `DRY_RUN` - Dry-run simulations
- `SESSION_START` / `SESSION_END` - Session lifecycle

## Dry-Run Mode & Rollback

### Dry-Run Mode

Enable safe operation testing:

```json
{
  "name": "security_dry_run_control",
  "arguments": {
    "operation": "enable", 
    "enabled": true
  }
}
```

Dry-run mode:
- Simulates operations without actual execution
- Predicts changes and potential issues
- Returns warnings and estimated timing
- Safe for testing sensitive operations

### Rollback Operations

Rollback the last operation:

```json
{
  "name": "security_rollback",
  "arguments": {
    "rollbackLast": true
  }
}
```

Rollback specific operation:

```json
{
  "name": "security_rollback", 
  "arguments": {
    "operationId": "rollback-1705312245123-xyz789"
  }
}
```

### Rollback Limitations

- Password fields: Original values are not captured for security
- Rollback attempts field restoration or clearing
- History limited to last 50 operations
- Operations older than session lifetime cannot be rolled back

## Security Status Monitoring

Get comprehensive security status:

```json
{
  "name": "security_status",
  "arguments": {
    "includeHistory": true,
    "includeStats": true
  }
}
```

Returns:
- Permission status
- Rollback statistics  
- Audit session info
- Environment configuration
- Recent operation history (if requested)

## MCP Tools Reference

### Core Typing Tool

#### `type_text`

Enhanced typing with full security integration:

```json
{
  "name": "type_text",
  "arguments": {
    "fieldId": "username-field",
    "text": "user@example.com", 
    "options": {
      "delay": 50,
      "clearFirst": true,
      "pressEnter": false,
      "simulate": false
    },
    "securityFlags": ["audit", "sensitive"]
  }
}
```

### Security Management Tools

#### `security_grant_permission`
Grant or revoke MCP root permissions

#### `security_rollback` 
Rollback typing operations (Ctrl+Z functionality)

#### `security_status`
Get security status, permissions, and audit information

#### `security_dry_run_control`
Control dry-run mode for safe operation testing

## Best Practices

### For Users

1. **Set Environment Variables**: Configure `ALLOW_TYPING=true` or use permission grants
2. **Use Security Flags**: Mark sensitive operations appropriately  
3. **Monitor Audit Logs**: Review logs for security incidents
4. **Test with Dry-Run**: Use dry-run mode for sensitive operations
5. **Understand Rollback**: Know limitations of rollback for password fields

### For Developers

1. **Validate Permissions**: Always check permissions before typing operations
2. **Handle Sensitive Data**: Use security manager for data detection and masking
3. **Log Operations**: Use audit logger for all significant operations  
4. **Support Rollback**: Implement rollback-compatible operations
5. **Secure by Default**: Default to secure configurations

## Troubleshooting

### Permission Denied Errors

```
Typing not allowed. Set ALLOW_TYPING=true environment variable or grant explicit MCP root permission.
```

**Solutions:**
1. Set `ALLOW_TYPING=true` environment variable
2. Grant MCP root permission for the session
3. Include `mcp_root_permission` security flag

### Audit Log Issues

**Log directory creation fails:**
- Ensure `%USERPROFILE%\Documents` is accessible
- Check file system permissions
- Review disk space availability

**Log entries missing:**
- Verify audit logger initialization
- Check for filesystem errors in main logs
- Ensure proper session management

### Rollback Failures

**"No operations to rollback":**
- No operations have been performed
- Rollback history was cleared
- Operation ID doesn't exist

**Rollback execution fails:**
- Field no longer exists or accessible
- UI automation client disconnected  
- Insufficient permissions for field access

## Security Considerations

### Data Protection

- Sensitive data is masked in all logs
- Password field values are never captured for rollback
- Audit logs are stored locally only
- No sensitive data transmitted over network

### Access Control

- Multiple permission layers (environment, session, request-level)
- Session-based permission management
- Explicit permission grants logged and auditable

### Audit Trail

- Comprehensive operation logging
- Tamper-evident log format
- Timestamped entries with session correlation
- Sensitive data protection in logs

### Safe Operation

- Dry-run mode for testing
- Rollback capability for error recovery
- Permission validation before execution
- Security flag validation and warnings

## Integration Examples

### Basic Secure Typing

```typescript
// 1. Grant permission
await mcpClient.callTool('security_grant_permission', {
  sessionId: 'my-session',
  operation: 'mcp_root',
  reason: 'User authentication'
});

// 2. Type with security
await mcpClient.callTool('type_text', {
  fieldId: 'password-field',
  text: 'secretPassword123',
  securityFlags: ['sensitive', 'audit']
});

// 3. Check status
const status = await mcpClient.callTool('security_status', {
  includeStats: true
});
```

### Safe Testing Workflow

```typescript
// 1. Enable dry-run
await mcpClient.callTool('security_dry_run_control', {
  operation: 'enable',
  enabled: true
});

// 2. Test operation
const dryRun = await mcpClient.callTool('type_text', {
  fieldId: 'critical-field',
  text: 'test-data',
  options: { simulate: true }
});

// 3. Review predictions
console.log('Would succeed:', dryRun.dryRunResult.wouldSucceed);
console.log('Warnings:', dryRun.dryRunResult.warnings);

// 4. Execute if safe
if (dryRun.dryRunResult.wouldSucceed && dryRun.dryRunResult.warnings.length === 0) {
  await mcpClient.callTool('security_dry_run_control', {
    operation: 'disable', 
    enabled: false
  });
  
  await mcpClient.callTool('type_text', {
    fieldId: 'critical-field',
    text: 'real-data'
  });
}
```

This security system provides comprehensive protection while maintaining usability for legitimate typing automation needs.
