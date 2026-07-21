#!/usr/bin/env node

/**
 * MCP Smart Typer Server - Simple Working Implementation
 * AI-powered typing automation with Windows UI integration
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { MockNativeClient } from './utils/mock-native-client.js';
import { logger } from './utils/logger.js';
import { generateAsyncJobId } from './utils/job-manager.js';
import {
  detectFieldsRequest,
  typeTextRequest,
  getFieldValueRequest,
  focusFieldRequest,
  DetectFieldsResponse,
  TypeTextResponse,
  GetFieldValueResponse,
  FocusFieldResponse,
} from './schemas/index.js';

const SERVER_NAME = 'mcp-smart-typer';
const SERVER_VERSION = '2.0.0';

async function main(): Promise<void> {
  try {
    logger.info(`Starting ${SERVER_NAME} v${SERVER_VERSION}...`);

    // Initialize native client (using mock for development)
    const nativeClient = new MockNativeClient();
    await nativeClient.connect();

    // Create MCP server
    const server = new Server(
      {
        name: SERVER_NAME,
        version: SERVER_VERSION,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Register list_tools handler
    server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'detect_fields',
            description:
              'Detect input fields in the active window with rich metadata and context awareness',
            inputSchema: {
              type: 'object',
              properties: {
                contextHint: {
                  type: 'string',
                  description:
                    'Context hint for field detection (e.g., "login-form", "search-box")',
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
            description:
              'Type text into a specified field with advanced options and security features',
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
            description:
              'Retrieve the current value from a specified field with security considerations',
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
        ],
      };
    });

    // Register call_tool handler
    server.setRequestHandler(CallToolRequestSchema, async request => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'detect_fields': {
            // Validate input with Zod
            const params = detectFieldsRequest.parse(args);
            logger.info('Detecting fields with params:', params);

            // Generate async job ID for tracking
            const asyncJobId = generateAsyncJobId();

            // Call native client to detect fields
            const result = await nativeClient.detectFields({
              contextHint: params.contextHint,
              windowTitle: params.windowTitle,
              includeHidden: params.includeHidden,
              confidence: params.confidence,
            });

            // Process and enrich field data
            const fields =
              result.fields?.map((field: any, index: number) => ({
                id: field.id || `field_${Date.now()}_${index}`,
                name: field.name || `unnamed_field_${index}`,
                type: field.type || 'input',
                metadata: {
                  description: field.description,
                  placeholder: field.placeholder,
                  maxLength: field.maxLength,
                  inputType: field.inputType || 'text',
                  required: field.required || false,
                  pattern: field.pattern,
                  bounds: field.bounds
                    ? {
                        x: Math.round(field.bounds.x),
                        y: Math.round(field.bounds.y),
                        width: Math.round(field.bounds.width),
                        height: Math.round(field.bounds.height),
                      }
                    : undefined,
                  confidence: field.confidence || 0.8,
                },
              })) || [];

            // Build response
            const response: DetectFieldsResponse = {
              fields,
              windowInfo: result.windowInfo
                ? {
                    title: result.windowInfo.title,
                    className: result.windowInfo.className,
                    handle: result.windowInfo.handle,
                    bounds: {
                      x: Math.round(result.windowInfo.bounds.x),
                      y: Math.round(result.windowInfo.bounds.y),
                      width: Math.round(result.windowInfo.bounds.width),
                      height: Math.round(result.windowInfo.bounds.height),
                    },
                  }
                : undefined,
              asyncJobId,
            };

            logger.info(`Detected ${fields.length} fields`, {
              asyncJobId,
              fieldTypes: fields.map((f: any) => f.type),
              windowTitle: result.windowInfo?.title,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(response, null, 2),
                },
              ],
            };
          }

          case 'type_text': {
            const startTime = Date.now();

            // Validate input with Zod
            const params = typeTextRequest.parse(args);
            logger.info('Typing text to field:', {
              fieldId: params.fieldId,
              textLength: params.text.length,
              options: params.options,
            });

            // Generate async job ID for tracking
            const asyncJobId = generateAsyncJobId();

            // Security check for sensitive data
            if (
              params.securityFlags?.includes('encrypted') &&
              (params.text.includes('password') || params.text.includes('secret'))
            ) {
              logger.warn('Potentially sensitive data detected in type_text call', {
                fieldId: params.fieldId,
              });
            }

            // Handle simulation mode
            if (params.options?.simulate) {
              logger.info('Simulating text typing (no actual input)', {
                fieldId: params.fieldId,
                asyncJobId,
              });

              const response: TypeTextResponse = {
                success: true,
                charactersTyped: params.text.length,
                timeTaken: Math.min(params.text.length * (params.options?.delay || 50), 1000),
                asyncJobId,
              };

              return {
                content: [
                  {
                    type: 'text',
                    text: JSON.stringify(response, null, 2),
                  },
                ],
              };
            }

            // Call native client to type text
            const result = await nativeClient.typeText({
              fieldId: params.fieldId,
              text: params.text,
              delay: params.options?.delay || 50,
              clearFirst: params.options?.clearFirst || false,
              pressEnter: params.options?.pressEnter || false,
            });

            const timeTaken = Date.now() - startTime;

            // Build response
            const response: TypeTextResponse = {
              success: result.success || false,
              charactersTyped: result.charactersTyped || params.text.length,
              timeTaken,
              asyncJobId,
              errorCode: result.success ? undefined : result.errorCode || 'TYPING_ERROR',
              errorMessage: result.success
                ? undefined
                : result.errorMessage || 'Failed to type text',
            };

            logger.info('Text typing completed:', {
              success: response.success,
              charactersTyped: response.charactersTyped,
              timeTaken: response.timeTaken,
              asyncJobId,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(response, null, 2),
                },
              ],
            };
          }

          case 'get_field_value': {
            // Validate input with Zod
            const params = getFieldValueRequest.parse(args);
            logger.info('Getting field value:', { fieldId: params.fieldId });

            // Generate async job ID for tracking
            const asyncJobId = generateAsyncJobId();

            // Call native client to get field value
            const result = await nativeClient.getFieldValue({
              fieldId: params.fieldId,
              maxLength: params.maxLength,
            });

            // Check if field contains sensitive data
            const isSecure =
              result.fieldInfo?.inputType === 'password' ||
              result.fieldInfo?.name?.toLowerCase().includes('password') ||
              params.securityFlags?.includes('sensitive');

            // Build response
            const response: GetFieldValueResponse = {
              value: isSecure ? '[REDACTED]' : result.value || '',
              fieldInfo: result.fieldInfo
                ? {
                    id: result.fieldInfo.id,
                    name: result.fieldInfo.name,
                    type: result.fieldInfo.type,
                    metadata: result.fieldInfo.metadata,
                  }
                : undefined,
              isSecure,
              asyncJobId,
              errorCode:
                result.success === false ? result.errorCode || 'RETRIEVAL_ERROR' : undefined,
              errorMessage:
                result.success === false
                  ? result.errorMessage || 'Failed to get field value'
                  : undefined,
            };

            logger.info('Field value retrieved:', {
              fieldId: params.fieldId,
              valueLength: result.value?.length || 0,
              isSecure,
              asyncJobId,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(response, null, 2),
                },
              ],
            };
          }

          case 'focus_field': {
            // Validate input with Zod
            const params = focusFieldRequest.parse(args);
            logger.info('Focusing field:', {
              fieldId: params.fieldId,
              bringToFront: params.bringToFront,
              scrollIntoView: params.scrollIntoView,
            });

            // Generate async job ID for tracking
            const asyncJobId = generateAsyncJobId();

            // Call native client to focus field
            const result = await nativeClient.focusField({
              fieldId: params.fieldId,
              bringToFront: params.bringToFront,
              scrollIntoView: params.scrollIntoView,
            });

            // Build response
            const response: FocusFieldResponse = {
              success: result.success || false,
              previousFocus: result.previousFocus,
              windowBroughtToFront: result.windowBroughtToFront || false,
              asyncJobId,
              errorCode: result.success ? undefined : result.errorCode || 'FOCUS_ERROR',
              errorMessage: result.success
                ? undefined
                : result.errorMessage || 'Failed to focus field',
            };

            logger.info('Field focus completed:', {
              fieldId: params.fieldId,
              success: response.success,
              windowBroughtToFront: response.windowBroughtToFront,
              asyncJobId,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(response, null, 2),
                },
              ],
            };
          }

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        logger.error(`Error in tool ${name}:`, error);

        const errorResponse = {
          success: false,
          errorCode: error instanceof z.ZodError ? 'VALIDATION_ERROR' : 'TOOL_ERROR',
          errorMessage: error instanceof Error ? error.message : 'Unknown error occurred',
          asyncJobId: generateAsyncJobId(),
        };

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(errorResponse, null, 2),
            },
          ],
          isError: true,
        };
      }
    });

    // Create transport and connect
    const transport = new StdioServerTransport();

    // Handle graceful shutdown
    const cleanup = async (): Promise<void> => {
      try {
        logger.info('Shutting down server...');
        await nativeClient.disconnect();
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
  } catch (error) {
    logger.error('Failed to start MCP server:', error);
    process.exit(1);
  }
}

// Run the server
main().catch(error => {
  logger.error('Unhandled error:', error);
  process.exit(1);
});
