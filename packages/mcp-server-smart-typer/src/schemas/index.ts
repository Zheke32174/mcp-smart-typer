/**
 * Zod schemas for MCP Smart Typer server
 * Defines request/response schemas for all MCP tools with security flags, async job IDs, and error codes
 */

import { z } from 'zod';

// Base response schema with common fields
const baseResponse = z.object({
  asyncJobId: z.string().optional().describe('Async job ID for tracking long-running operations'),
  errorCode: z.string().optional().describe('Error code if operation failed'),
  errorMessage: z.string().optional().describe('Human-readable error message'),
});

// Security flags schema
const securityFlags = z.array(z.string()).optional().describe('Security flags for operation validation');

// Field metadata schema
const fieldMetadata = z.object({
  description: z.string().optional().describe('Field description'),
  placeholder: z.string().optional().describe('Field placeholder text'),
  maxLength: z.number().optional().describe('Maximum input length'),
  inputType: z.enum(['text', 'password', 'email', 'number', 'tel', 'url']).optional().describe('Input field type'),
  required: z.boolean().optional().describe('Whether field is required'),
  pattern: z.string().optional().describe('Validation pattern regex'),
  bounds: z.object({
    x: z.number(),
    y: z.number(),
    width: z.number(),
    height: z.number(),
  }).optional().describe('Field coordinates and dimensions'),
  confidence: z.number().min(0).max(1).optional().describe('Detection confidence score'),
});

// Field information schema
const fieldInfo = z.object({
  id: z.string().describe('Unique field identifier'),
  name: z.string().describe('Field name or label'),
  type: z.string().describe('Field type (input, textarea, select, etc.)'),
  metadata: fieldMetadata.optional(),
});

// 1. DETECT FIELDS TOOL
export const detectFieldsRequest = z.object({
  contextHint: z.string().describe('Context hint for field detection (e.g., "login-form", "search-box")'),
  securityFlags: securityFlags,
  windowTitle: z.string().optional().describe('Specific window title to focus on'),
  includeHidden: z.boolean().default(false).describe('Whether to include hidden fields'),
  confidence: z.number().min(0).max(1).default(0.8).describe('Minimum confidence threshold for detection'),
});

export const detectFieldsResponse = baseResponse.extend({
  fields: z.array(fieldInfo).describe('List of detected fields with metadata'),
  windowInfo: z.object({
    title: z.string(),
    className: z.string(),
    handle: z.string(),
    bounds: z.object({
      x: z.number(),
      y: z.number(),
      width: z.number(),
      height: z.number(),
    }),
  }).optional().describe('Information about the active window'),
});

// 2. TYPE TEXT TOOL
export const typeTextRequest = z.object({
  fieldId: z.string().describe('Target field identifier'),
  text: z.string().describe('Text to type'),
  options: z.object({
    delay: z.number().min(0).max(5000).default(50).describe('Delay between keystrokes in milliseconds'),
    clearFirst: z.boolean().default(false).describe('Clear field before typing'),
    pressEnter: z.boolean().default(false).describe('Press Enter after typing'),
    simulate: z.boolean().default(false).describe('Simulate typing without actual input (for testing)'),
  }).optional(),
  securityFlags: securityFlags,
});

export const typeTextResponse = baseResponse.extend({
  success: z.boolean().describe('Whether typing was successful'),
  charactersTyped: z.number().optional().describe('Number of characters successfully typed'),
  timeTaken: z.number().optional().describe('Time taken to complete operation in milliseconds'),
});

// 3. GET FIELD VALUE TOOL
export const getFieldValueRequest = z.object({
  fieldId: z.string().describe('Field identifier to read from'),
  securityFlags: securityFlags,
  maxLength: z.number().default(10000).describe('Maximum length of value to retrieve'),
});

export const getFieldValueResponse = baseResponse.extend({
  value: z.string().describe('Current field value'),
  fieldInfo: fieldInfo.optional().describe('Updated field information'),
  isSecure: z.boolean().optional().describe('Whether field contains sensitive data'),
});

// 4. FOCUS FIELD TOOL
export const focusFieldRequest = z.object({
  fieldId: z.string().describe('Field identifier to focus'),
  securityFlags: securityFlags,
  bringToFront: z.boolean().default(true).describe('Whether to bring window to front'),
  scrollIntoView: z.boolean().default(true).describe('Whether to scroll field into view'),
});

export const focusFieldResponse = baseResponse.extend({
  success: z.boolean().describe('Whether focus was successful'),
  previousFocus: z.string().optional().describe('Previously focused element ID'),
  windowBroughtToFront: z.boolean().default(false).describe('Whether window was brought to front'),
});

// 5. ADDITIONAL UTILITY TOOLS

