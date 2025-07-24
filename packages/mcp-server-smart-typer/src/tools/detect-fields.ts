/**
 * Detect Fields Tool
 * Analyzes the active window to detect input fields with rich metadata
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { 
  detectFieldsRequest, 
  detectFieldsResponse,
  DetectFieldsResponse 
} from '../schemas/index.js';
import { logger } from '../utils/logger.js';
import { generateAsyncJobId } from '../utils/job-manager.js';
import { getFieldAnalyzer } from '../vision/field-analyzer.js';
import { getOCRInstance } from '../ocr/tesseract-ocr.js';

export function registerDetectFieldsTool(server: McpServer, nativeClient: any) {
  server.setToolHandler({
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
  }, async (request) => {
    try {
      // Validate input with Zod
      const params = detectFieldsRequest.parse(request.params.arguments);
      logger.info('Detecting fields with params:', params);

      // Generate async job ID for tracking
      const asyncJobId = generateAsyncJobId();
      
      // Try enhanced field detection with OCR and vision fallback
      let result;
      let enhancedFields = [];
      
      try {
        // Call native client with enhanced detection
        result = await nativeClient.detectFieldsWithFallback({
          contextHint: params.contextHint,
          windowTitle: params.windowTitle,
          includeHidden: params.includeHidden,
          confidence: params.confidence,
        });
        
        // If enhanced detection is available, use it
        if (result && result.fields) {
          enhancedFields = result.fields;
        } else {
          throw new Error('Enhanced detection not available, falling back to standard detection');
        }
      } catch (enhancedError) {
        logger.warn('Enhanced field detection failed, falling back to standard detection:', enhancedError);
        
        // Fall back to standard detection
        result = await nativeClient.detectFields({
          contextHint: params.contextHint,
          windowTitle: params.windowTitle,
          includeHidden: params.includeHidden,
          confidence: params.confidence,
        });
        
        enhancedFields = result.fields || [];
      }

      // Process and enrich field data
      const fields = enhancedFields.map((field: any, index: number) => ({
        id: field.id || `field_${Date.now()}_${index}`,
        name: field.name || `unnamed_field_${index}`,
        type: field.type || 'input',
        metadata: {
          description: field.description,
          placeholder: field.placeholder,
          maxLength: field.maxLength,
          inputType: field.semantic_type || detectInputType(field),
          required: field.required || false,
          pattern: field.pattern,
          bounds: field.bounds ? {
            x: Math.round(field.bounds.x),
            y: Math.round(field.bounds.y),
            width: Math.round(field.bounds.width),
            height: Math.round(field.bounds.height),
          } : undefined,
          confidence: field.confidence || 0.8,
          // Enhanced metadata from OCR and vision analysis
          ocrContext: field.ocr_context,
          ocrConfidence: field.ocr_confidence,
          visionType: field.vision_type,
          visionConfidence: field.vision_confidence,
          analysisMethod: field.analysis_method,
        },
      }));

      // Build response
      const response: DetectFieldsResponse = {
        fields,
        windowInfo: result.windowInfo ? {
          title: result.windowInfo.title,
          className: result.windowInfo.className,
          handle: result.windowInfo.handle,
          bounds: {
            x: Math.round(result.windowInfo.bounds.x),
            y: Math.round(result.windowInfo.bounds.y),
            width: Math.round(result.windowInfo.bounds.width),
            height: Math.round(result.windowInfo.bounds.height),
          },
        } : undefined,
        asyncJobId,
      };

      // Validate response with Zod
      const validatedResponse = detectFieldsResponse.parse(response);
      
      logger.info(`Detected ${fields.length} fields`, { 
        asyncJobId, 
        fieldTypes: fields.map(f => f.type),
        windowTitle: result.windowInfo?.title 
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
      logger.error('Failed to detect fields:', error);
      
      // Return error response with proper schema
      const errorResponse: DetectFieldsResponse = {
        fields: [],
        errorCode: error instanceof z.ZodError ? 'VALIDATION_ERROR' : 'DETECTION_ERROR',
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

/**
 * Detect input type from field characteristics
 */
function detectInputType(field: any): 'text' | 'password' | 'email' | 'number' | 'tel' | 'url' {
  const name = field.name?.toLowerCase() || '';
  const placeholder = field.placeholder?.toLowerCase() || '';
  const className = field.className?.toLowerCase() || '';
  
  // Password fields
  if (name.includes('password') || 
      name.includes('passwd') || 
      name.includes('pwd') ||
      field.type === 'password' ||
      className.includes('password')) {
    return 'password';
  }
  
  // Email fields
  if (name.includes('email') || 
      name.includes('mail') ||
      placeholder.includes('@') ||
      placeholder.includes('email')) {
    return 'email';
  }
  
  // Phone/tel fields
  if (name.includes('phone') || 
      name.includes('tel') ||
      name.includes('mobile') ||
      placeholder.includes('phone')) {
    return 'tel';
  }
  
  // URL fields
  if (name.includes('url') || 
      name.includes('website') ||
      name.includes('link') ||
      placeholder.includes('http')) {
    return 'url';
  }
  
  // Numeric fields
  if (name.includes('number') || 
      name.includes('amount') ||
      name.includes('price') ||
      name.includes('age') ||
      field.type === 'number') {
    return 'number';
  }
  
  // Default to text
  return 'text';
}
