/**
 * Jest test setup configuration
 * Sets up global test environment, logging, and common utilities
 */

import { beforeAll, afterAll, beforeEach } from '@jest/globals';
import { logger } from '../utils/logger.js';

// Configure logger for testing
beforeAll(() => {
  // Set test log level to reduce noise
  process.env.LOG_LEVEL = 'warn';

  // Initialize test environment
  console.log('🧪 Starting MCP Smart Typer test suite...');
});

beforeEach(() => {
  // Clear any test state between tests
  jest.clearAllMocks();
});

afterAll(() => {
  console.log('✅ Test suite completed');
});

// Global test timeout
jest.setTimeout(30000);

// Mock console methods in tests to reduce noise
const originalConsole = console;
global.console = {
  ...originalConsole,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: originalConsole.warn,
  error: originalConsole.error,
};
