/**
 * Type definitions for MCP Smart Typer server
 */

// Window information
export interface WindowInfo {
  title: string;
  className: string;
  pid: number;
  handle: string;
  bounds: WindowBounds;
  isActive: boolean;
}

export interface WindowBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

// Element information
export interface ElementInfo {
  id?: string;
  name?: string;
  className?: string;
  bounds: ElementBounds;
  isVisible: boolean;
  isEnabled: boolean;
  text?: string;
  elementType: string;
}

export interface ElementBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

// Tool parameters
export interface TypeTextParams {
  text: string;
  delay?: number;
}

export interface SendKeysParams {
  keys: string;
  modifiers?: string[];
}

export interface FindElementParams {
  selector: string;
  method: 'text' | 'class' | 'name' | 'id';
  timeout?: number;
}

export interface ClickElementParams {
  x: number;
  y: number;
  button?: 'left' | 'right' | 'middle';
  doubleClick?: boolean;
}

// gRPC request/response types (matching protobuf definitions)
export interface TypeTextRequest {
  text: string;
  delay?: number;
}

export interface TypeTextResponse {
  success: boolean;
  message?: string;
}

export interface SendKeysRequest {
  keys: string;
  modifiers?: string[];
}

export interface SendKeysResponse {
  success: boolean;
  message?: string;
}

export interface GetActiveWindowRequest {
  // Empty for now, might add parameters later
}

export interface GetActiveWindowResponse {
  success: boolean;
  window?: WindowInfo;
  message?: string;
}

export interface FindElementRequest {
  selector: string;
  method: string;
  timeout?: number;
}

export interface FindElementResponse {
  success: boolean;
  element?: ElementInfo;
  message?: string;
}

export interface ClickElementRequest {
  x: number;
  y: number;
  button?: string;
  doubleClick?: boolean;
}

export interface ClickElementResponse {
  success: boolean;
  message?: string;
}

// Configuration
export interface ServerConfig {
  grpcPort: number;
  grpcHost: string;
  timeout: number;
}

// Error types
export class SmartTyperError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'SmartTyperError';
  }
}

export class GrpcConnectionError extends SmartTyperError {
  constructor(message: string, originalError?: Error) {
    super(message, 'GRPC_CONNECTION_ERROR', originalError);
    this.name = 'GrpcConnectionError';
  }
}

export class UIAutomationError extends SmartTyperError {
  constructor(message: string, originalError?: Error) {
    super(message, 'UI_AUTOMATION_ERROR', originalError);
    this.name = 'UIAutomationError';
  }
}
