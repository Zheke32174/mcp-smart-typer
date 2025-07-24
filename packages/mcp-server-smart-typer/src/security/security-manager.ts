/**
 * Security Manager
 * Handles detection and masking of sensitive values in logs and data
 */

import { logger } from '../utils/logger.js';

export interface SensitiveField {
  fieldId: string;
  fieldType: 'password' | 'email' | 'phone' | 'ssn' | 'credit_card' | 'api_key' | 'token' | 'generic';
  confidence: number;
}

export class SecurityManager {
  private sensitivePatterns: Map<string, RegExp>;
  private passwordFieldPatterns: RegExp[];
  private sensitiveKeywords: string[];

  constructor() {
    this.initializePatterns();
    logger.info('Security Manager initialized');
  }

  private initializePatterns(): void {
    // Patterns for detecting sensitive data types
    this.sensitivePatterns = new Map([
      ['password', /(?:password|passwd|pwd|pass|secret|key|token|auth|credential)/i],
      ['email', /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g],
      ['phone', /(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}/g],
      ['ssn', /\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/g],
      ['credit_card', /\b(?:\d{4}[-.\s]?){3}\d{4}\b/g],
      ['api_key', /(?:api[_-]?key|apikey|access[_-]?token|bearer[_-]?token)/i],
      ['token', /(?:jwt|bearer|token)[_-]?[a-zA-Z0-9+/=]{20,}/i]
    ]);

    // Patterns for detecting password fields by name/id/class
    this.passwordFieldPatterns = [
      /password/i,
      /passwd/i,
      /pwd/i,
      /pass/i,
      /secret/i,
      /auth/i,
      /credential/i,
      /token/i,
      /key/i,
      /pin/i,
      /code/i,
      /otp/i,
      /2fa/i,
      /mfa/i
    ];

    // Keywords that indicate sensitive content
    this.sensitiveKeywords = [
      'password', 'passwd', 'pwd', 'pass', 'secret', 'key', 'token', 'auth',
      'credential', 'pin', 'code', 'otp', '2fa', 'mfa', 'bearer', 'jwt',
      'api_key', 'apikey', 'access_token', 'refresh_token', 'session_id'
    ];
  }

  /**
   * Detect if a field is likely to contain sensitive information
   */
  detectSensitiveField(fieldId: string, fieldName?: string, fieldType?: string, fieldClass?: string): SensitiveField | null {
    const identifiers = [fieldId, fieldName, fieldType, fieldClass].filter(Boolean).join(' ').toLowerCase();
    
    for (const [type, pattern] of this.sensitivePatterns) {
      if (pattern.test(identifiers)) {
        const confidence = this.calculateConfidence(identifiers, type);
        
        logger.debug('Sensitive field detected', {
          fieldId,
          detectedType: type,
          confidence,
          identifiers: identifiers.substring(0, 100) // Limit log output
        });

        return {
          fieldId,
          fieldType: type as any,
          confidence
        };
      }
    }

    return null;
  }

  /**
   * Check if a field is a password field
   */
  isPasswordField(fieldId: string, fieldName?: string, fieldType?: string, fieldClass?: string): boolean {
    const identifiers = [fieldId, fieldName, fieldType, fieldClass].filter(Boolean).join(' ').toLowerCase();
    
    // Check for explicit password type
    if (fieldType?.toLowerCase() === 'password') {
      return true;
    }

    // Check against password patterns
    return this.passwordFieldPatterns.some(pattern => pattern.test(identifiers));
  }

  /**
   * Mask sensitive values in text or objects
   */
  maskSensitiveData(data: any, fieldContext?: { fieldId?: string; fieldType?: string }): any {
    if (typeof data === 'string') {
      return this.maskSensitiveString(data, fieldContext);
    }

    if (typeof data === 'object' && data !== null) {
      const masked = Array.isArray(data) ? [] : {};
      
      for (const [key, value] of Object.entries(data)) {
        const isSensitiveKey = this.isSensitiveKey(key);
        
        if (isSensitiveKey && typeof value === 'string') {
          (masked as any)[key] = this.maskString(value);
        } else if (typeof value === 'object') {
          (masked as any)[key] = this.maskSensitiveData(value, fieldContext);
        } else {
          (masked as any)[key] = value;
        }
      }
      
      return masked;
    }

    return data;
  }

