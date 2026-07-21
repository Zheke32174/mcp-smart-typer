#!/usr/bin/env node

/**
 * Enhanced MCP Smart Typer Server
 * Wire Node server to helpers & expose MCP tools with:
 * - Python helper via gRPC
 * - Playwright for browser context
 * - Unified Field objects with source
 * - Async job tracking with MCP notifications
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { chromium, Browser, Page } from 'playwright';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { logger } from './utils/logger.js';
import {
  generateAsyncJobId,
  registerJob,
  updateJobStatus,
  getJobInfo,
  cleanupOldJobs,
} from './utils/job-manager.js';
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
  FocusFieldResponse,
} from './schemas/index.js';

const SERVER_NAME = 'mcp-smart-typer-enhanced';
const SERVER_VERSION = '2.0.0';

// Unified Field object with source
interface Field {
  id: string;
  name: string;
  type: 'text' | 'password' | 'email' | 'number' | 'tel' | 'url' | 'textarea' | 'select';
  source: 'browser' | 'desktop';
  metadata: {
    description?: string;
    placeholder?: string;
    maxLength?: number;
    required?: boolean;
    pattern?: string;
    bounds?: { x: number; y: number; width: number; height: number };
    confidence: number;
    // Browser-specific metadata
    selector?: string;
    tagName?: string;
    // Desktop-specific metadata
    windowHandle?: string;
    controlId?: string;
    // OCR/Vision metadata
    ocrContext?: string;
    ocrConfidence?: number;
    visionType?: string;
    visionConfidence?: number;
    analysisMethod?: string;
  };
  windowInfo?: {
    title: string;
    className: string;
    handle: string;
    bounds: { x: number; y: number; width: number; height: number };
    url?: string; // For browser contexts
  };
}

// Enhanced client that integrates both gRPC and Playwright
class EnhancedNativeClient {
  private grpcClient: any;
  private browser: Browser | null = null;
  private page: Page | null = null;
  private activeJobs = new Map<string, any>();

  constructor(private grpcPort: number = 50051) {}

  async connect(): Promise<void> {
    try {
      // Initialize gRPC client for Python helper
      await this.initializeGrpcClient();

      // Initialize Playwright browser context
      await this.initializeBrowserContext();

      logger.info('Enhanced client connected successfully', {
        grpcPort: this.grpcPort,
        browserReady: !!this.browser,
      });
    } catch (error) {
      logger.error('Failed to connect enhanced client:', error);
      throw error;
    }
  }

  private async initializeGrpcClient(): Promise<void> {
    try {
      const PROTO_PATH = '../native-helpers/proto/ui_automation.proto';
      const packageDefinition = await protoLoader.load(PROTO_PATH, {
        keepCase: true,
        longs: String,
        enums: String,
        defaults: true,
        oneofs: true,
      });

      const uiAutomation = grpc.loadPackageDefinition(packageDefinition).ui_automation as any;

      this.grpcClient = new uiAutomation.UIAutomationService(
        `localhost:${this.grpcPort}`,
        grpc.credentials.createInsecure()
      );

      // Test connection
      await new Promise<void>((resolve, reject) => {
        this.grpcClient.ping({}, (error: any, response: any) => {
          if (error) {
            reject(new Error(`gRPC connection failed: ${error.message}`));
          } else {
            logger.info('gRPC client connected to Python helper');
            resolve();
          }
        });
      });
    } catch (error) {
      logger.warn('gRPC client connection failed, using fallback mode:', error);
      // Don't throw - we can still work with browser-only mode
    }
  }

  private async initializeBrowserContext(): Promise<void> {
    try {
      this.browser = await chromium.launch({
        headless: false, // Keep visible for UI automation
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor'],
      });

      this.page = await this.browser.newPage();

      // Set up page event listeners for field detection
      await this.page.addInitScript(() => {
        // Inject field detection helpers
        (window as any).__mcpFieldDetector = {
          detectFields: () => {
            const fields: any[] = [];
            const inputs = document.querySelectorAll('input, textarea, select');

            inputs.forEach((element, index) => {
              const rect = element.getBoundingClientRect();
              const computedStyle = window.getComputedStyle(element);

              if (rect.width > 0 && rect.height > 0 && computedStyle.visibility !== 'hidden') {
                fields.push({
                  id: element.id || `browser_field_${Date.now()}_${index}`,
                  name:
                    element.getAttribute('name') ||
                    element.getAttribute('placeholder') ||
                    `field_${index}`,
                  type: (element as HTMLInputElement).type || element.tagName.toLowerCase(),
                  bounds: {
                    x: rect.left + window.scrollX,
                    y: rect.top + window.scrollY,
                    width: rect.width,
                    height: rect.height,
                  },
                  selector:
                    element.tagName.toLowerCase() +
                    (element.id ? `#${element.id}` : '') +
                    (element.className ? `.${element.className.split(' ').join('.')}` : ''),
                  tagName: element.tagName,
                  placeholder: element.getAttribute('placeholder'),
                  required: element.hasAttribute('required'),
                  maxLength: element.getAttribute('maxlength'),
                  pattern: element.getAttribute('pattern'),
                });
              }
            });

            return fields;
          },
        };
      });

      logger.info('Playwright browser context initialized');
    } catch (error) {
      logger.error('Failed to initialize browser context:', error);
      throw error;
    }
  }

  async detectFields(params: {
    contextHint: string;
    windowTitle?: string;
    includeHidden?: boolean;
    confidence?: number;
  }): Promise<{ fields: Field[]; windowInfo?: any }> {
    const asyncJobId = generateAsyncJobId();
    registerJob(asyncJobId, 'detect_fields', params);

    try {
      const fields: Field[] = [];
      let windowInfo: any = undefined;

      // Try browser context first if page is available
      if (this.page) {
        try {
          const browserFields = await this.detectBrowserFields(params);
          fields.push(
            ...browserFields.map(field => ({
              ...field,
              source: 'browser' as const,
              metadata: {
                ...field.metadata,
                confidence: field.metadata.confidence || 0.9,
                analysisMethod: 'browser_dom',
              },
            }))
          );

          // Get browser window info
          const url = this.page.url();
          const title = await this.page.title();
          windowInfo = {
            title,
            className: 'Browser',
            handle: 'browser_window',
            bounds: { x: 0, y: 0, width: 1920, height: 1080 },
            url,
          };
        } catch (browserError) {
          logger.warn('Browser field detection failed:', browserError);
        }
      }

      // Try desktop detection via gRPC if available
      if (this.grpcClient) {
        try {
          const desktopResult = await this.detectDesktopFields(params);
          fields.push(
            ...desktopResult.fields.map(field => ({
              ...field,
              source: 'desktop' as const,
              metadata: {
                ...field.metadata,
                confidence: field.metadata.confidence || 0.8,
                analysisMethod: 'desktop_ui',
              },
            }))
          );

          if (!windowInfo && desktopResult.windowInfo) {
            windowInfo = desktopResult.windowInfo;
          }
        } catch (desktopError) {
          logger.warn('Desktop field detection failed:', desktopError);
        }
      }

      updateJobStatus(asyncJobId, 'completed', { fieldsFound: fields.length });

      return { fields, windowInfo };
    } catch (error) {
      updateJobStatus(asyncJobId, 'failed', { error: error.message });
      throw error;
    }
  }

  private async detectBrowserFields(params: any): Promise<Field[]> {
    if (!this.page) return [];

    const browserFields = await this.page.evaluate(() => {
      return (window as any).__mcpFieldDetector?.detectFields() || [];
    });

    return browserFields.map((field: any, index: number) => ({
      id: field.id || `browser_field_${Date.now()}_${index}`,
      name: field.name || `browser_field_${index}`,
      type: this.mapBrowserFieldType(field.type),
      source: 'browser' as const,
      metadata: {
        description: field.placeholder || field.name,
        placeholder: field.placeholder,
        maxLength: field.maxLength ? parseInt(field.maxLength) : undefined,
        required: field.required,
        pattern: field.pattern,
        bounds: field.bounds,
        confidence: 0.9,
        selector: field.selector,
        tagName: field.tagName,
      },
    }));
  }

  private async detectDesktopFields(params: any): Promise<{ fields: Field[]; windowInfo?: any }> {
    return new Promise((resolve, reject) => {
      if (!this.grpcClient) {
        return reject(new Error('gRPC client not available'));
      }

      this.grpcClient.detectFields(params, (error: any, response: any) => {
        if (error) {
          reject(error);
        } else {
          const fields =
            response.fields?.map((field: any, index: number) => ({
              id: field.id || `desktop_field_${Date.now()}_${index}`,
              name: field.name || `desktop_field_${index}`,
              type: this.mapDesktopFieldType(field.type),
              source: 'desktop' as const,
              metadata: {
                description: field.description,
                placeholder: field.placeholder,
                maxLength: field.maxLength,
                required: field.required,
                pattern: field.pattern,
                bounds: field.bounds,
                confidence: field.confidence || 0.8,
                windowHandle: field.windowHandle,
                controlId: field.controlId,
              },
            })) || [];

          resolve({ fields, windowInfo: response.windowInfo });
        }
      });
    });
  }

  private mapBrowserFieldType(browserType: string): Field['type'] {
    const typeMap: Record<string, Field['type']> = {
      text: 'text',
      password: 'password',
      email: 'email',
      number: 'number',
      tel: 'tel',
      url: 'url',
      textarea: 'textarea',
      select: 'select',
    };
    return typeMap[browserType] || 'text';
  }

  private mapDesktopFieldType(desktopType: string): Field['type'] {
    const typeMap: Record<string, Field['type']> = {
      edit: 'text',
      password: 'password',
      numeric: 'number',
      combobox: 'select',
    };
    return typeMap[desktopType] || 'text';
  }

  async typeText(params: {
    fieldId: string;
    text: string;
    delay?: number;
    clearFirst?: boolean;
    pressEnter?: boolean;
  }): Promise<{
    success: boolean;
    charactersTyped?: number;
    errorCode?: string;
    errorMessage?: string;
  }> {
    const asyncJobId = generateAsyncJobId();
    registerJob(asyncJobId, 'type_text', {
      fieldId: params.fieldId,
      textLength: params.text.length,
    });

    try {
      // Determine if this is a browser or desktop field
      const fieldSource = this.determineFieldSource(params.fieldId);

      if (fieldSource === 'browser' && this.page) {
        return await this.typeBrowserText(params);
      } else if (fieldSource === 'desktop' && this.grpcClient) {
        return await this.typeDesktopText(params);
      } else {
        throw new Error('No suitable client available for field type');
      }
    } catch (error) {
      updateJobStatus(asyncJobId, 'failed', { error: error.message });
      return {
        success: false,
        errorCode: 'TYPE_ERROR',
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  private async typeBrowserText(params: any): Promise<any> {
    if (!this.page) throw new Error('Browser not available');

    const selector = this.extractSelectorFromFieldId(params.fieldId);

    try {
      // Find and focus the element
      await this.page.waitForSelector(selector, { timeout: 5000 });

      if (params.clearFirst) {
        await this.page.fill(selector, '');
      }

      // Type with delay if specified
      await this.page.type(selector, params.text, {
        delay: params.delay || 0,
      });

      if (params.pressEnter) {
        await this.page.press(selector, 'Enter');
      }

      return {
        success: true,
        charactersTyped: params.text.length,
      };
    } catch (error) {
      throw new Error(`Browser typing failed: ${error.message}`);
    }
  }

  private async typeDesktopText(params: any): Promise<any> {
    return new Promise((resolve, reject) => {
      this.grpcClient.typeText(params, (error: any, response: any) => {
        if (error) {
          reject(error);
        } else {
          resolve(response);
        }
      });
    });
  }

  private determineFieldSource(fieldId: string): 'browser' | 'desktop' {
    // Simple heuristic based on field ID
    if (fieldId.startsWith('browser_') || fieldId.includes('_dom_')) {
      return 'browser';
    }
    return 'desktop';
  }

  private extractSelectorFromFieldId(fieldId: string): string {
    // For browser fields, try to extract selector from metadata
    // This is a simplified implementation
    if (fieldId.includes('#')) {
      return fieldId.split('_').find(part => part.startsWith('#')) || `#${fieldId}`;
    }
    return `[data-field-id="${fieldId}"], #${fieldId}, [name="${fieldId}"]`;
  }

  async disconnect(): Promise<void> {
    try {
      if (this.browser) {
        await this.browser.close();
        this.browser = null;
        this.page = null;
      }

      if (this.grpcClient) {
        // gRPC client doesn't need explicit close in this implementation
        this.grpcClient = null;
      }

      logger.info('Enhanced client disconnected');
    } catch (error) {
      logger.error('Error during enhanced client disconnect:', error);
    }
  }

  // Additional methods for other operations...
  async getFieldValue(params: { fieldId: string; maxLength?: number }): Promise<any> {
    const fieldSource = this.determineFieldSource(params.fieldId);

    if (fieldSource === 'browser' && this.page) {
      const selector = this.extractSelectorFromFieldId(params.fieldId);
      const value = await this.page.inputValue(selector).catch(() => '');
      return { success: true, value: value.slice(0, params.maxLength) };
    } else if (fieldSource === 'desktop' && this.grpcClient) {
      return new Promise((resolve, reject) => {
        this.grpcClient.getFieldValue(params, (error: any, response: any) => {
          if (error) reject(error);
          else resolve(response);
        });
      });
    }

    throw new Error('No suitable client available');
  }

  async focusField(params: {
    fieldId: string;
    bringToFront?: boolean;
    scrollIntoView?: boolean;
  }): Promise<any> {
    const fieldSource = this.determineFieldSource(params.fieldId);

    if (fieldSource === 'browser' && this.page) {
      const selector = this.extractSelectorFromFieldId(params.fieldId);
      await this.page.focus(selector);
      if (params.scrollIntoView) {
        await this.page.locator(selector).scrollIntoViewIfNeeded();
      }
      return { success: true, windowBroughtToFront: true };
    } else if (fieldSource === 'desktop' && this.grpcClient) {
      return new Promise((resolve, reject) => {
        this.grpcClient.focusField(params, (error: any, response: any) => {
          if (error) reject(error);
          else resolve(response);
        });
      });
    }

    throw new Error('No suitable client available');
  }
}

async function main(): Promise<void> {
  try {
    logger.info(`Starting ${SERVER_NAME} v${SERVER_VERSION}...`);

    // Initialize enhanced native client
    const nativeClient = new EnhancedNativeClient();
    await nativeClient.connect();

    // Create MCP server with notification capabilities
    const server = new Server(
      {
        name: SERVER_NAME,
        version: SERVER_VERSION,
      },
      {
        capabilities: {
          tools: {},
          notifications: {}, // Enable notifications for async job tracking
        },
      }
    );

    // Set up job cleanup interval
    setInterval(
      () => {
        const cleaned = cleanupOldJobs(30); // Clean jobs older than 30 minutes
        if (cleaned > 0) {
          logger.info(`Cleaned up ${cleaned} old jobs`);
        }
      },
      5 * 60 * 1000
    ); // Every 5 minutes

    // Register list_tools handler
    server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'detect_fields',
            description:
              'Detect input fields from both browser and desktop contexts with unified Field objects',
            inputSchema: {
              type: 'object',
              properties: {
                contextHint: {
                  type: 'string',
                  description:
                    'Context hint for field detection (e.g., "login-form", "search-box")',
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
                sources: {
                  type: 'array',
                  items: { type: 'string', enum: ['browser', 'desktop'] },
                  description: 'Sources to search for fields',
                  default: ['browser', 'desktop'],
                },
              },
              required: ['contextHint'],
            },
          },
          {
            name: 'type_text',
            description: 'Type text into browser or desktop fields with automatic source detection',
            inputSchema: {
              type: 'object',
              properties: {
                fieldId: {
                  type: 'string',
                  description: 'Target field identifier (browser or desktop)',
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
                  },
                },
              },
              required: ['fieldId', 'text'],
            },
          },
          {
            name: 'get_field_value',
            description: 'Get field value from browser or desktop with automatic source detection',
            inputSchema: {
              type: 'object',
              properties: {
                fieldId: {
                  type: 'string',
                  description: 'Field identifier to read from',
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
            description: 'Focus field in browser or desktop with automatic source detection',
            inputSchema: {
              type: 'object',
              properties: {
                fieldId: {
                  type: 'string',
                  description: 'Field identifier to focus',
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
            name: 'get_job_status',
            description: 'Get status of async job operations',
            inputSchema: {
              type: 'object',
              properties: {
                jobId: {
                  type: 'string',
                  description: 'Job ID to check status for',
                },
              },
              required: ['jobId'],
            },
          },
        ],
      };
    });

    // Register call_tool handler with enhanced functionality
    server.setRequestHandler(CallToolRequestSchema, async request => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'detect_fields': {
            const params = detectFieldsRequest.parse(args);
            logger.info('Enhanced field detection:', params);

            const result = await nativeClient.detectFields(params);

            // Process fields to include source information
            const enhancedFields = result.fields.map(field => ({
              id: field.id,
              name: field.name,
              type: field.type,
              source: field.source, // 'browser' | 'desktop'
              metadata: {
                ...field.metadata,
                analysisMethod: field.metadata.analysisMethod,
              },
            }));

            const response: DetectFieldsResponse = {
              fields: enhancedFields,
              windowInfo: result.windowInfo,
              asyncJobId: generateAsyncJobId(),
            };

            // Send notification about completion
            server.sendNotification({
              method: 'mcp/job/completed',
              params: {
                jobId: response.asyncJobId,
                operation: 'detect_fields',
                result: {
                  fieldsFound: enhancedFields.length,
                  sources: enhancedFields.map(f => f.source),
                },
              },
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
            const params = typeTextRequest.parse(args);
            const startTime = Date.now();

            logger.info('Enhanced text typing:', {
              fieldId: params.fieldId,
              textLength: params.text.length,
            });

            const result = await nativeClient.typeText({
              fieldId: params.fieldId,
              text: params.text,
              delay: params.options?.delay,
              clearFirst: params.options?.clearFirst,
              pressEnter: params.options?.pressEnter,
            });

            const timeTaken = Date.now() - startTime;
            const asyncJobId = generateAsyncJobId();

            const response: TypeTextResponse = {
              success: result.success,
              charactersTyped: result.charactersTyped || params.text.length,
              timeTaken,
              asyncJobId,
              errorCode: result.errorCode,
              errorMessage: result.errorMessage,
            };

            // Send notification
            server.sendNotification({
              method: result.success ? 'mcp/job/completed' : 'mcp/job/failed',
              params: {
                jobId: asyncJobId,
                operation: 'type_text',
                result: { success: result.success, charactersTyped: result.charactersTyped },
              },
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
            const params = getFieldValueRequest.parse(args);
            logger.info('Enhanced field value retrieval:', { fieldId: params.fieldId });

            const result = await nativeClient.getFieldValue({
              fieldId: params.fieldId,
              maxLength: params.maxLength,
            });

            const response: GetFieldValueResponse = {
              value: result.value || '',
              fieldInfo: result.fieldInfo,
              isSecure: result.isSecure,
              asyncJobId: generateAsyncJobId(),
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

          case 'focus_field': {
            const params = focusFieldRequest.parse(args);
            logger.info('Enhanced field focus:', { fieldId: params.fieldId });

            const result = await nativeClient.focusField({
              fieldId: params.fieldId,
              bringToFront: params.bringToFront,
              scrollIntoView: params.scrollIntoView,
            });

            const response: FocusFieldResponse = {
              success: result.success,
              previousFocus: result.previousFocus,
              windowBroughtToFront: result.windowBroughtToFront,
              asyncJobId: generateAsyncJobId(),
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

          case 'get_job_status': {
            const { jobId } = args as { jobId: string };
            const jobInfo = getJobInfo(jobId);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(jobInfo || { error: 'Job not found' }, null, 2),
                },
              ],
            };
          }

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        logger.error(`Error in enhanced tool ${name}:`, error);

        const errorResponse = {
          success: false,
          errorCode: error instanceof z.ZodError ? 'VALIDATION_ERROR' : 'TOOL_ERROR',
          errorMessage: error instanceof Error ? error.message : 'Unknown error occurred',
          asyncJobId: generateAsyncJobId(),
        };

        // Send error notification
        server.sendNotification({
          method: 'mcp/job/failed',
          params: {
            jobId: errorResponse.asyncJobId,
            operation: name,
            error: errorResponse.errorMessage,
          },
        });

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
        logger.info('Shutting down enhanced server...');
        await nativeClient.disconnect();
        logger.info('Enhanced server shutdown complete');
      } catch (error) {
        logger.error('Error during enhanced cleanup:', error);
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
    logger.info(`${SERVER_NAME} v${SERVER_VERSION} running with enhanced capabilities`);
    logger.info('Enhanced MCP Smart Typer ready for connections!');
  } catch (error) {
    logger.error('Failed to start enhanced MCP server:', error);
    process.exit(1);
  }
}

// Run the enhanced server
main().catch(error => {
  logger.error('Unhandled error in enhanced server:', error);
  process.exit(1);
});
