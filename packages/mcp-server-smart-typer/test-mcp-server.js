/**
 * Test script for MCP Smart Typer Server
 * Tests all the tools with various inputs
 */

import { spawn } from 'child_process';
import { writeFileSync, readFileSync } from 'fs';
import { join } from 'path';

class MCPTestClient {
  constructor() {
    this.server = null;
    this.requestId = 1;
  }

  async start() {
    console.log('Starting MCP Smart Typer server...');
    
    this.server = spawn('npm', ['start'], {
      cwd: join(process.cwd(), 'packages/mcp-server-smart-typer'),
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true
    });

    this.server.stderr.on('data', (data) => {
      console.log('Server log:', data.toString());
    });

    // Give the server time to start
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('Server should be ready!');
  }

  async sendRequest(method, params = {}) {
    const request = {
      jsonrpc: '2.0',
      id: this.requestId++,
      method,
      params
    };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Request timeout'));
      }, 10000);

      const handleResponse = (data) => {
        try {
          const response = JSON.parse(data.toString());
          if (response.id === request.id) {
            clearTimeout(timeout);
            this.server.stdout.off('data', handleResponse);
            if (response.error) {
              reject(new Error(`Server error: ${JSON.stringify(response.error)}`));
            } else {
              resolve(response.result);
            }
          }
        } catch (error) {
          console.log('Failed to parse response:', data.toString());
        }
      };

      this.server.stdout.on('data', handleResponse);
      
      console.log('Sending request:', JSON.stringify(request, null, 2));
      this.server.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  async testDetectFields() {
    console.log('\n=== Testing detect_fields ===');
    
    try {
      const result = await this.sendRequest('call_tool', {
        name: 'detect_fields',
        arguments: {
          contextHint: 'login-form',
          windowTitle: 'Test Login Window',
          includeHidden: false,
          confidence: 0.8
        }
      });
      
      console.log('✅ detect_fields result:', JSON.stringify(result, null, 2));
    } catch (error) {
      console.error('❌ detect_fields failed:', error.message);
    }
  }

  async testTypeText() {
    console.log('\n=== Testing type_text ===');
    
    try {
      const result = await this.sendRequest('call_tool', {
        name: 'type_text',
        arguments: {
          fieldId: 'field_username_001',
          text: 'test@example.com',
          options: {
            delay: 50,
            clearFirst: true,
            simulate: true // Use simulation mode
          },
          securityFlags: ['test']
        }
      });
      
      console.log('✅ type_text result:', JSON.stringify(result, null, 2));
    } catch (error) {
      console.error('❌ type_text failed:', error.message);
    }
  }

  async testGetFieldValue() {
    console.log('\n=== Testing get_field_value ===');
    
    try {
      const result = await this.sendRequest('call_tool', {
        name: 'get_field_value',
        arguments: {
          fieldId: 'field_username_001',
          maxLength: 1000
        }
      });
      
      console.log('✅ get_field_value result:', JSON.stringify(result, null, 2));
    } catch (error) {
      console.error('❌ get_field_value failed:', error.message);
    }
  }

  async testFocusField() {
    console.log('\n=== Testing focus_field ===');
    
    try {
      const result = await this.sendRequest('call_tool', {
        name: 'focus_field',
        arguments: {
          fieldId: 'field_password_002',
          bringToFront: true,
          scrollIntoView: true
        }
      });
      
      console.log('✅ focus_field result:', JSON.stringify(result, null, 2));
    } catch (error) {
      console.error('❌ focus_field failed:', error.message);
    }
  }

  async testListTools() {
    console.log('\n=== Testing list_tools ===');
    
    try {
      const result = await this.sendRequest('list_tools');
      console.log('✅ list_tools result:', JSON.stringify(result, null, 2));
    } catch (error) {
      console.error('❌ list_tools failed:', error.message);
    }
  }

  async runAllTests() {
    try {
      await this.start();
      
      await this.testListTools();
      await this.testDetectFields();
      await this.testTypeText();
      await this.testGetFieldValue();
      await this.testFocusField();
      
      console.log('\n🎉 All tests completed!');
    } catch (error) {
      console.error('❌ Test suite failed:', error);
    } finally {
      if (this.server) {
        this.server.kill();
      }
    }
  }
}

// Run the tests
const client = new MCPTestClient();
client.runAllTests().catch(console.error);