// Clear field tool
export const clearFieldRequest = z.object({
  fieldId: z.string().describe('Field identifier to clear'),
  securityFlags: securityFlags,
  method: z.enum(['selectAll', 'backspace', 'delete']).default('selectAll').describe('Method to clear field'),
});

export const clearFieldResponse = baseResponse.extend({
  success: z.boolean().describe('Whether clearing was successful'),
  previousValue: z.string().optional().describe('Previous field value (if not secure)'),
});

// Get window info tool
export const getWindowInfoRequest = z.object({
  windowTitle: z.string().optional().describe('Specific window title to get info for'),
  securityFlags: securityFlags,
});

export const getWindowInfoResponse = baseResponse.extend({
  windows: z.array(z.object({
    title: z.string(),
    className: z.string(),
    handle: z.string(),
    pid: z.number(),
    isActive: z.boolean(),
    bounds: z.object({
      x: z.number(),
      y: z.number(),
      width: z.number(),
      height: z.number(),
    }),
  })).describe('List of available windows'),
  activeWindow: z.string().optional().describe('Handle of currently active window'),
});

// Take screenshot tool for debugging
export const takeScreenshotRequest = z.object({
  region: z.object({
    x: z.number(),
    y: z.number(),
    width: z.number(),
    height: z.number(),
  }).optional().describe('Specific region to capture'),
  securityFlags: securityFlags,
  format: z.enum(['png', 'jpeg']).default('png').describe('Image format'),
  quality: z.number().min(1).max(100).default(90).describe('Image quality for JPEG'),
});

export const takeScreenshotResponse = baseResponse.extend({
  success: z.boolean().describe('Whether screenshot was taken'),
  imageData: z.string().optional().describe('Base64 encoded image data'),
  imageSize: z.object({
    width: z.number(),
    height: z.number(),
  }).optional().describe('Image dimensions'),
  filePath: z.string().optional().describe('Path to saved screenshot file'),
});

// Type definitions derived from schemas
export type DetectFieldsRequest = z.infer<typeof detectFieldsRequest>;
export type DetectFieldsResponse = z.infer<typeof detectFieldsResponse>;
export type TypeTextRequest = z.infer<typeof typeTextRequest>;
export type TypeTextResponse = z.infer<typeof typeTextResponse>;
export type GetFieldValueRequest = z.infer<typeof getFieldValueRequest>;
export type GetFieldValueResponse = z.infer<typeof getFieldValueResponse>;
export type FocusFieldRequest = z.infer<typeof focusFieldRequest>;
export type FocusFieldResponse = z.infer<typeof focusFieldResponse>;
export type ClearFieldRequest = z.infer<typeof clearFieldRequest>;
export type ClearFieldResponse = z.infer<typeof clearFieldResponse>;
export type GetWindowInfoRequest = z.infer<typeof getWindowInfoRequest>;
export type GetWindowInfoResponse = z.infer<typeof getWindowInfoResponse>;
export type TakeScreenshotRequest = z.infer<typeof takeScreenshotRequest>;
export type TakeScreenshotResponse = z.infer<typeof takeScreenshotResponse>;

// Example data for documentation
export const examples = {
  detectFieldsRequest: {
    contextHint: "login-form",
    securityFlags: ["authenticated"],
    windowTitle: "Login - My App",
    includeHidden: false,
    confidence: 0.8,
  } as DetectFieldsRequest,

  detectFieldsResponse: {
    fields: [
      {
        id: "field_username_001",
        name: "username",
        type: "input",
        metadata: {
          description: "Username input field",
          inputType: "text",
          required: true,
          bounds: { x: 100, y: 200, width: 200, height: 30 },
          confidence: 0.95,
        },
      },
      {
        id: "field_password_002", 
        name: "password",
        type: "input",
        metadata: {
          description: "Password input field",
          inputType: "password",
          required: true,
          bounds: { x: 100, y: 250, width: 200, height: 30 },
          confidence: 0.92,
        },
      },
    ],
    windowInfo: {
      title: "Login - My App",
      className: "Chrome_WidgetWin_1",
      handle: "0x001234AB",
      bounds: { x: 0, y: 0, width: 1920, height: 1080 },
    },
  } as DetectFieldsResponse,

  typeTextRequest: {
    fieldId: "field_username_001",
    text: "john.doe@example.com",
    options: {
      delay: 50,
      clearFirst: true,
      pressEnter: false,
      simulate: false,
    },
    securityFlags: ["encrypted"],
  } as TypeTextRequest,

  typeTextResponse: {
    success: true,
    charactersTyped: 19,
    timeTaken: 950,
    asyncJobId: "job_12345",
  } as TypeTextResponse,
};
