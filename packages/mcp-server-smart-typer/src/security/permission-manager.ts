/**
 * Permission Manager
 * Handles permission validation for typing operations
 */

import { logger } from '../utils/logger.js';

export interface PermissionContext {
  sessionId: string;
  toolName: string;
  fieldId?: string;
  securityFlags?: string[];
  mcpRootPermission?: boolean;
}

export class PermissionManager {
  private allowTyping: boolean;
  private mcpRootPermissions: Set<string>;

  constructor() {
    this.allowTyping = process.env.ALLOW_TYPING === 'true';
    this.mcpRootPermissions = new Set();

    // Log initial permission state
    logger.info('Permission Manager initialized', {
      allowTyping: this.allowTyping,
      hasAllowTypingEnv: process.env.ALLOW_TYPING !== undefined,
    });
  }

  /**
   * Grant MCP root permission for a session
   */
  grantMcpRootPermission(sessionId: string): void {
    this.mcpRootPermissions.add(sessionId);
    logger.info('Granted MCP root permission', { sessionId });
  }

  /**
   * Revoke MCP root permission for a session
   */
  revokeMcpRootPermission(sessionId: string): void {
    this.mcpRootPermissions.delete(sessionId);
    logger.info('Revoked MCP root permission', { sessionId });
  }

  /**
   * Check if typing is allowed for the given context
   */
  isTypingAllowed(context: PermissionContext): boolean {
    // Check environment variable first
    if (this.allowTyping) {
      logger.debug('Typing allowed via ALLOW_TYPING environment variable', {
        sessionId: context.sessionId,
        toolName: context.toolName,
      });
      return true;
    }

    // Check for explicit MCP root permission
    if (this.mcpRootPermissions.has(context.sessionId)) {
      logger.debug('Typing allowed via MCP root permission', {
        sessionId: context.sessionId,
        toolName: context.toolName,
      });
      return true;
    }

    // Check for explicit permission in context
    if (context.mcpRootPermission === true) {
      logger.debug('Typing allowed via explicit permission in context', {
        sessionId: context.sessionId,
        toolName: context.toolName,
      });
      return true;
    }

    logger.warn('Typing permission denied', {
      sessionId: context.sessionId,
      toolName: context.toolName,
      fieldId: context.fieldId,
      allowTypingEnv: this.allowTyping,
      hasMcpRootPermission: this.mcpRootPermissions.has(context.sessionId),
    });

    return false;
  }

  /**
   * Validate permissions and throw error if not allowed
   */
  validateTypingPermission(context: PermissionContext): void {
    if (!this.isTypingAllowed(context)) {
      throw new Error(
        `Typing not allowed. Set ALLOW_TYPING=true environment variable or grant explicit MCP root permission. ` +
          `Session: ${context.sessionId}, Tool: ${context.toolName}`
      );
    }
  }

  /**
   * Get current permission status
   */
  getPermissionStatus(): {
    allowTypingEnv: boolean;
    activeMcpRootSessions: number;
  } {
    return {
      allowTypingEnv: this.allowTyping,
      activeMcpRootSessions: this.mcpRootPermissions.size,
    };
  }
}

export const permissionManager = new PermissionManager();
