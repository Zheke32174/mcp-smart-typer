/**
 * Focus Field Tool
 * Focuses a specified field and optionally brings its window to front
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import {
  focusFieldRequest,
  focusFieldResponse,
  FocusFieldRequest,
  FocusFieldResponse,
} from '../schemas/index.js';
import { logger } from '../utils/logger.js';
import { generateAsyncJobId } from '../utils/job-manager.js';

export function registerFocusFieldTool(server: McpServer, nativeClient: any) {
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'focus_field') {
      return;
    }

    try {
      // Validate input with Zod
      const params = focusFieldRequest.parse(request.params.arguments);
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
        errorMessage: result.success ? undefined : result.errorMessage || 'Failed to focus field',
      };

      // Validate response with Zod
      const validatedResponse = focusFieldResponse.parse(response);

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
            text: JSON.stringify(validatedResponse, null, 2),
          },
        ],
      };
    } catch (error) {
      logger.error('Failed to focus field:', error);

      // Return error response with proper schema
      const errorResponse: FocusFieldResponse = {
        success: false,
        windowBroughtToFront: false,
        errorCode: error instanceof z.ZodError ? 'VALIDATION_ERROR' : 'FOCUS_ERROR',
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
}
