/**
 * Test utilities for MCP Smart Typer
 * Provides common testing functions and mock implementations
 */

import { spawn, ChildProcess } from 'child_process';
import { Browser, Page, chromium } from 'playwright';
import { join } from 'path';
import { promises as fs } from 'fs';

export interface TestMCPClient {
  server: ChildProcess | null;
  requestId: number;
  sendRequest(method: string, params?: any): Promise<any>;
  start(): Promise<void>;
  stop(): Promise<void>;
}

export interface TestEnvironment {
  browser: Browser;
  page: Page;
  mcpClient: TestMCPClient;
}

/**
 * Creates a test MCP client that communicates with the server
 */
export function createTestMCPClient(): TestMCPClient {
  let server: ChildProcess | null = null;
  let requestId = 1;

  return {
    server,
    requestId,

    async start() {
      console.log('Starting test MCP server...');

      server = spawn('node', ['dist/index.js'], {
        cwd: join(process.cwd()),
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true,
        env: {
          ...process.env,
          NODE_ENV: 'test',
          LOG_LEVEL: 'error',
        },
      });

      if (!server) {
        throw new Error('Failed to start MCP server');
      }

      this.server = server;

      server.stderr?.on('data', data => {
        console.error('Server error:', data.toString());
      });

      // Give the server time to start
      await new Promise(resolve => setTimeout(resolve, 3000));
      console.log('Test MCP server started');
    },

    async stop() {
      if (server) {
        server.kill('SIGTERM');
        await new Promise(resolve => setTimeout(resolve, 1000));
        if (!server.killed) {
          server.kill('SIGKILL');
        }
        server = null;
        this.server = null;
      }
    },

    async sendRequest(method: string, params = {}) {
      if (!server) {
        throw new Error('Server not started');
      }

      const request = {
        jsonrpc: '2.0',
        id: requestId++,
        method,
        params,
      };

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error(`Request timeout for ${method}`));
        }, 10000);

        const handleResponse = (data: Buffer) => {
          try {
            const response = JSON.parse(data.toString());
            if (response.id === request.id && response.id !== undefined) {
              clearTimeout(timeout);
              server?.stdout?.off('data', handleResponse);
              if (response.error) {
                reject(new Error(`Server error: ${JSON.stringify(response.error)}`));
              } else {
                resolve(response.result);
              }
            }
          } catch (error) {
            // Ignore parsing errors from partial data
          }
        };

        server?.stdout?.on('data', handleResponse);
        server?.stdin?.write(JSON.stringify(request) + '\n');
      });
    },
  };
}

/**
 * Creates a test browser page with common test page content
 */
export async function createTestPage(browser: Browser): Promise<Page> {
  const page = await browser.newPage();

  // Set viewport for consistent testing
  await page.setViewportSize({ width: 1200, height: 800 });

  return page;
}

/**
 * Creates a sample HTML page for testing field detection
 */
