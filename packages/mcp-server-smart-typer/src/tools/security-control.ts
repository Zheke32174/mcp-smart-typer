/**
 * Security Control Tool
 * Provides MCP tools for managing security features, permissions, and rollback operations
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { logger } from '../utils/logger.js';
import { 
  permissionManager, 
  securityManager, 
  getAuditLogger, 
  rollbackManager 
} from '../security/index.js';

// Zod schemas for security control tools
const grantPermissionSchema = z.object({
  sessionId: z.string().min(1, 'Session ID is required'),
  operation: z.enum(['mcp_root', 'revoke_mcp_root']),
  reason: z.string().optional()
});

const rollbackOperationSchema = z.object({
  operationId: z.string().optional(),
  rollbackLast: z.boolean().default(false)
});

const securityStatusSchema = z.object({
  includeHistory: z.boolean().default(false),
  includeStats: z.boolean().default(true)
});

const dryRunControlSchema = z.object({
  enabled: z.boolean(),
  operation: z.enum(['enable', 'disable', 'status'])
});

export function registerSecurityControlTools(server: McpServer) {
  
  // Tool: Grant or revoke MCP root permissions
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'security_grant_permission') {
      return;
    }

    try {
      const params = grantPermissionSchema.parse(request.params.arguments);
      
      if (params.operation === 'mcp_root') {
        permissionManager.grantMcpRootPermission(params.sessionId);
        
        getAuditLogger().logPermissionCheck('grant_mcp_root', true, params.reason);
        
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              operation: 'mcp_root_granted',
              sessionId: params.sessionId,
              reason: params.reason,
              timestamp: new Date().toISOString()
            }, null, 2)
          }]
        };
        
      } else if (params.operation === 'revoke_mcp_root') {
        permissionManager.revokeMcpRootPermission(params.sessionId);
        
        getAuditLogger().logPermissionCheck('revoke_mcp_root', true, params.reason);
        
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              operation: 'mcp_root_revoked',
              sessionId: params.sessionId,
              reason: params.reason,
              timestamp: new Date().toISOString()
            }, null, 2)
          }]
        };
      }

    } catch (error) {
      logger.error('Failed to manage permissions:', error);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            operation: 'permission_management'
          }, null, 2)
        }],
        isError: true
      };
    }
  });

  // Tool: Rollback operations
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'security_rollback') {
      return;
    }

    try {
      const params = rollbackOperationSchema.parse(request.params.arguments);
      
      let rollbackResult;
      if (params.rollbackLast) {
        rollbackResult = await rollbackManager.rollbackLastOperation();
      } else if (params.operationId) {
        rollbackResult = await rollbackManager.rollbackOperation(params.operationId);
      } else {
        throw new Error('Either rollbackLast must be true or operationId must be provided');
      }

      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: rollbackResult.success,
            error: rollbackResult.error,
            rollbackState: rollbackResult.rollbackState,
            timestamp: new Date().toISOString()
          }, null, 2)
        }],
        isError: !rollbackResult.success
      };

    } catch (error) {
      logger.error('Failed to rollback operation:', error);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            operation: 'rollback'
          }, null, 2)
        }],
        isError: true
      };
    }
  });

  // Tool: Get security status and audit information
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'security_status') {
      return;
    }

    try {
      const params = securityStatusSchema.parse(request.params.arguments);
      
      const permissionStatus = permissionManager.getPermissionStatus();
      const rollbackStats = rollbackManager.getRollbackStats();
      const auditStats = getAuditLogger().getSessionStats();
      const loggerConfig = logger.getConfig();
      
      const status = {
        timestamp: new Date().toISOString(),
        permissions: permissionStatus,
        rollback: rollbackStats,
        audit: auditStats,
        logging: loggerConfig,
        environment: {
          allowTyping: process.env.ALLOW_TYPING === 'true',
          dryRunMode: process.env.DRY_RUN_MODE === 'true',
          secureLogging: process.env.SECURE_LOGGING === 'true'
        }
      };

      if (params.includeHistory) {
        const rollbackHistory = rollbackManager.getRollbackHistory();
        (status as any).rollbackHistory = rollbackHistory.slice(0, 10); // Last 10 operations
      }

      return {
        content: [{
          type: 'text',
          text: JSON.stringify(status, null, 2)
        }]
      };

    } catch (error) {
      logger.error('Failed to get security status:', error);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            operation: 'security_status'
          }, null, 2)
        }],
        isError: true
      };
    }
  });

  // Tool: Control dry-run mode
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'security_dry_run_control') {
      return;
    }

    try {
      const params = dryRunControlSchema.parse(request.params.arguments);
      
      if (params.operation === 'enable') {
        rollbackManager.setDryRunMode(true);
      } else if (params.operation === 'disable') {
        rollbackManager.setDryRunMode(false);
      }

      const currentStatus = rollbackManager.isDryRunMode();
      
      getAuditLogger().logOperation('DRY_RUN_CONTROL', 'security', {
        success: true,
        metadata: {
          operation: params.operation,
          previousState: !currentStatus,
          newState: currentStatus
        }
      });

      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            operation: params.operation,
            dryRunMode: currentStatus,
            timestamp: new Date().toISOString()
          }, null, 2)
        }]
      };

    } catch (error) {
      logger.error('Failed to control dry-run mode:', error);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            operation: 'dry_run_control'
          }, null, 2)
        }],
        isError: true
      };
    }
  });
}