  /**
   * Mask sensitive strings based on patterns
   */
  private maskSensitiveString(text: string, fieldContext?: { fieldId?: string; fieldType?: string }): string {
    let maskedText = text;

    // If we know the field context and it's sensitive, mask the entire value
    if (fieldContext?.fieldId && this.isPasswordField(fieldContext.fieldId, '', fieldContext.fieldType)) {
      return this.maskString(text);
    }

    // Apply pattern-based masking
    for (const [type, pattern] of this.sensitivePatterns) {
      if (type === 'password') continue; // Skip password pattern for string content
      
      maskedText = maskedText.replace(pattern, (match) => this.maskString(match));
    }

    return maskedText;
  }

  /**
   * Check if a key name indicates sensitive data
   */
  private isSensitiveKey(key: string): boolean {
    const lowerKey = key.toLowerCase();
    return this.sensitiveKeywords.some(keyword => lowerKey.includes(keyword));
  }

  /**
   * Calculate confidence score for sensitive field detection
   */
  private calculateConfidence(identifiers: string, type: string): number {
    const exactMatches = {
      'password': ['password', 'passwd', 'pwd'],
      'email': ['email', 'mail'],
      'phone': ['phone', 'tel', 'mobile'],
      'api_key': ['apikey', 'api_key', 'key'],
      'token': ['token', 'bearer', 'jwt']
    };

    const exact = exactMatches[type as keyof typeof exactMatches] || [];
    
    // High confidence for exact matches
    if (exact.some(match => identifiers.includes(match))) {
      return 0.95;
    }

    // Medium confidence for pattern matches
    return 0.7;
  }

  /**
   * Mask a string value
   */
  private maskString(value: string): string {
    if (!value || typeof value !== 'string') {
      return value;
    }

    if (value.length <= 2) {
      return '*'.repeat(value.length);
    }

    if (value.length <= 8) {
      return value[0] + '*'.repeat(value.length - 2) + value[value.length - 1];
    }

    // For longer strings, show first 2 and last 2 characters
    return value.substring(0, 2) + '*'.repeat(value.length - 4) + value.substring(value.length - 2);
  }

  /**
   * Create a secure log entry with masked sensitive data
   */
  createSecureLogEntry(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: any): {
    message: string;
    data: any;
    hasSensitiveData: boolean;
  } {
    let hasSensitiveData = false;
    let maskedData = data;

    if (data) {
      const originalData = JSON.stringify(data);
      maskedData = this.maskSensitiveData(data);
      const maskedDataString = JSON.stringify(maskedData);
      
      hasSensitiveData = originalData !== maskedDataString;
    }

    return {
      message,
      data: maskedData,
      hasSensitiveData
    };
  }

  /**
   * Validate security flags for operation
   */
  validateSecurityFlags(securityFlags?: string[]): {
    isValid: boolean;
    warnings: string[];
  } {
    const warnings: string[] = [];
    
    if (!securityFlags || securityFlags.length === 0) {
      warnings.push('No security flags provided');
      return { isValid: true, warnings };
    }

    const validFlags = ['encrypted', 'sensitive', 'audit', 'restricted', 'public'];
    const invalidFlags = securityFlags.filter(flag => !validFlags.includes(flag));
    
    if (invalidFlags.length > 0) {
      warnings.push(`Invalid security flags: ${invalidFlags.join(', ')}`);
    }

    // Check for conflicting flags
    if (securityFlags.includes('sensitive') && securityFlags.includes('public')) {
      warnings.push('Conflicting security flags: sensitive and public');
    }

    return {
      isValid: invalidFlags.length === 0,
      warnings
    };
  }
}

export const securityManager = new SecurityManager();
