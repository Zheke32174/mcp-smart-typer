/**
 * Audit Logger
 * Maintains per-session audit logs saved to %USERPROFILE%\Documents\mcp-typer-logs\
 */

import { writeFileSync, appendFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { logger } from '../utils/logger.js';
import { securityManager } from './security-manager.js';

export interface AuditLogEntry {
  timestamp: string;
  sessionId: string;
  operation: string;
  toolName: string;
  fieldId?: string;
  success: boolean;
  errorCode?: string;
  metadata?: Record<string, any>;
  hasSensitiveData?: boolean;
}

export class AuditLogger {
  private sessionId: string;
  private logDirectory: string;
  private logFilePath: string;
  private entries: AuditLogEntry[];

  constructor(sessionId?: string) {
    this.sessionId = sessionId || this.generateSessionId();
    this.entries = [];
    
    // Create log directory path: %USERPROFILE%\Documents\mcp-typer-logs\
    this.logDirectory = join(homedir(), 'Documents', 'mcp-typer-logs');
    this.ensureLogDirectory();
    
    // Create log file with format: yyyy-mm-dd_HHMMSS.log
    const timestamp = new Date().toISOString().replace(/:/g, '').replace(/\..+/, '').replace('T', '_');
    this.logFilePath = join(this.logDirectory, `${timestamp}.log`);
    
    this.initializeLogFile();
    
    logger.info('Audit Logger initialized', {
      sessionId: this.sessionId,
      logFilePath: this.logFilePath
    });
  }

  private generateSessionId(): string {
    return `mcp-typer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private ensureLogDirectory(): void {
    try {
      if (!existsSync(this.logDirectory)) {
        mkdirSync(this.logDirectory, { recursive: true });
        logger.info('Created audit log directory', { directory: this.logDirectory });
      }
    } catch (error) {
      logger.error('Failed to create audit log directory', {
        directory: this.logDirectory,
        error: error instanceof Error ? error.message : String(error)
      });
      throw new Error(`Failed to create audit log directory: ${error}`);
    }
  }

  private initializeLogFile(): void {
    try {
      const header = [
        '# MCP Smart Typer Audit Log',
        `# Session ID: ${this.sessionId}`,
        `# Created: ${new Date().toISOString()}`,
        `# Log Format: JSON Lines (one JSON object per line)`,
        '',
      ].join('\n');
      
      writeFileSync(this.logFilePath, header, 'utf8');
      
      // Log session start
      this.logOperation('SESSION_START', 'audit', {
        success: true,
        metadata: {
          sessionId: this.sessionId,
          logFilePath: this.logFilePath,
          timestamp: new Date().toISOString()
        }
      });
      
    } catch (error) {
      logger.error('Failed to initialize audit log file', {
        logFilePath: this.logFilePath,
        error: error instanceof Error ? error.message : String(error)
      });
      throw new Error(`Failed to initialize audit log file: ${error}`);
    }
  }

  /**
   * Log an operation to the audit log
   */
  logOperation(operation: string, toolName: string, details: {
    fieldId?: string;
    success: boolean;
    errorCode?: string;
    metadata?: Record<string, any>;
  }): void {
    const timestamp = new Date().toISOString();
    
    // Create secure log entry with masked sensitive data
    const secureLogEntry = securityManager.createSecureLogEntry('info', 'Audit log entry', details.metadata);
    
    const entry: AuditLogEntry = {
      timestamp,
      sessionId: this.sessionId,
      operation,
      toolName,
      fieldId: details.fieldId,
      success: details.success,
      errorCode: details.errorCode,
      metadata: secureLogEntry.data,
      hasSensitiveData: secureLogEntry.hasSensitiveData
    };

    // Add to in-memory entries
    this.entries.push(entry);

    // Write to file
    this.writeToFile(entry);

    logger.debug('Audit log entry created', {
      operation,
      toolName,
      success: details.success,
      hasSensitiveData: entry.hasSensitiveData
    });
  }

  private writeToFile(entry: AuditLogEntry): void {
    try {
      const logLine = JSON.stringify(entry) + '\n';
      appendFileSync(this.logFilePath, logLine, 'utf8');
    } catch (error) {
      logger.error('Failed to write audit log entry', {
        logFilePath: this.logFilePath,
        operation: entry.operation,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }

  /**
   * Log typing operation
   */
  logTypingOperation(fieldId: string, success: boolean, metadata?: Record<string, any>, errorCode?: string): void {
    this.logOperation('TYPE_TEXT', 'type_text', {
      fieldId,
      success,
      errorCode,
      metadata: {
        ...metadata,
        charactersTyped: metadata?.charactersTyped || 0,
        timeTaken: metadata?.timeTaken || 0,
        clearFirst: metadata?.clearFirst || false,
        pressEnter: metadata?.pressEnter || false
      }
    });
  }

  /**
   * Log field detection operation
   */
  logFieldDetection(success: boolean, metadata?: Record<string, any>, errorCode?: string): void {
    this.logOperation('DETECT_FIELDS', 'detect_fields', {
      success,
      errorCode,
      metadata: {
        ...metadata,
        fieldsDetected: metadata?.fieldsDetected || 0,
        contextHint: metadata?.contextHint,
        includeHidden: metadata?.includeHidden || false
      }
    });
  }

  /**
   * Log field focus operation
   */
  logFieldFocus(fieldId: string, success: boolean, metadata?: Record<string, any>, errorCode?: string): void {
    this.logOperation('FOCUS_FIELD', 'focus_field', {
      fieldId,
      success,
      errorCode,
      metadata: {
        ...metadata,
        bringToFront: metadata?.bringToFront || false,
        scrollIntoView: metadata?.scrollIntoView || false
      }
    });
  }

  /**
   * Log field value retrieval operation
   */
  logFieldValueRetrieval(fieldId: string, success: boolean, metadata?: Record<string, any>, errorCode?: string): void {
    this.logOperation('GET_FIELD_VALUE', 'get_field_value', {
      fieldId,
      success,
      errorCode,
      metadata: {
        ...metadata,
        valueLength: metadata?.valueLength || 0,
        maxLength: metadata?.maxLength || 10000
      }
    });
  }

  /**
   * Log permission check
   */
  logPermissionCheck(operation: string, allowed: boolean, reason?: string): void {
    this.logOperation('PERMISSION_CHECK', 'security', {
      success: allowed,
      errorCode: allowed ? undefined : 'PERMISSION_DENIED',
      metadata: {
        operation,
        reason,
        allowTypingEnv: process.env.ALLOW_TYPING === 'true',
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Log security validation
   */
  logSecurityValidation(operation: string, valid: boolean, warnings?: string[]): void {
    this.logOperation('SECURITY_VALIDATION', 'security', {
      success: valid,
      errorCode: valid ? undefined : 'SECURITY_VALIDATION_FAILED',
      metadata: {
        operation,
        warnings,
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Log rollback operation
   */
  logRollback(operation: string, success: boolean, metadata?: Record<string, any>): void {
    this.logOperation('ROLLBACK', 'rollback', {
      success,
      errorCode: success ? undefined : 'ROLLBACK_FAILED',
      metadata: {
        ...metadata,
        originalOperation: operation,
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Close the audit log session
   */
  closeSession(): void {
    this.logOperation('SESSION_END', 'audit', {
      success: true,
      metadata: {
        sessionId: this.sessionId,
        totalEntries: this.entries.length,
        duration: Date.now() - parseInt(this.sessionId.split('-')[2]),
        timestamp: new Date().toISOString()
      }
    });

    logger.info('Audit log session closed', {
      sessionId: this.sessionId,
      totalEntries: this.entries.length,
      logFilePath: this.logFilePath
    });
  }

  /**
   * Get session statistics
   */
  getSessionStats(): {
    sessionId: string;
    totalEntries: number;
    operationCounts: Record<string, number>;
    successRate: number;
    logFilePath: string;
  } {
    const operationCounts: Record<string, number> = {};
    let successCount = 0;

    for (const entry of this.entries) {
      operationCounts[entry.operation] = (operationCounts[entry.operation] || 0) + 1;
      if (entry.success) {
        successCount++;
      }
    }

    return {
      sessionId: this.sessionId,
      totalEntries: this.entries.length,
      operationCounts,
      successRate: this.entries.length > 0 ? successCount / this.entries.length : 0,
      logFilePath: this.logFilePath
    };
  }

  /**
   * Get the current session ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Get the log file path
   */
  getLogFilePath(): string {
    return this.logFilePath;
  }
}

// Global audit logger instance - will be initialized when server starts
let globalAuditLogger: AuditLogger | null = null;

export function initializeAuditLogger(sessionId?: string): AuditLogger {
  globalAuditLogger = new AuditLogger(sessionId);
  return globalAuditLogger;
}

export function getAuditLogger(): AuditLogger {
  if (!globalAuditLogger) {
    throw new Error('Audit logger not initialized. Call initializeAuditLogger() first.');
  }
  return globalAuditLogger;
}