export async function createSampleLoginPage(page: Page): Promise<void> {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Login Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .login-form {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        input[type="text"], input[type="password"], input[type="email"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input:focus {
            border-color: #007bff;
            outline: none;
        }
        .btn {
            background-color: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
        }
        .btn:hover {
            background-color: #0056b3;
        }
        .remember-me {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .remember-me input {
            width: auto;
            margin-right: 8px;
        }
        .hidden-field {
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-form">
        <h2>Login to Your Account</h2>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username or Email:</label>
                <input type="email" id="username" name="username" placeholder="Enter your email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter your password" required>
            </div>
            
            <div class="form-group remember-me">
                <input type="checkbox" id="remember" name="remember">
                <label for="remember">Remember me</label>
            </div>
            
            <!-- Hidden field for testing -->
            <input type="hidden" id="token" name="token" value="test-token-123" class="hidden-field">
            
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <div style="margin-top: 20px; text-align: center;">
            <a href="#forgot">Forgot Password?</a>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Login form submitted (test mode)');
        });
    </script>
</body>
</html>`;

  await page.setContent(html);
  await page.waitForLoadState('domcontentloaded');
}

/**
 * Creates a sample search page for testing different field types
 */
export async function createSampleSearchPage(page: Page): Promise<void> {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Search Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        .search-container {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 18px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            margin-bottom: 20px;
            box-sizing: border-box;
        }
        .filters {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
        }
        .filter-group label {
            margin-bottom: 5px;
            font-weight: bold;
        }
        .filter-group input, .filter-group select {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .search-btn {
            background: #28a745;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="search-container">
        <h2>Advanced Search</h2>
        <form id="searchForm">
            <input type="text" id="mainSearch" class="search-box" placeholder="Search for anything..." required>
            
            <div class="filters">
                <div class="filter-group">
                    <label for="category">Category:</label>
                    <select id="category" name="category">
                        <option value="">All Categories</option>
                        <option value="electronics">Electronics</option>
                        <option value="books">Books</option>
                        <option value="clothing">Clothing</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="minPrice">Min Price:</label>
                    <input type="number" id="minPrice" name="minPrice" placeholder="0" min="0">
                </div>
                
                <div class="filter-group">
                    <label for="maxPrice">Max Price:</label>
                    <input type="number" id="maxPrice" name="maxPrice" placeholder="1000" min="0">
                </div>
                
                <div class="filter-group">
                    <label for="location">Location:</label>
                    <input type="text" id="location" name="location" placeholder="Enter city or zip">
                </div>
            </div>
            
            <button type="submit" class="search-btn">Search</button>
        </form>
    </div>

    <script>
        document.getElementById('searchForm').addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Search form submitted (test mode)');
        });
    </script>
</body>
</html>`;

  await page.setContent(html);
  await page.waitForLoadState('domcontentloaded');
}

/**
 * Mock native client for testing without actual Windows UI automation
 */
export function createMockNativeClient() {
  return {
    async detectFields(params: any) {
      // Simulate field detection based on the current test page
      const mockFields = [
        {
          id: 'field_username_001',
          name: 'username',
          type: 'email',
          description: 'Username or Email field',
          placeholder: 'Enter your email',
          semantic_type: 'email',
          required: true,
          bounds: { x: 100, y: 150, width: 300, height: 40 },
          confidence: 0.95,
          analysis_method: 'mock',
        },
        {
          id: 'field_password_002',
          name: 'password',
          type: 'password',
          description: 'Password field',
          placeholder: 'Enter your password',
          semantic_type: 'password',
          required: true,
          bounds: { x: 100, y: 200, width: 300, height: 40 },
          confidence: 0.92,
          analysis_method: 'mock',
        },
      ];

      return {
        fields: mockFields,
        windowInfo: {
          title: 'Test Login Page',
          className: 'Chrome_WidgetWin_1',
          handle: '12345',
          bounds: { x: 0, y: 0, width: 1200, height: 800 },
        },
      };
    },

    async detectFieldsWithFallback(params: any) {
      return this.detectFields(params);
    },

    async typeText(params: any) {
      // Simulate typing with realistic timing
      const delay = params.delay || 50;
      const simulatedTime = params.text.length * delay;

      // Simulate some realistic scenarios
      if (params.fieldId === 'invalid_field') {
        throw new Error('Field not found');
      }

      return {
        success: true,
        charactersTyped: params.text.length,
        timeTaken: simulatedTime,
        fieldId: params.fieldId,
      };
    },

    async getFieldValue(params: any) {
      // Return mock values for different fields
      const mockValues: Record<string, string> = {
        field_username_001: 'test@example.com',
        field_password_002: '***', // Masked password
        field_search_001: 'sample search query',
      };

      return {
        value: mockValues[params.fieldId] || '',
        fieldId: params.fieldId,
        success: true,
      };
    },

    async focusField(params: any) {
      return {
        success: true,
        fieldId: params.fieldId,
        focused: true,
      };
    },
  };
}

/**
 * Waits for a condition to be true with timeout
 */
export async function waitFor(
  condition: () => boolean | Promise<boolean>,
  timeout = 5000
): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (await condition()) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Condition not met within ${timeout}ms`);
}

/**
 * Takes a screenshot for debugging failed tests
 */
export async function takeDebugScreenshot(page: Page, testName: string): Promise<string> {
  const screenshotPath = `./test-screenshots/${testName}-${Date.now()}.png`;
  await fs.mkdir('./test-screenshots', { recursive: true });
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return screenshotPath;
}
