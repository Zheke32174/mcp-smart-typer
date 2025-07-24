#!/usr/bin/env node

/**
 * MCP Smart Typer Server
 * AI-powered typing automation with Windows UI integration using comprehensive Zod schemas
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { MockNativeClient } from './utils/mock-native-client.js';
import { logger } from './utils/logger.js';
import { 
  detectFieldsRequest, 
  detectFieldsResponse,
  typeTextRequest, 
  typeTextResponse,
  getFieldValueRequest, 
  getFieldValueResponse,
  focusFieldRequest, 
  focusFieldResponse,
  DetectFieldsResponse,
  TypeTextResponse,
  GetFieldValueResponse,
  FocusFieldResponse
} from './schemas/index.js';
import { generateAsyncJobId } from './utils/job-manager.js';
import { initializeAuditLogger, getAuditLogger } from './security/audit-logger.js';
import { registerTypeTextTool } from './tools/type-text.js';
import { registerSecurityControlTools } from './tools/security-control.js';

const SERVER_NAME = 'mcp-smart-typer';
const SERVER_VERSION = '1.0.0';

async function main(): Promise<void> {
  try {
    logger.info(`Starting ${SERVER_NAME} v${SERVER_VERSION}...`);

    // Initialize security features
    logger.info('Initializing security features...');
    const auditLogger = initializeAuditLogger();
    logger.info('Audit logger initialized', {
      sessionId: auditLogger.getSessionId(),
      logPath: auditLogger.getLogFilePath()
    });

    // Initialize native client (using mock for development)
    const nativeClient = new MockNativeClient();
    await nativeClient.connect();

    // Create MCP server
    const server = new Server({
      name: SERVER_NAME,
      version: SERVER_VERSION,
    }, {
      capabilities: {
        tools: {},
      },
    });

    // Register MCP tools with comprehensive schema validation
    logger.info('Registering MCP tools...');
    registerTypeTextTool(server, nativeClient);
    registerSecurityControlTools(server);
    
    // TODO: Update other tools with security features
    // registerDetectFieldsTool(server, nativeClient);
    // registerGetFieldValueTool(server, nativeClient);
    // registerFocusFieldTool(server, nativeClient);

    // Register server info endpoint
    server.setRequestHandler('list_tools', async () => {
      return {
        tools: [
          {
            name: 'detect_fields',
            description: 'Detect input fields in the active window with rich metadata and context awareness',
            inputSchema: {
              type: 'object',
              properties: {
                contextHint: {
                  type: 'string',
                  description: 'Context hint for field detection (e.g., "login-form", "search-box")',
                },
                securityFlags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Security flags for operation validation',
                },
                windowTitle: {
                  type: 'string', 
                  description: 'Specific window title to focus on',
                },
                includeHidden: {
                  type: 'boolean',
                  description: 'Whether to include hidden fields',
                  default: false,
                },
                confidence: {
                  type: 'number',
                  description: 'Minimum confidence threshold for detection',
                  minimum: 0,
                  maximum: 1,
                  default: 0.8,
                },
              },
              required: ['contextHint'],
            },
          },
          {
            name: 'type_text',
            description: 'Type text into a specified field with advanced options and security features',
            inputSchema: {
              type: 'object',
              properties: {
                fieldId: {
                  type: 'string',
                  description: 'Target field identifier',
                },
                text: {
                  type: 'string',
                  description: 'Text to type',
                },
                options: {
                  type: 'object',
                  properties: {
                    delay: {
                      type: 'number',
                      description: 'Delay between keystrokes in milliseconds',
                      minimum: 0,
                      maximum: 5000,
                      default: 50,
                    },
                    clearFirst: {
                      type: 'boolean',
                      description: 'Clear field before typing',
                      default: false,
                    },
                    pressEnter: {
                      type: 'boolean',
                      description: 'Press Enter after typing', 
                      default: false,
                    },
                    simulate: {
                      type: 'boolean',
                      description: 'Simulate typing without actual input (for testing)',
                      default: false,
                    },
                  },
                },
                securityFlags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Security flags for operation validation',
                },
              },
              required: ['fieldId', 'text'],
            },
          },
          {
            name: 'get_field_value',
            description: 'Retrieve the current value from a specified field with security considerations',
            inputSchema: {
              type: 'object',
              properties: {
                fieldId: {
                  type: 'string',
                  description: 'Field identifier to read from',
                },
                securityFlags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Security flags for operation validation',
                },
                maxLength: {
                  type: 'number',
                  description: 'Maximum length of value to retrieve',
                  default: 10000,
                },
              },
              required: ['fieldId'],
            },
          },
          {
            name: 'focus_field',
            description: 'Focus a specified field and optionally bring its window to front',
            inputSchema: {
              type: 'object',
              properties: {
                fieldId: {
                  type: 'string',
                  description: 'Field identifier to focus',
                },
                securityFlags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Security flags for operation validation',
                },
                bringToFront: {
                  type: 'boolean',
                  description: 'Whether to bring window to front',
                  default: true,
                },
                scrollIntoView: {
                  type: 'boolean',
                  description: 'Whether to scroll field into view',
                  default: true,
                },
              },
              required: ['fieldId'],
            },
          },
          {
            name: 'security_grant_permission',
            description: 'Grant or revoke MCP root permissions for typing operations',
            inputSchema: {
              type: 'object',
              properties: {
                sessionId: {
                  type: 'string',
                  description: 'Session ID to grant/revoke permissions for'
                },
                operation: {
                  type: 'string',
                  enum: ['mcp_root', 'revoke_mcp_root'],
                  description: 'Permission operation to perform'
                },
                reason: {
                  type: 'string',
                  description: 'Reason for the permission change'
                }
              },
              required: ['sessionId', 'operation']
            }
          },
          {
            name: 'security_rollback',
            description: 'Rollback typing operations (Ctrl+Z functionality)',
            inputSchema: {
              type: 'object',
              properties: {
                operationId: {
                  type: 'string',
                  description: 'Specific operation ID to rollback'
                },
                rollbackLast: {
                  type: 'boolean',
                  default: false,
                  description: 'Rollback the last operation'
                }
              }
            }
          },
          {
            name: 'security_status',
            description: 'Get security status, permissions, and audit information',
            inputSchema: {
              type: 'object',
              properties: {
                includeHistory: {
                  type: 'boolean',
                  default: false,
                  description: 'Include rollback history in response'
                },
                includeStats: {
                  type: 'boolean',
                  default: true,
                  description: 'Include statistics in response'
                }
              }
            }
          },
          {
            name: 'security_dry_run_control',
            description: 'Control dry-run mode for safe operation testing',
            inputSchema: {
              type: 'object',
              properties: {
                enabled: {
                  type: 'boolean',
                  description: 'Enable or disable dry-run mode'
                },
                operation: {
                  type: 'string',
                  enum: ['enable', 'disable', 'status'],
                  description: 'Dry-run control operation'
                }
              },
              required: ['enabled', 'operation']
            }
          }
        ],
      };
    });

    // Create transport and connect
    const transport = new StdioServerTransport();

    // Handle graceful shutdown
    const cleanup = async (): Promise<void> => {
      try {
        logger.info('Shutting down server...');
        
        // Close audit logger session
        const auditLogger = getAuditLogger();
        const auditStats = auditLogger.getSessionStats();
        logger.info('Final audit statistics:', auditStats);
        auditLogger.closeSession();
        
        await nativeClient.disconnect();
        transport.close();
        logger.info('Server shutdown complete');
      } catch (error) {
        logger.error('Error during cleanup:', error);
      }
    };

    process.on('SIGINT', async () => {
      logger.info('Received SIGINT, shutting down gracefully');
      await cleanup();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      logger.info('Received SIGTERM, shutting down gracefully');
      await cleanup();
      process.exit(0);
    });

    // Connect and start server
    await server.connect(transport);
    logger.info(`${SERVER_NAME} v${SERVER_VERSION} running on stdio transport`);
    logger.info('MCP Smart Typer ready for connections!');
    
    // Log initial audit statistics
    const auditStats = auditLogger.getSessionStats();
    logger.info('Initial audit statistics:', auditStats);
    
  } catch (error) {
    logger.error('Failed to start MCP server:', error);
    process.exit(1);
  }
}

// Run the server
main().catch((error) => {
  logger.error('Unhandled error:', error);
  process.exit(1);
});
