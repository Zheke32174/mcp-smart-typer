/**
 * Mock Native Client
 * Simulates native Windows UI automation for testing and development
 */

import { logger } from './logger.js';

export class MockNativeClient {
  private connected = false;
  private mockFields = [
    {
      id: 'field_username_001',
      name: 'username',
      type: 'input',
      description: 'Username input field',
      placeholder: 'Enter your username',
      inputType: 'text',
      required: true,
      bounds: { x: 100, y: 200, width: 200, height: 30 },
      confidence: 0.95,
      value: '',
    },
    {
      id: 'field_password_002',
      name: 'password',
      type: 'input',
      description: 'Password input field',
      placeholder: 'Enter your password',
      inputType: 'password',
      required: true,
      bounds: { x: 100, y: 250, width: 200, height: 30 },
      confidence: 0.92,
      value: '',
    },
    {
      id: 'field_email_003',
      name: 'email',
      type: 'input',
      description: 'Email input field',
      placeholder: 'user@example.com',
      inputType: 'email',
      required: false,
      bounds: { x: 100, y: 300, width: 200, height: 30 },
      confidence: 0.88,
      value: '',
    },
  ];

  async connect(): Promise<void> {
    logger.info('Connecting to mock native client...');
    // Simulate connection delay
    await new Promise(resolve => setTimeout(resolve, 500));
    this.connected = true;
    logger.info('Mock native client connected');
  }

  async disconnect(): Promise<void> {
    logger.info('Disconnecting mock native client...');
    this.connected = false;
    logger.info('Mock native client disconnected');
  }

  isReady(): boolean {
    return this.connected;
  }

  async detectFields(params: {
    contextHint: string;
    windowTitle?: string;
    includeHidden?: boolean;
    confidence?: number;
  }): Promise<any> {
    logger.info('Mock: Detecting fields', params);

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 200));

    // Filter fields based on confidence threshold
    const filteredFields = this.mockFields.filter(
      field => field.confidence >= (params.confidence || 0.8)
    );

    return {
      success: true,
      fields: filteredFields.map(field => ({
        id: field.id,
        name: field.name,
        type: field.type,
        description: field.description,
        placeholder: field.placeholder,
        inputType: field.inputType,
        required: field.required,
        bounds: field.bounds,
        confidence: field.confidence,
      })),
      windowInfo: {
        title: params.windowTitle || 'Mock Application - Login',
        className: 'Chrome_WidgetWin_1',
        handle: '0x001234AB',
        bounds: { x: 0, y: 0, width: 1920, height: 1080 },
      },
    };
  }

  async typeText(params: {
    fieldId: string;
    text: string;
    delay?: number;
    clearFirst?: boolean;
    pressEnter?: boolean;
  }): Promise<any> {
    logger.info('Mock: Typing text', {
      fieldId: params.fieldId,
      textLength: params.text.length,
      delay: params.delay,
    });

    // Find the field
    const field = this.mockFields.find(f => f.id === params.fieldId);
    if (!field) {
      return {
        success: false,
        errorCode: 'FIELD_NOT_FOUND',
        errorMessage: `Field with ID ${params.fieldId} not found`,
      };
    }

    // Simulate typing delay
    const typingTime = params.text.length * (params.delay || 50);
    await new Promise(resolve => setTimeout(resolve, Math.min(typingTime, 2000)));

    // Update field value
    if (params.clearFirst) {
      field.value = params.text;
    } else {
      field.value += params.text;
    }

    return {
      success: true,
      charactersTyped: params.text.length,
      fieldValue: field.value,
    };
  }

  async getFieldValue(params: { fieldId: string; maxLength?: number }): Promise<any> {
    logger.info('Mock: Getting field value', { fieldId: params.fieldId });

    // Find the field
    const field = this.mockFields.find(f => f.id === params.fieldId);
    if (!field) {
      return {
        success: false,
        errorCode: 'FIELD_NOT_FOUND',
        errorMessage: `Field with ID ${params.fieldId} not found`,
      };
    }

    // Simulate retrieval delay
    await new Promise(resolve => setTimeout(resolve, 100));

    let value = field.value;
    if (params.maxLength && value.length > params.maxLength) {
      value = value.substring(0, params.maxLength);
    }

    return {
      success: true,
      value,
      fieldInfo: {
        id: field.id,
        name: field.name,
        type: field.type,
        metadata: {
          description: field.description,
          placeholder: field.placeholder,
          inputType: field.inputType,
          required: field.required,
          bounds: field.bounds,
          confidence: field.confidence,
        },
      },
    };
  }

  async focusField(params: {
    fieldId: string;
    bringToFront?: boolean;
    scrollIntoView?: boolean;
  }): Promise<any> {
    logger.info('Mock: Focusing field', params);

    // Find the field
    const field = this.mockFields.find(f => f.id === params.fieldId);
    if (!field) {
      return {
        success: false,
        errorCode: 'FIELD_NOT_FOUND',
        errorMessage: `Field with ID ${params.fieldId} not found`,
      };
    }

    // Simulate focus delay
    await new Promise(resolve => setTimeout(resolve, 150));

    return {
      success: true,
      previousFocus: 'field_previous_001',
      windowBroughtToFront: params.bringToFront || false,
    };
  }

  async clearField(params: {
    fieldId: string;
    method?: 'selectAll' | 'backspace' | 'delete';
  }): Promise<any> {
    logger.info('Mock: Clearing field', params);

    // Find the field
    const field = this.mockFields.find(f => f.id === params.fieldId);
    if (!field) {
      return {
        success: false,
        errorCode: 'FIELD_NOT_FOUND',
        errorMessage: `Field with ID ${params.fieldId} not found`,
      };
    }

    // Simulate clear delay
    await new Promise(resolve => setTimeout(resolve, 100));

    const previousValue = field.value;
    field.value = '';

    return {
      success: true,
      previousValue: field.inputType === 'password' ? '[REDACTED]' : previousValue,
    };
  }

  async getWindowInfo(
    params: {
      windowTitle?: string;
    } = {}
  ): Promise<any> {
    logger.info('Mock: Getting window info', params);

    // Simulate window detection delay
    await new Promise(resolve => setTimeout(resolve, 200));

    return {
      success: true,
      windows: [
        {
          title: 'Mock Application - Login',
          className: 'Chrome_WidgetWin_1',
          handle: '0x001234AB',
          pid: 12345,
          isActive: true,
          bounds: { x: 0, y: 0, width: 1920, height: 1080 },
        },
        {
          title: 'Notepad',
          className: 'Notepad',
          handle: '0x005678CD',
          pid: 67890,
          isActive: false,
          bounds: { x: 100, y: 100, width: 800, height: 600 },
        },
      ],
      activeWindow: '0x001234AB',
    };
  }

  async takeScreenshot(
    params: {
      region?: { x: number; y: number; width: number; height: number };
      format?: 'png' | 'jpeg';
      quality?: number;
    } = {}
  ): Promise<any> {
    logger.info('Mock: Taking screenshot', params);

    // Simulate screenshot delay
    await new Promise(resolve => setTimeout(resolve, 300));

    // Generate mock base64 image data (1x1 transparent PNG)
    const mockImageData =
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI/hL+bHwAAAABJRU5ErkJggg==';

    return {
      success: true,
      imageData: mockImageData,
      imageSize: {
        width: params.region?.width || 1920,
        height: params.region?.height || 1080,
      },
      filePath: `/tmp/screenshot_${Date.now()}.${params.format || 'png'}`,
    };
  }
}
