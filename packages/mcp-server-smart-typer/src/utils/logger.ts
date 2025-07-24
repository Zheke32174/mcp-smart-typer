/**
 * Enhanced logging utility for the MCP server with security features
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class Logger {
  private level: LogLevel;
  private enableSecureMasking: boolean;

  constructor() {
    this.level = (process.env.LOG_LEVEL as LogLevel) || 'info';
    this.enableSecureMasking = process.env.SECURE_LOGGING === 'true';
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.level);
  }

  private formatMessage(level: LogLevel, message: string, ...args: any[]): string {
    const timestamp = new Date().toISOString();
    
    let formattedArgs = '';
    if (args.length > 0) {
      const processedArgs = this.enableSecureMasking 
        ? args.map(arg => this.maskSensitiveData(arg))
        : args;
      
      formattedArgs = ' ' + processedArgs.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ');
    }
    
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${formattedArgs}`;
  }

  private maskSensitiveData(data: any): any {
    if (!this.enableSecureMasking) {
      return data;
    }

    if (typeof data === 'string') {
      return this.maskSensitiveString(data);
    }

    if (typeof data === 'object' && data !== null) {
      const masked = Array.isArray(data) ? [] : {};
      
      for (const [key, value] of Object.entries(data)) {
        const isSensitiveKey = this.isSensitiveKey(key);
        
        if (isSensitiveKey && typeof value === 'string') {
          (masked as any)[key] = this.maskString(value);
        } else if (typeof value === 'object') {
          (masked as any)[key] = this.maskSensitiveData(value);
        } else {
          (masked as any)[key] = value;
        }
      }
      
      return masked;
    }

    return data;
  }

  private isSensitiveKey(key: string): boolean {
    const sensitiveKeywords = [
      'password', 'passwd', 'pwd', 'pass', 'secret', 'key', 'token', 'auth',
      'credential', 'pin', 'code', 'otp', '2fa', 'mfa', 'bearer', 'jwt',
      'api_key', 'apikey', 'access_token', 'refresh_token', 'session_id', 'text'
    ];
    
    const lowerKey = key.toLowerCase();
    return sensitiveKeywords.some(keyword => lowerKey.includes(keyword));
  }

  private maskSensitiveString(text: string): string {
    const sensitivePatterns = [
      /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, // Email
      /\b(?:\d{4}[-.]?){3}\d{4}\b/g, // Credit card
      /\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/g, // SSN
    ];

    let maskedText = text;
    for (const pattern of sensitivePatterns) {
      maskedText = maskedText.replace(pattern, (match) => this.maskString(match));
    }

    return maskedText;
  }

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

    return value.substring(0, 2) + '*'.repeat(value.length - 4) + value.substring(value.length - 2);
  }

  debug(message: string, ...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.debug(this.formatMessage('debug', message, ...args));
    }
  }

  info(message: string, ...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', message, ...args));
    }
  }

  warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message, ...args));
    }
  }

  error(message: string, ...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message, ...args));
    }
  }

  /**
   * Log with explicit security context
   */
  secureLog(level: LogLevel, message: string, data?: any, options?: { fieldId?: string; hasSensitiveData?: boolean }): void {
    if (!this.shouldLog(level)) {
      return;
    }

    const logData = { ...data };
    if (options?.hasSensitiveData) {
      logData._security = { containsSensitiveData: true, fieldId: options.fieldId };
    }

    this[level](message, logData);
  }

  /**
   * Enable or disable secure masking
   */
  setSecureMasking(enabled: boolean): void {
    this.enableSecureMasking = enabled;
  }

  /**
   * Get current logger configuration
   */
  getConfig(): { level: LogLevel; secureMasking: boolean } {
    return {
      level: this.level,
      secureMasking: this.enableSecureMasking
    };
  }
}

export const logger = new Logger();
