/**
 * End-to-End Tests for Typing Accuracy
 * Tests the precision and accuracy of text typing functionality
 */

import { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } from '@jest/globals';
import { Browser, Page, chromium } from 'playwright';
import { 
  createTestPage, 
  createSampleLoginPage, 
  createSampleSearchPage,
  takeDebugScreenshot,
  waitFor
} from '../test-utils.js';

describe('Typing Accuracy E2E Tests', () => {
  let browser: Browser;
  let page: Page;

  beforeAll(async () => {
    console.log('⌨️  Starting typing accuracy E2E tests...');
    browser = await chromium.launch({ headless: true });
  });

  beforeEach(async () => {
    page = await createTestPage(browser);
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
    console.log('✅ Typing accuracy E2E tests completed');
  });

  describe('Basic Text Input Accuracy', () => {
    test('should type simple text accurately', async () => {
      await createSampleLoginPage(page);
      
      const testText = 'test@example.com';
      const usernameField = '#username';
      
      // Clear field and type text
      await page.click(usernameField);
      await page.fill('', ''); // Clear
      await page.type(usernameField, testText, { delay: 50 });
      
      // Verify typed text
      const actualValue = await page.inputValue(usernameField);
      expect(actualValue).toBe(testText);
      
      console.log(`✅ Typed "${testText}" accurately`);
    });

    test('should handle special characters correctly', async () => {
      await createSampleLoginPage(page);
      
      const specialText = 'p@$$w0rd!#$%^&*()_+{}[]';
      const passwordField = '#password';
      
      await page.click(passwordField);
      await page.type(passwordField, specialText, { delay: 30 });
      
      const actualValue = await page.inputValue(passwordField);
      expect(actualValue).toBe(specialText);
      
      console.log(`✅ Special characters typed accurately: ${specialText.length} chars`);
    });

    test('should handle unicode and international characters', async () => {
      await createSampleLoginPage(page);
      
      const unicodeTexts = [
        'Café', // French
        'naïve', // Diacritics
        'Москва', // Cyrillic
        '北京', // Chinese
        'こんにちは', // Japanese
        '🚀🎉✨', // Emojis
        'Ñoño' // Spanish
      ];
      
      for (const unicodeText of unicodeTexts) {
        await page.click('#username');
        await page.fill('#username', ''); // Clear
        await page.type('#username', unicodeText, { delay: 40 });
        
        const actualValue = await page.inputValue('#username');
        expect(actualValue).toBe(unicodeText);
      }
      
      console.log(`✅ Unicode characters typed accurately: ${unicodeTexts.length} test cases`);
    });

    test('should maintain typing accuracy with different delays', async () => {
      await createSampleLoginPage(page);
      
      const testCases = [
        { text: 'fast typing test', delay: 10 },
        { text: 'medium speed test', delay: 50 },
        { text: 'slow typing test', delay: 100 }
      ];
      
      for (const testCase of testCases) {
        await page.click('#username');
        await page.fill('#username', '');
        
        const startTime = Date.now();
        await page.type('#username', testCase.text, { delay: testCase.delay });
        const actualTime = Date.now() - startTime;
        
        const actualValue = await page.inputValue('#username');
        const expectedMinTime = testCase.text.length * testCase.delay;
        
        expect(actualValue).toBe(testCase.text);
        expect(actualTime).toBeGreaterThanOrEqual(expectedMinTime * 0.8); // Allow 20% variance
        
        console.log(`✅ Typed "${testCase.text}" with ${testCase.delay}ms delay in ${actualTime}ms`);
      }
    });
  });

  describe('Field-Specific Typing Accuracy', () => {
    test('should handle email field validation correctly', async () => {
      await createSampleLoginPage(page);
      
      const emailTests = [
        'user@example.com',
        'firstname.lastname@domain.co.uk',
        'user+tag@example.org',
        'test.email-with-dash@example-domain.com'
      ];
      
      for (const email of emailTests) {
        await page.click('#username');
        await page.fill('#username', '');
        await page.type('#username', email, { delay: 30 });
        
        const actualValue = await page.inputValue('#username');
        expect(actualValue).toBe(email);
        
        // Check if field accepts the email (no validation errors)
        const fieldValidity = await page.evaluate((selector) => {
          const field = document.querySelector(selector) as HTMLInputElement;
          return field ? field.validity.valid : false;
        }, '#username');
        
        expect(fieldValidity).toBe(true);
      }
      
      console.log(`✅ Email typing accuracy verified for ${emailTests.length} test cases`);
    });

    test('should handle password field securely', async () => {
      await createSampleLoginPage(page);
      
      const passwordTests = [
        'simplepass',
        'Complex123!',
        'V3ry$tr0ng&P@ssw0rd',
        '1234567890!@#$%^&*()'
      ];
      
      for (const password of passwordTests) {
        await page.click('#password');
        await page.fill('#password', '');
        await page.type('#password', password, { delay: 40 });
        
        const actualValue = await page.inputValue('#password');
        expect(actualValue).toBe(password);
        
        // Verify password field is masked in DOM
        const fieldType = await page.getAttribute('#password', 'type');
        expect(fieldType).toBe('password');
      }
      
      console.log(`✅ Password typing accuracy verified for ${passwordTests.length} test cases`);
    });

    test('should handle number fields with correct formatting', async () => {
      await createSampleSearchPage(page);
      
      const numberTests = [
        { input: '123', expected: '123' },
        { input: '0', expected: '0' },
        { input: '999999', expected: '999999' },
        { input: '1.50', expected: '1.50' }, // Decimal
        { input: '1000.99', expected: '1000.99' } // Large decimal
      ];
      
      for (const test of numberTests) {
        await page.click('#minPrice');
        await page.fill('#minPrice', '');
        await page.type('#minPrice', test.input, { delay: 30 });
        
        const actualValue = await page.inputValue('#minPrice');
        expect(actualValue).toBe(test.expected);
        
        // Verify numeric validity
        const isValid = await page.evaluate((selector) => {
          const field = document.querySelector(selector) as HTMLInputElement;
          return field ? field.validity.valid : false;
        }, '#minPrice');
        
        expect(isValid).toBe(true);
      }
      
      console.log(`✅ Number field typing accuracy verified`);
    });
  });

  describe('Advanced Typing Scenarios', () => {
    test('should handle text replacement accurately', async () => {
      await createSampleLoginPage(page);
      
      // Type initial text
      await page.click('#username');
      await page.type('#username', 'initial.text@example.com', { delay: 20 });
      
      // Select all and replace
      await page.keyboard.press('Control+a');
      await page.type('#username', 'replaced@newdomain.com', { delay: 30 });
      
      const finalValue = await page.inputValue('#username');
      expect(finalValue).toBe('replaced@newdomain.com');
      
      console.log('✅ Text replacement accuracy verified');
    });

    test('should handle insertion at cursor position', async () => {
      await createSampleLoginPage(page);
      
      // Type initial text
      await page.click('#username');
      await page.type('#username', 'user@domain.com', { delay: 20 });
      
      // Position cursor and insert text
      await page.keyboard.press('Home'); // Go to beginning
      await page.keyboard.press('ArrowRight'); // Move right 1 position
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('ArrowRight'); // Position after "user"
      
      await page.type('#username', '.name', { delay: 30 });
      
      const finalValue = await page.inputValue('#username');
      expect(finalValue).toBe('user.name@domain.com');
      
      console.log('✅ Cursor insertion accuracy verified');
    });

    test('should handle backspace and delete operations', async () => {
      await createSampleLoginPage(page);
      
      // Type text with intentional mistakes
      await page.click('#username');
      await page.type('#username', 'userXXX@example.com', { delay: 20 });
      
      // Remove the XXX using backspace
      for (let i = 0; i < 12; i++) { // Move cursor to before @
        await page.keyboard.press('ArrowLeft');
      }
      
      // Delete the XXX
      for (let i = 0; i < 3; i++) {
        await page.keyboard.press('Delete');
      }
      
      const finalValue = await page.inputValue('#username');
      expect(finalValue).toBe('user@example.com');
      
      console.log('✅ Delete/backspace accuracy verified');
    });

    test('should maintain accuracy during rapid typing', async () => {
      await createSampleLoginPage(page);
      
      const rapidText = 'ThisIsARapidTypingTestWithNoDelaysBetweenKeystrokes';
      
      await page.click('#username');
      await page.type('#username', rapidText, { delay: 5 }); // Very fast typing
      
      const actualValue = await page.inputValue('#username');
      expect(actualValue).toBe(rapidText);
      expect(actualValue.length).toBe(rapidText.length);
      
      console.log(`✅ Rapid typing accuracy verified: ${rapidText.length} characters`);
    });
  });

  describe('Error Scenarios and Recovery', () => {
    test('should handle typing in disabled fields gracefully', async () => {
      // Create page with disabled field
      await page.setContent(`
        <!DOCTYPE html>
        <html>
        <body>
          <input type="text" id="disabled-field" disabled placeholder="This field is disabled">
          <input type="text" id="enabled-field" placeholder="This field is enabled">
        </body>
        </html>
      `);
      
      // Attempt to type in disabled field
      await page.click('#disabled-field').catch(() => {}); // May fail, that's expected
      await page.type('#disabled-field', 'test text', { delay: 20 }).catch(() => {});
      
      const disabledValue = await page.inputValue('#disabled-field');
      expect(disabledValue).toBe(''); // Should remain empty
      
      // Verify enabled field still works
      await page.click('#enabled-field');
      await page.type('#enabled-field', 'test text', { delay: 20 });
      const enabledValue = await page.inputValue('#enabled-field');
      expect(enabledValue).toBe('test text');
      
      console.log('✅ Disabled field handling verified');
    });

    test('should handle readonly fields correctly', async () => {
      await page.setContent(`
        <!DOCTYPE html>
        <html>
        <body>
          <input type="text" id="readonly-field" readonly value="readonly content">
          <input type="text" id="normal-field" placeholder="normal field">
        </body>
        </html>
      `);
      
      const initialValue = await page.inputValue('#readonly-field');
      
      // Attempt to type in readonly field
      await page.click('#readonly-field');
      await page.type('#readonly-field', 'should not appear', { delay: 20 });
      
      const finalValue = await page.inputValue('#readonly-field');
      expect(finalValue).toBe(initialValue); // Should remain unchanged
      
      console.log('✅ Readonly field handling verified');
    });

    test('should recover from typing errors', async () => {
      await createSampleLoginPage(page);
      
      // Simulate a scenario where the field loses focus during typing
      await page.click('#username');
      await page.type('#username', 'partial', { delay: 30 });
      
      // Simulate focus loss (click elsewhere)
      await page.click('body');
      
      // Resume typing in the same field
      await page.click('#username');
      await page.keyboard.press('End'); // Go to end of existing text
      await page.type('#username', '@example.com', { delay: 30 });
      
      const finalValue = await page.inputValue('#username');
      expect(finalValue).toBe('partial@example.com');
      
      console.log('✅ Typing error recovery verified');
    });
  });

  describe('Performance and Timing Accuracy', () => {
    test('should meet typing speed requirements', async () => {
      await createSampleLoginPage(page);
      
      const testText = 'performance.test@email.com';
      const expectedDelay = 25; // 25ms per character
      
      const startTime = Date.now();
      await page.click('#username');
      await page.type('#username', testText, { delay: expectedDelay });
      const actualTime = Date.now() - startTime;
      
      const expectedMinTime = testText.length * expectedDelay;
      const expectedMaxTime = expectedMinTime * 1.5; // Allow 50% overhead
      
      expect(actualTime).toBeGreaterThanOrEqual(expectedMinTime);
      expect(actualTime).toBeLessThan(expectedMaxTime);
      
      const actualValue = await page.inputValue('#username');
      expect(actualValue).toBe(testText);
      
      console.log(`✅ Performance test: ${testText.length} chars in ${actualTime}ms (expected: ${expectedMinTime}ms)`);
    });

    test('should maintain accuracy under load', async () => {
      await createSampleLoginPage(page);
      
      const testCases = Array.from({ length: 10 }, (_, i) => `testuser${i}@example.com`);
      const results = [];
      
      for (const testText of testCases) {
        const startTime = Date.now();
        
        await page.click('#username');
        await page.fill('#username', ''); // Clear previous
        await page.type('#username', testText, { delay: 15 });
        
        const actualValue = await page.inputValue('#username');
        const timeTaken = Date.now() - startTime;
        
        results.push({
          expected: testText,
          actual: actualValue,
          correct: actualValue === testText,
          time: timeTaken
        });
      }
      
      const accuracy = results.filter(r => r.correct).length / results.length;
      const averageTime = results.reduce((sum, r) => sum + r.time, 0) / results.length;
      
      expect(accuracy).toBe(1.0); // 100% accuracy expected
      expect(averageTime).toBeLessThan(1000); // Should complete within 1 second each
      
      console.log(`✅ Load test: ${accuracy * 100}% accuracy over ${results.length} iterations`);
      console.log(`📊 Average time per test: ${averageTime.toFixed(1)}ms`);
    });

    test('should handle concurrent typing scenarios', async () => {
      await createSampleSearchPage(page);
      
      // Test typing in multiple fields in sequence (simulating fast user interaction)
      const fieldTests = [
        { selector: '#mainSearch', text: 'search query' },
        { selector: '#minPrice', text: '100' },
        { selector: '#maxPrice', text: '500' },
        { selector: '#location', text: 'New York' }
      ];
      
      const startTime = Date.now();
      
      for (const test of fieldTests) {
        await page.click(test.selector);
        await page.type(test.selector, test.text, { delay: 10 }); // Fast typing
      }
      
      const totalTime = Date.now() - startTime;
      
      // Verify all fields have correct values
      for (const test of fieldTests) {
        const actualValue = await page.inputValue(test.selector);
        expect(actualValue).toBe(test.text);
      }
      
      console.log(`✅ Concurrent typing test completed in ${totalTime}ms`);
    });
  });
});
