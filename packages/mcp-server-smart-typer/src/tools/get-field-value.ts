/**
 * Get Field Value Tool
 * Retrieves the current value from a specified field
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import {
  getFieldValueRequest,
  getFieldValueResponse,
  GetFieldValueRequest,
  GetFieldValueResponse,
} from '../schemas/index.js';
import { logger } from '../utils/logger.js';
import { generateAsyncJobId } from '../utils/job-manager.js';

export function registerGetFieldValueTool(server: McpServer, nativeClient: any) {
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'get_field_value') {
      return;
    }

    try {
      // Validate input with Zod
      const params = getFieldValueRequest.parse(request.params.arguments);
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
        errorCode: result.success === false ? result.errorCode || 'RETRIEVAL_ERROR' : undefined,
        errorMessage:
          result.success === false ? result.errorMessage || 'Failed to get field value' : undefined,
      };

      // Validate response with Zod
      const validatedResponse = getFieldValueResponse.parse(response);

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
            text: JSON.stringify(validatedResponse, null, 2),
          },
        ],
      };
    } catch (error) {
      logger.error('Failed to get field value:', error);

      // Return error response with proper schema
      const errorResponse: GetFieldValueResponse = {
        value: '',
        isSecure: false,
        errorCode: error instanceof z.ZodError ? 'VALIDATION_ERROR' : 'RETRIEVAL_ERROR',
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
