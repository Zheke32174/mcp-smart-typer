/**
 * Type Text Tool
 * Types text into a specified field with advanced security, audit, and rollback features
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import {
  typeTextRequest,
  typeTextResponse,
  TypeTextRequest,
  TypeTextResponse,
} from '../schemas/index.js';
import { logger } from '../utils/logger.js';
import { generateAsyncJobId } from '../utils/job-manager.js';
import { permissionManager } from '../security/permission-manager.js';
import { securityManager } from '../security/security-manager.js';
import { getAuditLogger } from '../security/audit-logger.js';
import { rollbackManager } from '../security/rollback-manager.js';

export function registerTypeTextTool(server: McpServer, nativeClient: any) {
  server.setRequestHandler('call_tool', async (request: any) => {
    if (request.params?.name !== 'type_text') {
      return;
    }

    const startTime = Date.now();
    const sessionId = 'default-session'; // TODO: Extract from request context
    let asyncJobId: string;

    try {
      // Validate input with Zod
      const params = typeTextRequest.parse(request.params.arguments);
      asyncJobId = generateAsyncJobId();

      // === PERMISSION CHECK ===
      try {
        permissionManager.validateTypingPermission({
          sessionId,
          toolName: 'type_text',
          fieldId: params.fieldId,
          securityFlags: params.securityFlags,
          mcpRootPermission: params.securityFlags?.includes('mcp_root_permission'),
        });

        getAuditLogger().logPermissionCheck('type_text', true, 'Permission granted');
      } catch (permissionError) {
        getAuditLogger().logPermissionCheck(
          'type_text',
          false,
          permissionError instanceof Error ? permissionError.message : String(permissionError)
        );
        throw permissionError;
      }

      // === SECURITY VALIDATION ===
      const securityValidation = securityManager.validateSecurityFlags(params.securityFlags);
      getAuditLogger().logSecurityValidation(
        'type_text',
        securityValidation.isValid,
        securityValidation.warnings
      );

      if (!securityValidation.isValid) {
        throw new Error(`Security validation failed: ${securityValidation.warnings.join(', ')}`);
      }

      // Detect sensitive field
      const sensitiveField = securityManager.detectSensitiveField(params.fieldId);
      const isPasswordField = securityManager.isPasswordField(params.fieldId);

      // Create secure log entry
      const secureLogEntry = securityManager.createSecureLogEntry('info', 'Typing text to field', {
        fieldId: params.fieldId,
        textLength: params.text.length,
        options: params.options,
        sensitiveField: sensitiveField?.fieldType,
        isPasswordField,
      });

      logger.secureLog('info', secureLogEntry.message, secureLogEntry.data, {
        fieldId: params.fieldId,
        hasSensitiveData: secureLogEntry.hasSensitiveData,
      });

      // === ROLLBACK EXECUTION ===
      const rollbackResult = await rollbackManager.executeWithRollback(
        'type_text',
        params.fieldId,
        async () => {
          // Handle simulation mode
          if (params.options?.simulate) {
            logger.info('Simulating text typing (no actual input)', {
              fieldId: params.fieldId,
              asyncJobId,
            });

            return {
              success: true,
              charactersTyped: params.text.length,
              timeTaken: Math.min(params.text.length * (params.options?.delay || 50), 1000),
            };
          }

          // Call native client to type text
          return await nativeClient.typeText({
            fieldId: params.fieldId,
            text: params.text,
            delay: params.options?.delay || 50,
            clearFirst: params.options?.clearFirst || false,
            pressEnter: params.options?.pressEnter || false,
          });
        },
        undefined, // No custom rollback executor
        {
          dryRun: params.options?.simulate || rollbackManager.isDryRunMode(),
          captureOriginalValue: !isPasswordField, // Don't capture password field values
        }
      );

      const timeTaken = Date.now() - startTime;

      // Handle dry-run result
      if (rollbackResult.dryRunResult) {
        const dryRunResponse: TypeTextResponse = {
          success: rollbackResult.dryRunResult.wouldSucceed,
          charactersTyped: 0,
          timeTaken: rollbackResult.dryRunResult.estimatedTime,
          asyncJobId,
          errorCode: rollbackResult.dryRunResult.wouldSucceed ? undefined : 'DRY_RUN_FAILED',
          errorMessage: rollbackResult.dryRunResult.wouldSucceed
            ? undefined
            : `Dry-run warnings: ${rollbackResult.dryRunResult.warnings.join(', ')}`,
        };

        // Log dry-run result
        getAuditLogger().logTypingOperation(
          params.fieldId,
          rollbackResult.dryRunResult.wouldSucceed,
          {
            isDryRun: true,
            predictedChanges: rollbackResult.dryRunResult.predictedChanges,
            warnings: rollbackResult.dryRunResult.warnings,
            estimatedTime: rollbackResult.dryRunResult.estimatedTime,
          },
          rollbackResult.dryRunResult.wouldSucceed ? undefined : 'DRY_RUN_FAILED'
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  ...dryRunResponse,
                  dryRunResult: rollbackResult.dryRunResult,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      // Handle execution error
      if (rollbackResult.error) {
        throw rollbackResult.error;
      }

      // Build successful response
      const result = rollbackResult.result!;
      const response: TypeTextResponse = {
        success: result.success || false,
        charactersTyped: result.charactersTyped || params.text.length,
        timeTaken,
        asyncJobId,
        errorCode: result.success ? undefined : result.errorCode || 'TYPING_ERROR',
        errorMessage: result.success ? undefined : result.errorMessage || 'Failed to type text',
      };

      // Validate response with Zod
      const validatedResponse = typeTextResponse.parse(response);

      // Log successful operation
      getAuditLogger().logTypingOperation(
        params.fieldId,
        response.success,
        {
          charactersTyped: response.charactersTyped,
          timeTaken: response.timeTaken,
          clearFirst: params.options?.clearFirst || false,
          pressEnter: params.options?.pressEnter || false,
          delay: params.options?.delay || 50,
          hasSensitiveData: secureLogEntry.hasSensitiveData,
        },
        response.errorCode
      );

      logger.secureLog(
        'info',
        'Text typing completed',
        {
          success: response.success,
          charactersTyped: response.charactersTyped,
          timeTaken: response.timeTaken,
          asyncJobId,
        },
        {
          fieldId: params.fieldId,
          hasSensitiveData: secureLogEntry.hasSensitiveData,
        }
      );

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(validatedResponse, null, 2),
          },
        ],
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      const errorCode = error instanceof z.ZodError ? 'VALIDATION_ERROR' : 'TYPING_ERROR';

      logger.error('Failed to type text:', error);

      const timeTaken = Date.now() - startTime;

      // Log failed operation
      if (asyncJobId!) {
        getAuditLogger().logTypingOperation(
          'unknown-field',
          false,
          {
            timeTaken,
            error: errorMessage,
          },
          errorCode
        );
      }

      // Return error response with proper schema
      const errorResponse: TypeTextResponse = {
        success: false,
        charactersTyped: 0,
        timeTaken,
        errorCode,
        errorMessage,
        asyncJobId: asyncJobId || generateAsyncJobId(),
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
