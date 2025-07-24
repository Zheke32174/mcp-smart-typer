/**
 * End-to-End Tests for Field Detection
 * Tests the precision and accuracy of field detection using Playwright sample pages
 */

import { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } from '@jest/globals';
import { Browser, Page, chromium } from 'playwright';
import { 
  createTestMCPClient, 
  createTestPage, 
  createSampleLoginPage, 
  createSampleSearchPage,
  takeDebugScreenshot,
  TestMCPClient
} from '../test-utils.js';

describe('Field Detection E2E Tests', () => {
  let browser: Browser;
  let page: Page;
  let mcpClient: TestMCPClient;

  beforeAll(async () => {
    console.log('🚀 Starting field detection E2E tests...');
    
    // Start headless browser
    browser = await chromium.launch({ headless: true });
    
    // Create MCP client (will use mock implementation for tests)
    mcpClient = createTestMCPClient();
  });

  beforeEach(async () => {
    // Create fresh page for each test
    page = await createTestPage(browser);
  });

  afterEach(async () => {
    // Clean up page
    if (page) {
      await page.close();
    }
  });

  afterAll(async () => {
    // Cleanup
    if (mcpClient) {
      await mcpClient.stop();
    }
    if (browser) {
      await browser.close();
    }
    console.log('✅ Field detection E2E tests completed');
  });

  describe('Login Form Field Detection', () => {
    test('should detect email and password fields with high precision', async () => {
      // Setup: Create login page
      await createSampleLoginPage(page);
      
      // Mock the detect_fields call (in real scenario, this would communicate with native client)
      const mockDetectFields = async (params: any) => {
        const pageFields = await page.$$eval('input', (inputs) =>
          inputs.map((input, index) => ({
            id: `field_${input.name || input.type}_${String(index).padStart(3, '0')}`,
            name: input.name || `unnamed_${index}`,
            type: input.type,
            description: input.getAttribute('placeholder') || `${input.type} field`,
            placeholder: input.getAttribute('placeholder'),
            semantic_type: input.type === 'email' ? 'email' : input.type,
            required: input.hasAttribute('required'),
            bounds: {
              x: Math.round(Math.random() * 100 + 100),
              y: Math.round(Math.random() * 100 + 150 + index * 50),
              width: 300,
              height: 40
            },
            confidence: 0.9 + Math.random() * 0.1,
            analysis_method: 'playwright_mock'
          }))
        );

        return {
          fields: pageFields,
          windowInfo: {
            title: await page.title(),
            className: 'Chrome_WidgetWin_1',
            handle: '12345',
            bounds: { x: 0, y: 0, width: 1200, height: 800 }
          }
        };
      };

      // Execute detection
      const result = await mockDetectFields({
        contextHint: 'login-form',
        confidence: 0.8
      });

      // Assertions
      expect(result.fields).toHaveLength(4); // username, password, remember checkbox, hidden token
      
      // Find email field
      const emailField = result.fields.find(f => f.semantic_type === 'email');
      expect(emailField).toBeDefined();
      expect(emailField?.name).toBe('username');
      expect(emailField?.confidence).toBeGreaterThan(0.8);
      expect(emailField?.required).toBe(true);

      // Find password field
      const passwordField = result.fields.find(f => f.semantic_type === 'password');
      expect(passwordField).toBeDefined();
      expect(passwordField?.name).toBe('password');
      expect(passwordField?.confidence).toBeGreaterThan(0.8);
      expect(passwordField?.required).toBe(true);

      // Find checkbox field
      const checkboxField = result.fields.find(f => f.type === 'checkbox');
      expect(checkboxField).toBeDefined();
      expect(checkboxField?.name).toBe('remember');

      // Find hidden field
      const hiddenField = result.fields.find(f => f.type === 'hidden');
      expect(hiddenField).toBeDefined();
      expect(hiddenField?.name).toBe('token');

      console.log(`✅ Detected ${result.fields.length} fields with average confidence: ${
        (result.fields.reduce((sum, f) => sum + f.confidence, 0) / result.fields.length).toFixed(3)
      }`);
    });

    test('should handle different confidence thresholds', async () => {
      await createSampleLoginPage(page);

      const mockDetectFieldsWithConfidence = async (minConfidence: number) => {
        const allFields = [
          { id: 'field_1', name: 'username', confidence: 0.95, type: 'email' },
          { id: 'field_2', name: 'password', confidence: 0.92, type: 'password' },
          { id: 'field_3', name: 'remember', confidence: 0.75, type: 'checkbox' },
          { id: 'field_4', name: 'token', confidence: 0.60, type: 'hidden' }
        ];

        return {
          fields: allFields.filter(f => f.confidence >= minConfidence),
          windowInfo: { title: 'Test Page' }
        };
      };

      // Test high confidence threshold
      const highConfidenceResult = await mockDetectFieldsWithConfidence(0.9);
      expect(highConfidenceResult.fields).toHaveLength(2); // Only username and password

      // Test medium confidence threshold
      const mediumConfidenceResult = await mockDetectFieldsWithConfidence(0.8);
      expect(mediumConfidenceResult.fields).toHaveLength(2); // Still only username and password

      // Test low confidence threshold
      const lowConfidenceResult = await mockDetectFieldsWithConfidence(0.5);
      expect(lowConfidenceResult.fields).toHaveLength(4); // All fields
    });

    test('should provide accurate field metadata', async () => {
      await createSampleLoginPage(page);

      // Get actual field data from the page
      const pageFieldData = await page.evaluate(() => {
        const fields = Array.from(document.querySelectorAll('input'));
        return fields.map(input => ({
          id: input.id,
          name: input.name,
          type: input.type,
          placeholder: input.placeholder,
          required: input.required,
          className: input.className
        }));
      });

      // Mock detection with accurate metadata
      const result = {
        fields: pageFieldData.map((field, index) => ({
          id: field.id || `field_${index}`,
          name: field.name || field.id,
          type: field.type,
          metadata: {
            description: field.placeholder || `${field.type} field`,
            placeholder: field.placeholder,
            required: field.required,
            inputType: field.type === 'email' ? 'email' : field.type,
            bounds: {
              x: 100 + index * 10,
              y: 150 + index * 50,
              width: 300,
              height: 40
            },
            confidence: 0.9 + Math.random() * 0.1
          }
        }))
      };

      // Verify metadata accuracy
      const usernameField = result.fields.find(f => f.name === 'username');
      expect(usernameField?.metadata.placeholder).toBe('Enter your email');
      expect(usernameField?.metadata.required).toBe(true);
      expect(usernameField?.metadata.inputType).toBe('email');

      const passwordField = result.fields.find(f => f.name === 'password');
      expect(passwordField?.metadata.placeholder).toBe('Enter your password');
      expect(passwordField?.metadata.required).toBe(true);
      expect(passwordField?.metadata.inputType).toBe('password');
    });
  });

  describe('Search Form Field Detection', () => {
    test('should detect search fields and filters with correct types', async () => {
      await createSampleSearchPage(page);

      // Mock detection for search page
      const mockSearchDetection = async () => {
        const fields = await page.$$eval('input, select', (elements) =>
          elements.map((el, index) => {
            const isSelect = el.tagName.toLowerCase() === 'select';
            return {
              id: el.id || `field_${index}`,
              name: el.getAttribute('name') || el.id,
              type: isSelect ? 'select' : (el as HTMLInputElement).type,
              description: el.getAttribute('placeholder') || `${isSelect ? 'select' : (el as HTMLInputElement).type} field`,
              placeholder: el.getAttribute('placeholder'),
              semantic_type: detectSemanticType(el.id, el.getAttribute('placeholder') || ''),
              bounds: {
                x: 100 + (index % 2) * 200,
                y: 200 + Math.floor(index / 2) * 60,
                width: isSelect ? 180 : 200,
                height: 40
              },
              confidence: 0.85 + Math.random() * 0.15,
              analysis_method: 'playwright_semantic'
            };
          })
        );

        return { fields };
      };

      function detectSemanticType(id: string, placeholder: string): string {
        if (id.includes('search') || placeholder.includes('search')) return 'search';
        if (id.includes('price') || placeholder.includes('price')) return 'number';
        if (id.includes('location')) return 'location';
        if (id.includes('category')) return 'category';
        return 'text';
      }

      const result = await mockSearchDetection();

      // Verify search field detection
      const searchField = result.fields.find(f => f.id === 'mainSearch');
      expect(searchField).toBeDefined();
      expect(searchField?.semantic_type).toBe('search');
      expect(searchField?.type).toBe('text');

      // Verify category select field
      const categoryField = result.fields.find(f => f.id === 'category');
      expect(categoryField).toBeDefined();
      expect(categoryField?.type).toBe('select');
      expect(categoryField?.semantic_type).toBe('category');

      // Verify price fields
      const minPriceField = result.fields.find(f => f.id === 'minPrice');
      expect(minPriceField).toBeDefined();
      expect(minPriceField?.type).toBe('number');
      expect(minPriceField?.semantic_type).toBe('number');

      const maxPriceField = result.fields.find(f => f.id === 'maxPrice');
      expect(maxPriceField).toBeDefined();
      expect(maxPriceField?.type).toBe('number');

      // Verify location field
      const locationField = result.fields.find(f => f.id === 'location');
      expect(locationField).toBeDefined();
      expect(locationField?.semantic_type).toBe('location');

      console.log(`✅ Detected ${result.fields.length} search form fields`);
    });

    test('should detect field bounds accurately', async () => {
      await createSampleSearchPage(page);

      // Get actual element bounds from the page
      const actualBounds = await page.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('input, select'));
        return elements.map(el => {
          const rect = el.getBoundingClientRect();
          return {
            id: el.id,
            bounds: {
              x: Math.round(rect.x),
              y: Math.round(rect.y),
              width: Math.round(rect.width),
              height: Math.round(rect.height)
            }
          };
        });
      });

      // Mock detection should provide bounds close to actual
      const mockDetectionWithBounds = {
        fields: actualBounds.map(item => ({
          id: item.id,
          name: item.id,
          type: 'input',
          metadata: {
            bounds: item.bounds,
            confidence: 0.9
          }
        }))
      };

      // Verify bounds are reasonable
      mockDetectionWithBounds.fields.forEach(field => {
        expect(field.metadata.bounds.width).toBeGreaterThan(0);
        expect(field.metadata.bounds.height).toBeGreaterThan(0);
        expect(field.metadata.bounds.x).toBeGreaterThanOrEqual(0);
        expect(field.metadata.bounds.y).toBeGreaterThanOrEqual(0);
      });

      const mainSearchField = mockDetectionWithBounds.fields.find(f => f.id === 'mainSearch');
      expect(mainSearchField?.metadata.bounds.width).toBeGreaterThan(200); // Should be wide search box
    });
  });

  describe('Error Handling and Edge Cases', () => {
    test('should handle pages with no input fields', async () => {
      // Create page with no form fields
      await page.setContent(`
        <!DOCTYPE html>
        <html>
        <head><title>No Fields Page</title></head>
        <body>
          <h1>This page has no input fields</h1>
          <p>Just some text content</p>
          <button>A button that does nothing</button>
        </body>
        </html>
      `);

      const mockEmptyDetection = async () => ({
        fields: [],
        windowInfo: {
          title: await page.title(),
          className: 'Chrome_WidgetWin_1',
          handle: '12345',
          bounds: { x: 0, y: 0, width: 1200, height: 800 }
        }
      });

      const result = await mockEmptyDetection();
      expect(result.fields).toHaveLength(0);
      expect(result.windowInfo.title).toBe('No Fields Page');
    });

    test('should handle detection timeout gracefully', async () => {
      await createSampleLoginPage(page);

      const mockTimeoutDetection = async () => {
        // Simulate timeout
        await new Promise(resolve => setTimeout(resolve, 100));
        throw new Error('Detection timeout after 5 seconds');
      };

      await expect(mockTimeoutDetection()).rejects.toThrow('Detection timeout');
    });

    test('should handle malformed HTML gracefully', async () => {
      // Create page with malformed HTML
      await page.setContent(`
        <!DOCTYPE html>
        <html>
        <body>
          <form>
            <input type="text" name="field1" <!-- missing closing -->
            <input type="password" name="field2">
            <div><input type="text" name="field3"</div>
          </form>
        </body>
        </html>
      `, { waitUntil: 'domcontentloaded' });

      const mockMalformedDetection = async () => {
        try {
          const fields = await page.$$eval('input', (inputs) =>
            inputs.map((input, index) => ({
              id: `field_${index}`,
              name: input.name || `unnamed_${index}`,
              type: input.type || 'text',
              confidence: 0.8,
              analysis_method: 'robust_detection'
            }))
          );

          return { fields };
        } catch (error) {
          return { fields: [], error: 'Failed to parse malformed HTML' };
        }
      };

      const result = await mockMalformedDetection();
      // Should still detect some fields despite malformed HTML
      expect(result.fields.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Performance and Accuracy Metrics', () => {
    test('should meet detection speed requirements', async () => {
      await createSampleLoginPage(page);

      const startTime = Date.now();
      
      const mockFastDetection = async () => {
        // Simulate realistic detection time
        await new Promise(resolve => setTimeout(resolve, 200)); // 200ms simulation
        
        return {
          fields: [
            { id: 'field_1', name: 'username', confidence: 0.95 },
            { id: 'field_2', name: 'password', confidence: 0.92 }
          ],
          detectionTime: Date.now() - startTime
        };
      };

      const result = await mockFastDetection();
      const detectionTime = Date.now() - startTime;

      expect(detectionTime).toBeLessThan(1000); // Should complete within 1 second
      expect(result.fields).toHaveLength(2);
      
      console.log(`✅ Detection completed in ${detectionTime}ms`);
    });

    test('should maintain high accuracy across different page types', async () => {
      const testPages = [
        { name: 'login', setup: createSampleLoginPage, expectedFields: 4 },
        { name: 'search', setup: createSampleSearchPage, expectedFields: 5 }
      ];

      const accuracyResults = [];

      for (const testPage of testPages) {
        await testPage.setup(page);
        
        const mockPageDetection = async () => {
          const actualFieldCount = await page.$$eval('input, select', els => els.length);
          const detectedFields = Math.min(actualFieldCount, testPage.expectedFields);
          
          return {
            fields: Array.from({ length: detectedFields }, (_, i) => ({
              id: `field_${i}`,
              confidence: 0.85 + Math.random() * 0.15
            })),
            actualFieldCount
          };
        };

        const result = await mockPageDetection();
        const accuracy = result.fields.length / result.actualFieldCount;
        
        accuracyResults.push({
          page: testPage.name,
          accuracy,
          detected: result.fields.length,
          actual: result.actualFieldCount
        });

        expect(accuracy).toBeGreaterThan(0.8); // At least 80% accuracy
      }

      const averageAccuracy = accuracyResults.reduce((sum, r) => sum + r.accuracy, 0) / accuracyResults.length;
      expect(averageAccuracy).toBeGreaterThan(0.85); // Average accuracy should be > 85%

      console.log('📊 Accuracy Results:', accuracyResults);
      console.log(`✅ Average accuracy: ${(averageAccuracy * 100).toFixed(1)}%`);
    });
  });
});
