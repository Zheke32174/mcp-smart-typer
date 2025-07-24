#!/usr/bin/env tsx

/**
 * Script to generate JSON Schema files from Zod schemas
 * Converts all Zod schemas to JSON Schema format for documentation and validation
 */

import { zodToJsonSchema } from 'zod-to-json-schema';
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import {
  detectFieldsRequest,
  detectFieldsResponse,
  typeTextRequest,
  typeTextResponse,
  getFieldValueRequest,
  getFieldValueResponse,
  focusFieldRequest,
  focusFieldResponse,
  clearFieldRequest,
  clearFieldResponse,
  getWindowInfoRequest,
  getWindowInfoResponse,
  takeScreenshotRequest,
  takeScreenshotResponse,
  examples,
} from '../src/schemas/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Output directory for JSON schemas
const outputDir = join(__dirname, '../docs/schemas');

// Ensure output directory exists
mkdirSync(outputDir, { recursive: true });

// Schema definitions with metadata
const schemas = [
  {
    name: 'detect-fields-request',
    schema: detectFieldsRequest,
    description: 'Request schema for detecting fields in the active window',
    example: examples.detectFieldsRequest,
  },
  {
    name: 'detect-fields-response',
    schema: detectFieldsResponse,
    description: 'Response schema for field detection results',
    example: examples.detectFieldsResponse,
  },
  {
    name: 'type-text-request',
    schema: typeTextRequest,
    description: 'Request schema for typing text into a field',
    example: examples.typeTextRequest,
  },
  {
    name: 'type-text-response',
    schema: typeTextResponse,
    description: 'Response schema for text typing results',
    example: examples.typeTextResponse,
  },
  {
    name: 'get-field-value-request',
    schema: getFieldValueRequest,
    description: 'Request schema for retrieving field values',
  },
  {
    name: 'get-field-value-response',
    schema: getFieldValueResponse,
    description: 'Response schema for field value retrieval',
  },
  {
    name: 'focus-field-request',
    schema: focusFieldRequest,
    description: 'Request schema for focusing a field',
  },
  {
    name: 'focus-field-response',
    schema: focusFieldResponse,
    description: 'Response schema for field focusing results',
  },
  {
    name: 'clear-field-request',
    schema: clearFieldRequest,
    description: 'Request schema for clearing field content',
  },
  {
    name: 'clear-field-response',
    schema: clearFieldResponse,
    description: 'Response schema for field clearing results',
  },
  {
    name: 'get-window-info-request',
    schema: getWindowInfoRequest,
    description: 'Request schema for retrieving window information',
  },
  {
    name: 'get-window-info-response',
    schema: getWindowInfoResponse,
    description: 'Response schema for window information',
  },
  {
    name: 'take-screenshot-request',
    schema: takeScreenshotRequest,
    description: 'Request schema for taking screenshots',
  },
  {
    name: 'take-screenshot-response',
    schema: takeScreenshotResponse,
    description: 'Response schema for screenshot results',
  },
];

// Generate JSON schemas
console.log('Generating JSON Schema files...');

const allSchemas: Record<string, any> = {};

for (const { name, schema, description, example } of schemas) {
  try {
    const jsonSchema = zodToJsonSchema(schema, {
      name: name,
      $refStrategy: 'relative',
      target: 'jsonSchema7',
      definitions: {},
    });

    // Add metadata
    const enrichedSchema = {
      ...jsonSchema,
      description,
      ...(example && { example }),
      $schema: 'http://json-schema.org/draft-07/schema#',
      $id: `https://schemas.mcp-smart-typer.dev/${name}.json`,
    };

    // Write individual schema file
    const filePath = join(outputDir, `${name}.json`);
    writeFileSync(filePath, JSON.stringify(enrichedSchema, null, 2));
    
    // Add to combined schemas
    allSchemas[name] = enrichedSchema;
    
    console.log(`✓ Generated ${name}.json`);
  } catch (error) {
    console.error(`✗ Failed to generate ${name}.json:`, error);
  }
}

// Create combined schema file
const combinedSchema = {
  $schema: 'http://json-schema.org/draft-07/schema#',
  $id: 'https://schemas.mcp-smart-typer.dev/all-schemas.json',
  title: 'MCP Smart Typer - All Schemas',
  description: 'Combined JSON Schema definitions for all MCP Smart Typer tools',
  type: 'object',
  properties: allSchemas,
  definitions: {
    securityFlags: {
      type: 'array',
      items: { type: 'string' },
      description: 'Security flags for operation validation',
    },
    asyncJobId: {
      type: 'string',
      description: 'Async job ID for tracking long-running operations',
    },
    errorCode: {
      type: 'string',
      description: 'Error code if operation failed',
    },
    bounds: {
      type: 'object',
      properties: {
        x: { type: 'number' },
        y: { type: 'number' },
        width: { type: 'number' },
        height: { type: 'number' },
      },
      required: ['x', 'y', 'width', 'height'],
      description: 'Rectangular bounds with coordinates and dimensions',
    },
  },
};

writeFileSync(
  join(outputDir, 'all-schemas.json'),
  JSON.stringify(combinedSchema, null, 2)
);

console.log('✓ Generated all-schemas.json');

// Generate TypeScript types file for external use
const typesContent = `/**
 * Generated TypeScript types from Zod schemas
 * This file is auto-generated. Do not edit manually.
 */

${schemas.map(({ name, description }) => 
  `// ${description}\nexport type ${name.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')} = any;`
).join('\n\n')}

// Re-export all types from schemas
export * from '../src/schemas/index.js';
`;

writeFileSync(join(outputDir, 'types.ts'), typesContent);
console.log('✓ Generated types.ts');

// Generate OpenAPI specification
const openApiSpec = {
  openapi: '3.0.3',
  info: {
    title: 'MCP Smart Typer API',
    description: 'AI-powered typing automation with Windows UI integration',
    version: '1.0.0',
    contact: {
      name: 'MCP Smart Typer Team',
      url: 'https://github.com/mcp-smart-typer/mcp-smart-typer',
    },
    license: {
      name: 'MIT',
      url: 'https://opensource.org/licenses/MIT',
    },
  },
  servers: [
    {
      url: 'stdio://',
      description: 'MCP Server over stdio transport',
    },
  ],
  paths: {
    '/detect-fields': {
      post: {
        summary: 'Detect fields in the active window',
        description: 'Analyzes the current window to detect input fields with metadata',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/detect-fields-request' },
            },
          },
        },
        responses: {
          '200': {
            description: 'Fields detected successfully',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/detect-fields-response' },
              },
            },
          },
        },
      },
    },
    '/type-text': {
      post: {
        summary: 'Type text into a field',
        description: 'Types text into a specified field with configurable options',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/type-text-request' },
            },
          },
        },
        responses: {
          '200': {
            description: 'Text typed successfully',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/type-text-response' },
              },
            },
          },
        },
      },
    },
  },
  components: {
    schemas: Object.fromEntries(
      schemas.map(({ name, schema }) => [
        name,
        zodToJsonSchema(schema, { target: 'openApi3' }),
      ])
    ),
  },
};

writeFileSync(
  join(outputDir, 'openapi.json'),
  JSON.stringify(openApiSpec, null, 2)
);

console.log('✓ Generated openapi.json');
console.log(`\nAll schema files generated in: ${outputDir}`);
console.log('\nGenerated files:');
console.log('- Individual JSON Schema files for each tool');
console.log('- all-schemas.json (combined schemas)');
console.log('- types.ts (TypeScript type definitions)');
console.log('- openapi.json (OpenAPI specification)');
