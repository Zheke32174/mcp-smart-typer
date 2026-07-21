/**
 * Precision Interaction Engine for MCP Smart Typer
 * Provides pixel-perfect interaction capabilities with advanced timing,
 * gesture recognition, and multi-modal input support.
 */

import { EventEmitter } from 'events';

export interface InteractionPoint {
  x: number;
  y: number;
  pressure?: number;
  timestamp: number;
  confidence: number;
}

export interface InteractionPath {
  points: InteractionPoint[];
  duration: number;
  velocity: number;
  acceleration: number;
  smoothness: number;
}

export interface GestureDefinition {
  name: string;
  pattern: InteractionPoint[];
  tolerance: number;
  minConfidence: number;
  contextRequirements?: string[];
}

export interface InteractionResult {
  success: boolean;
  accuracy: number;
  timingPrecision: number;
  errorCode?: string;
  errorMessage?: string;
  metadata: {
    startTime: number;
    endTime: number;
    actualPath?: InteractionPoint[];
    expectedPath?: InteractionPoint[];
    deviation: number;
  };
}

export interface AdvancedClickOptions {
  button: 'left' | 'right' | 'middle' | 'x1' | 'x2';
  clickType: 'single' | 'double' | 'triple' | 'hold' | 'release';
  pressure?: number;
  duration?: number;
  preDelay?: number;
  postDelay?: number;
  acceleration?: number;
  deceleration?: number;
  bezierCurve?: boolean;
  humanLike?: boolean;
  verifyTarget?: boolean;
  fallbackStrategy?: 'retry' | 'alternative' | 'abort';
}

export interface DragOperationOptions {
  startPoint: InteractionPoint;
  endPoint: InteractionPoint;
  path: 'straight' | 'curved' | 'custom';
  customPath?: InteractionPoint[];
  speed: 'slow' | 'normal' | 'fast' | 'custom';
  customSpeed?: number;
  acceleration: 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'custom';
  smoothing: boolean;
  snapToGrid?: boolean;
  gridSize?: number;
  pausePoints?: InteractionPoint[];
  pauseDuration?: number;
}

export interface KeyboardInputOptions {
  text?: string;
  keys?: string[];
  modifiers?: ('ctrl' | 'alt' | 'shift' | 'win')[];
  timing: 'instant' | 'realistic' | 'custom';
  customTiming?: {
    keyDownDelay: number;
    keyUpDelay: number;
    betweenKeysDelay: number;
  };
  language?: string;
  inputMethod?: 'direct' | 'simulation' | 'clipboard';
  verification?: boolean;
  autocorrect?: boolean;
}

export interface TouchGestureOptions {
  gestureType: 'tap' | 'swipe' | 'pinch' | 'rotate' | 'long-press';
  fingers: number;
  startPoints: InteractionPoint[];
  endPoints?: InteractionPoint[];
  duration: number;
  pressure: number;
  friction?: number;
  inertia?: boolean;
}

export interface InteractionContext {
  screenResolution: { width: number; height: number };
  scalingFactor: number;
  activeWindow: string;
  cursorPosition: InteractionPoint;
  keyboardLayout: string;
  inputLanguage: string;
  accessibility: {
    highContrast: boolean;
    magnification: number;
    screenReader: boolean;
  };
}

export interface SafetyConstraints {
  allowedRegions: Array<{ x: number; y: number; width: number; height: number }>;
  forbiddenRegions: Array<{ x: number; y: number; width: number; height: number }>;
  maxClickRate: number;
  maxMovementSpeed: number;
  requireConfirmation: boolean;
  timeouts: {
    maxInteractionTime: number;
    maxIdleTime: number;
  };
}

export class PrecisionInteractionEngine extends EventEmitter {
  private context: InteractionContext;
  private safetyConstraints: SafetyConstraints;
  private gestureLibrary: Map<string, GestureDefinition> = new Map();
  private interactionHistory: InteractionResult[] = [];
  private calibrationData: Map<string, any> = new Map();
  private isCalibrated = false;
  private performanceMetrics = {
    accuracy: 0,
    averageLatency: 0,
    successRate: 0,
    totalInteractions: 0,
  };

  constructor(config: PrecisionInteractionConfig = {}) {
    super();

    this.context = {
      screenResolution: { width: 1920, height: 1080 },
      scalingFactor: 1.0,
      activeWindow: '',
      cursorPosition: { x: 0, y: 0, timestamp: Date.now(), confidence: 1.0 },
      keyboardLayout: 'QWERTY',
      inputLanguage: 'en-US',
      accessibility: {
        highContrast: false,
        magnification: 1.0,
        screenReader: false,
      },
      ...config.context,
    };

    this.safetyConstraints = {
      allowedRegions: [],
      forbiddenRegions: [],
      maxClickRate: 10, // clicks per second
      maxMovementSpeed: 5000, // pixels per second
      requireConfirmation: false,
      timeouts: {
        maxInteractionTime: 30000,
        maxIdleTime: 5000,
      },
      ...config.safetyConstraints,
    };

    this.initializeGestureLibrary();
    this.startPerformanceMonitoring();
  }

  private initializeGestureLibrary(): void {
    // Define common gestures
    const commonGestures: GestureDefinition[] = [
      {
        name: 'single-click',
        pattern: [{ x: 0, y: 0, timestamp: 0, confidence: 1.0 }],
        tolerance: 5,
        minConfidence: 0.8,
      },
      {
        name: 'double-click',
        pattern: [
          { x: 0, y: 0, timestamp: 0, confidence: 1.0 },
          { x: 0, y: 0, timestamp: 250, confidence: 1.0 },
        ],
        tolerance: 10,
        minConfidence: 0.8,
      },
      {
        name: 'right-click',
        pattern: [{ x: 0, y: 0, timestamp: 0, confidence: 1.0 }],
        tolerance: 5,
        minConfidence: 0.8,
      },
      {
        name: 'drag-horizontal',
        pattern: [
          { x: 0, y: 0, timestamp: 0, confidence: 1.0 },
          { x: 100, y: 0, timestamp: 500, confidence: 1.0 },
        ],
        tolerance: 15,
        minConfidence: 0.7,
      },
    ];

    commonGestures.forEach(gesture => {
      this.gestureLibrary.set(gesture.name, gesture);
    });
  }

  private startPerformanceMonitoring(): void {
    setInterval(() => {
      this.updatePerformanceMetrics();
      this.emit('performance-update', this.performanceMetrics);
    }, 10000); // Update every 10 seconds
  }

  async initialize(): Promise<void> {
    console.log('🎯 Initializing Precision Interaction Engine...');

    try {
      // Update screen context
      await this.updateScreenContext();

      // Perform calibration
      await this.performCalibration();

      console.log('✅ Precision Interaction Engine initialized');
      this.emit('initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Precision Interaction Engine:', error);
      throw error;
    }
  }

  private async updateScreenContext(): Promise<void> {
    // Update screen resolution and other context information
    // This would integrate with the system APIs
    console.log('📊 Updating screen context...');

    // Placeholder implementation
    this.context.cursorPosition = {
      x: 0,
      y: 0,
      timestamp: Date.now(),
      confidence: 1.0,
    };
  }

  private async performCalibration(): Promise<void> {
    console.log('🎲 Performing interaction calibration...');

    const calibrationPoints = [
      { x: 100, y: 100 },
      { x: this.context.screenResolution.width - 100, y: 100 },
      { x: this.context.screenResolution.width / 2, y: this.context.screenResolution.height / 2 },
      { x: 100, y: this.context.screenResolution.height - 100 },
      {
        x: this.context.screenResolution.width - 100,
        y: this.context.screenResolution.height - 100,
      },
    ];

    for (const point of calibrationPoints) {
      const startTime = performance.now();

      // Simulate calibration click
      const result = await this.performPrecisionClick(point, {
        button: 'left',
        clickType: 'single',
        verifyTarget: true,
        humanLike: false, // Disable for calibration
      });

      const endTime = performance.now();
      const latency = endTime - startTime;

      this.calibrationData.set(`point_${point.x}_${point.y}`, {
        targetPoint: point,
        actualAccuracy: result.accuracy,
        latency: latency,
        success: result.success,
      });
    }

    this.isCalibrated = true;
    console.log('✅ Calibration completed');
  }

  async performPrecisionClick(
    target: InteractionPoint,
    options: AdvancedClickOptions = { button: 'left', clickType: 'single' }
  ): Promise<InteractionResult> {
    const startTime = performance.now();

    try {
      // Validate target and options
      this.validateInteraction(target, options);

      // Calculate optimal path to target
      const path = await this.calculateOptimalPath(this.context.cursorPosition, target, options);

      // Apply human-like variations if requested
      const adjustedTarget = options.humanLike
        ? this.applyHumanLikeVariations(target, options)
        : target;

      // Perform pre-click delay
      if (options.preDelay) {
        await this.delay(options.preDelay);
      }

      // Execute the movement
      const movementResult = await this.executeMovement(path, options);

      // Perform the click
      const clickResult = await this.executeClick(adjustedTarget, options);

      // Verify if requested
      if (options.verifyTarget) {
        const verificationResult = await this.verifyClickTarget(adjustedTarget);
        if (!verificationResult.success) {
          return this.handleClickFailure(target, options, verificationResult);
        }
      }

      // Apply post-click delay
      if (options.postDelay) {
        await this.delay(options.postDelay);
      }

      const endTime = performance.now();
      const result: InteractionResult = {
        success: true,
        accuracy: this.calculateAccuracy(target, adjustedTarget),
        timingPrecision: this.calculateTimingPrecision(startTime, endTime, options),
        metadata: {
          startTime,
          endTime,
          actualPath: path.points,
          expectedPath: [this.context.cursorPosition, target],
          deviation: this.calculateDeviation(target, adjustedTarget),
        },
      };

      this.recordInteraction(result);
      this.emit('interaction-completed', result);

      return result;
    } catch (error) {
      const endTime = performance.now();
      const result: InteractionResult = {
        success: false,
        accuracy: 0,
        timingPrecision: 0,
        errorCode: 'INTERACTION_FAILED',
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        metadata: {
          startTime,
          endTime,
          deviation: 0,
        },
      };

      this.recordInteraction(result);
      this.emit('interaction-failed', result);

      return result;
    }
  }

  private validateInteraction(target: InteractionPoint, options: AdvancedClickOptions): void {
    // Check safety constraints
    if (this.safetyConstraints.forbiddenRegions.length > 0) {
      const inForbiddenRegion = this.safetyConstraints.forbiddenRegions.some(
        region =>
          target.x >= region.x &&
          target.x <= region.x + region.width &&
          target.y >= region.y &&
          target.y <= region.y + region.height
      );

      if (inForbiddenRegion) {
        throw new Error('Target is in forbidden region');
      }
    }

    // Check allowed regions
    if (this.safetyConstraints.allowedRegions.length > 0) {
      const inAllowedRegion = this.safetyConstraints.allowedRegions.some(
        region =>
          target.x >= region.x &&
          target.x <= region.x + region.width &&
          target.y >= region.y &&
          target.y <= region.y + region.height
      );

      if (!inAllowedRegion) {
        throw new Error('Target is not in allowed region');
      }
    }

    // Check screen boundaries
    if (
      target.x < 0 ||
      target.x > this.context.screenResolution.width ||
      target.y < 0 ||
      target.y > this.context.screenResolution.height
    ) {
      throw new Error('Target is outside screen boundaries');
    }
  }

  private async calculateOptimalPath(
    start: InteractionPoint,
    end: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<InteractionPath> {
    const distance = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));
    const baseVelocity = options.humanLike ? this.getHumanLikeVelocity(distance) : 1000;

    const points: InteractionPoint[] = [];
    const steps = Math.max(10, Math.floor(distance / 10));

    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      let x, y;

      if (options.bezierCurve && options.humanLike) {
        // Use Bezier curve for more natural movement
        const controlPoint = this.calculateBezierControlPoint(start, end);
        const bezierPoint = this.calculateBezierPoint(start, controlPoint, end, t);
        x = bezierPoint.x;
        y = bezierPoint.y;
      } else {
        // Linear interpolation
        x = start.x + (end.x - start.x) * t;
        y = start.y + (end.y - start.y) * t;
      }

      // Add human-like variations
      if (options.humanLike) {
        const variation = this.getHumanLikeVariation(t, distance);
        x += variation.x;
        y += variation.y;
      }

      const velocity = this.calculateVelocityAtPoint(t, baseVelocity, options);

      points.push({
        x: Math.round(x),
        y: Math.round(y),
        timestamp: Date.now() + i * 10, // 10ms intervals
        confidence: 1.0 - Math.abs(t - 0.5) * 0.2, // Higher confidence in middle
      });
    }

    return {
      points,
      duration: steps * 10,
      velocity: baseVelocity,
      acceleration: options.acceleration || 0,
      smoothness: this.calculatePathSmoothness(points),
    };
  }

  private getHumanLikeVelocity(distance: number): number {
    // Fitts' Law: Time = a + b * log2(D/W + 1)
    // Simplified for mouse movement
    const a = 0.1; // Base time
    const b = 0.2; // Scaling factor
    const targetWidth = 20; // Assume 20px target width

    const time = a + b * Math.log2(distance / targetWidth + 1);
    return distance / (time * 1000); // pixels per second
  }

  private calculateBezierControlPoint(
    start: InteractionPoint,
    end: InteractionPoint
  ): InteractionPoint {
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;

    // Add some curvature
    const offset = Math.random() * 50 - 25; // Random offset -25 to 25

    return {
      x: midX + offset,
      y: midY + offset,
      timestamp: Date.now(),
      confidence: 0.8,
    };
  }

  private calculateBezierPoint(
    start: InteractionPoint,
    control: InteractionPoint,
    end: InteractionPoint,
    t: number
  ): InteractionPoint {
    const invT = 1 - t;
    const x = invT * invT * start.x + 2 * invT * t * control.x + t * t * end.x;
    const y = invT * invT * start.y + 2 * invT * t * control.y + t * t * end.y;

    return { x, y, timestamp: Date.now(), confidence: 1.0 };
  }

  private getHumanLikeVariation(t: number, distance: number): { x: number; y: number } {
    // Add small random variations to simulate human imprecision
    const maxVariation = Math.min(5, distance * 0.01);
    const variation = Math.sin(t * Math.PI) * maxVariation; // Bell curve variation

    return {
      x: (Math.random() - 0.5) * variation,
      y: (Math.random() - 0.5) * variation,
    };
  }

  private calculateVelocityAtPoint(
    t: number,
    baseVelocity: number,
    options: AdvancedClickOptions
  ): number {
    let velocity = baseVelocity;

    // Apply acceleration/deceleration
    if (options.acceleration) {
      if (t < 0.3) {
        // Acceleration phase
        velocity *= (t / 0.3) * (1 + options.acceleration);
      } else if (t > 0.7) {
        // Deceleration phase
        velocity *= ((1 - t) / 0.3) * (1 + (options.deceleration || options.acceleration));
      }
    }

    return velocity;
  }

  private calculatePathSmoothness(points: InteractionPoint[]): number {
    if (points.length < 3) return 1.0;

    let totalAngleChange = 0;
    for (let i = 1; i < points.length - 1; i++) {
      const angle1 = Math.atan2(points[i].y - points[i - 1].y, points[i].x - points[i - 1].x);
      const angle2 = Math.atan2(points[i + 1].y - points[i].y, points[i + 1].x - points[i].x);
      totalAngleChange += Math.abs(angle2 - angle1);
    }

    // Normalize smoothness (lower angle change = higher smoothness)
    return Math.max(0, 1 - totalAngleChange / (points.length - 2));
  }

  private applyHumanLikeVariations(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): InteractionPoint {
    const maxVariation = 2; // 2 pixel maximum variation
    const variation = {
      x: (Math.random() - 0.5) * maxVariation,
      y: (Math.random() - 0.5) * maxVariation,
    };

    return {
      x: target.x + variation.x,
      y: target.y + variation.y,
      timestamp: target.timestamp,
      confidence: target.confidence * 0.95, // Slightly lower confidence due to variation
    };
  }

  private async executeMovement(
    path: InteractionPath,
    options: AdvancedClickOptions
  ): Promise<InteractionResult> {
    console.log(`🎯 Executing movement along ${path.points.length} points`);

    // Simulate smooth mouse movement
    for (let i = 0; i < path.points.length - 1; i++) {
      const point = path.points[i];
      const nextPoint = path.points[i + 1];

      // Update cursor position
      this.context.cursorPosition = point;

      // Calculate delay based on velocity
      const distance = Math.sqrt(
        Math.pow(nextPoint.x - point.x, 2) + Math.pow(nextPoint.y - point.y, 2)
      );
      const delay = Math.max(1, (distance / path.velocity) * 1000);

      await this.delay(delay);

      this.emit('cursor-moved', point);
    }

    // Update final position
    this.context.cursorPosition = path.points[path.points.length - 1];

    return {
      success: true,
      accuracy: 1.0,
      timingPrecision: 1.0,
      metadata: {
        startTime: performance.now(),
        endTime: performance.now(),
        actualPath: path.points,
        deviation: 0,
      },
    };
  }

  private async executeClick(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<InteractionResult> {
    console.log(
      `🖱️ Executing ${options.clickType} ${options.button} click at (${target.x}, ${target.y})`
    );

    const startTime = performance.now();

    try {
      // Simulate the actual click operation
      // This would integrate with the native automation system

      switch (options.clickType) {
        case 'single':
          await this.performSingleClick(target, options);
          break;
        case 'double':
          await this.performDoubleClick(target, options);
          break;
        case 'triple':
          await this.performTripleClick(target, options);
          break;
        case 'hold':
          await this.performMouseHold(target, options);
          break;
        case 'release':
          await this.performMouseRelease(target, options);
          break;
      }

      const endTime = performance.now();

      return {
        success: true,
        accuracy: 1.0,
        timingPrecision: this.calculateTimingPrecision(startTime, endTime, options),
        metadata: {
          startTime,
          endTime,
          deviation: 0,
        },
      };
    } catch (error) {
      const endTime = performance.now();

      return {
        success: false,
        accuracy: 0,
        timingPrecision: 0,
        errorCode: 'CLICK_FAILED',
        errorMessage: error instanceof Error ? error.message : 'Unknown click error',
        metadata: {
          startTime,
          endTime,
          deviation: 0,
        },
      };
    }
  }

  private async performSingleClick(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<void> {
    // Mouse down
    this.emit('mouse-down', { point: target, button: options.button });

    // Hold duration
    const holdDuration = options.duration || (options.humanLike ? 50 + Math.random() * 50 : 50);
    await this.delay(holdDuration);

    // Mouse up
    this.emit('mouse-up', { point: target, button: options.button });
  }

  private async performDoubleClick(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<void> {
    await this.performSingleClick(target, options);

    // Delay between clicks
    const betweenClickDelay = options.humanLike ? 100 + Math.random() * 100 : 150;
    await this.delay(betweenClickDelay);

    await this.performSingleClick(target, options);
  }

  private async performTripleClick(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<void> {
    await this.performDoubleClick(target, options);

    // Delay before third click
    const betweenClickDelay = options.humanLike ? 100 + Math.random() * 100 : 150;
    await this.delay(betweenClickDelay);

    await this.performSingleClick(target, options);
  }

  private async performMouseHold(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<void> {
    this.emit('mouse-down', { point: target, button: options.button, hold: true });
  }

  private async performMouseRelease(
    target: InteractionPoint,
    options: AdvancedClickOptions
  ): Promise<void> {
    this.emit('mouse-up', { point: target, button: options.button, release: true });
  }

  private async verifyClickTarget(target: InteractionPoint): Promise<InteractionResult> {
    // Implement target verification logic
    // This would check if the click actually hit the intended target

    return {
      success: true,
      accuracy: 0.95,
      timingPrecision: 1.0,
      metadata: {
        startTime: performance.now(),
        endTime: performance.now(),
        deviation: 0,
      },
    };
  }

  private async handleClickFailure(
    originalTarget: InteractionPoint,
    options: AdvancedClickOptions,
    verificationResult: InteractionResult
  ): Promise<InteractionResult> {
    console.warn(
      '🔄 Click verification failed, applying fallback strategy:',
      options.fallbackStrategy
    );

    switch (options.fallbackStrategy) {
      case 'retry':
        console.log('🔁 Retrying click...');
        return this.performPrecisionClick(originalTarget, {
          ...options,
          fallbackStrategy: 'abort',
        });

      case 'alternative':
        console.log('🎯 Trying alternative interaction method...');
        // Implement alternative methods (e.g., keyboard navigation)
        return verificationResult;

      case 'abort':
      default:
        console.log('🛑 Aborting interaction due to repeated failures');
        return verificationResult;
    }
  }

  async performAdvancedDrag(options: DragOperationOptions): Promise<InteractionResult> {
    const startTime = performance.now();

    try {
      console.log(
        `🎯 Performing drag from (${options.startPoint.x}, ${options.startPoint.y}) to (${options.endPoint.x}, ${options.endPoint.y})`
      );

      // Calculate drag path
      const path = await this.calculateDragPath(options);

      // Start drag
      this.emit('mouse-down', { point: options.startPoint, button: 'left', drag: true });

      // Execute drag movement
      for (const point of path.points) {
        this.context.cursorPosition = point;
        this.emit('mouse-move', { point, dragging: true });

        // Check for pause points
        if (options.pausePoints?.some(p => this.pointsAreClose(p, point, 10))) {
          await this.delay(options.pauseDuration || 100);
        }

        await this.delay(10); // Small delay between movements
      }

      // End drag
      this.emit('mouse-up', { point: options.endPoint, button: 'left', drag: true });

      const endTime = performance.now();

      const result: InteractionResult = {
        success: true,
        accuracy: this.calculateAccuracy(options.endPoint, path.points[path.points.length - 1]),
        timingPrecision: 1.0,
        metadata: {
          startTime,
          endTime,
          actualPath: path.points,
          expectedPath: [options.startPoint, options.endPoint],
          deviation: 0,
        },
      };

      this.recordInteraction(result);
      return result;
    } catch (error) {
      const endTime = performance.now();

      const result: InteractionResult = {
        success: false,
        accuracy: 0,
        timingPrecision: 0,
        errorCode: 'DRAG_FAILED',
        errorMessage: error instanceof Error ? error.message : 'Unknown drag error',
        metadata: {
          startTime,
          endTime,
          deviation: 0,
        },
      };

      this.recordInteraction(result);
      return result;
    }
  }

  private async calculateDragPath(options: DragOperationOptions): Promise<InteractionPath> {
    const points: InteractionPoint[] = [];
    const distance = Math.sqrt(
      Math.pow(options.endPoint.x - options.startPoint.x, 2) +
        Math.pow(options.endPoint.y - options.startPoint.y, 2)
    );

    let pathPoints: InteractionPoint[];

    switch (options.path) {
      case 'straight':
        pathPoints = this.generateStraightPath(options.startPoint, options.endPoint, 50);
        break;
      case 'curved':
        pathPoints = this.generateCurvedPath(options.startPoint, options.endPoint, 50);
        break;
      case 'custom':
        pathPoints = options.customPath || [options.startPoint, options.endPoint];
        break;
      default:
        pathPoints = [options.startPoint, options.endPoint];
    }

    // Apply smoothing if requested
    if (options.smoothing) {
      pathPoints = this.smoothPath(pathPoints);
    }

    // Apply snap to grid if requested
    if (options.snapToGrid && options.gridSize) {
      pathPoints = pathPoints.map(point => this.snapToGrid(point, options.gridSize!));
    }

    const baseVelocity = this.getSpeedValue(options.speed, options.customSpeed);

    return {
      points: pathPoints,
      duration: (distance / baseVelocity) * 1000,
      velocity: baseVelocity,
      acceleration: 0,
      smoothness: this.calculatePathSmoothness(pathPoints),
    };
  }

  private generateStraightPath(
    start: InteractionPoint,
    end: InteractionPoint,
    steps: number
  ): InteractionPoint[] {
    const points: InteractionPoint[] = [];

    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      points.push({
        x: Math.round(start.x + (end.x - start.x) * t),
        y: Math.round(start.y + (end.y - start.y) * t),
        timestamp: Date.now() + i * 10,
        confidence: 1.0,
      });
    }

    return points;
  }

  private generateCurvedPath(
    start: InteractionPoint,
    end: InteractionPoint,
    steps: number
  ): InteractionPoint[] {
    const points: InteractionPoint[] = [];
    const controlPoint = this.calculateBezierControlPoint(start, end);

    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const point = this.calculateBezierPoint(start, controlPoint, end, t);

      points.push({
        x: Math.round(point.x),
        y: Math.round(point.y),
        timestamp: Date.now() + i * 10,
        confidence: 1.0,
      });
    }

    return points;
  }

  private smoothPath(points: InteractionPoint[]): InteractionPoint[] {
    if (points.length < 3) return points;

    const smoothed: InteractionPoint[] = [points[0]];

    for (let i = 1; i < points.length - 1; i++) {
      const prev = points[i - 1];
      const current = points[i];
      const next = points[i + 1];

      smoothed.push({
        x: Math.round((prev.x + current.x + next.x) / 3),
        y: Math.round((prev.y + current.y + next.y) / 3),
        timestamp: current.timestamp,
        confidence: current.confidence,
      });
    }

    smoothed.push(points[points.length - 1]);
    return smoothed;
  }

  private snapToGrid(point: InteractionPoint, gridSize: number): InteractionPoint {
    return {
      ...point,
      x: Math.round(point.x / gridSize) * gridSize,
      y: Math.round(point.y / gridSize) * gridSize,
    };
  }

  private getSpeedValue(speed: DragOperationOptions['speed'], customSpeed?: number): number {
    if (speed === 'custom' && customSpeed) {
      return customSpeed;
    }

    switch (speed) {
      case 'slow':
        return 200;
      case 'normal':
        return 500;
      case 'fast':
        return 1000;
      default:
        return 500;
    }
  }

  private pointsAreClose(a: InteractionPoint, b: InteractionPoint, threshold: number): boolean {
    const distance = Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2));
    return distance <= threshold;
  }

  async performAdvancedKeyboardInput(options: KeyboardInputOptions): Promise<InteractionResult> {
    const startTime = performance.now();

    try {
      console.log('⌨️ Performing advanced keyboard input...');

      if (options.text) {
        await this.typeText(options.text, options);
      }

      if (options.keys) {
        await this.pressKeys(options.keys, options);
      }

      const endTime = performance.now();

      const result: InteractionResult = {
        success: true,
        accuracy: 1.0,
        timingPrecision: this.calculateTimingPrecision(startTime, endTime, {}),
        metadata: {
          startTime,
          endTime,
          deviation: 0,
        },
      };

      this.recordInteraction(result);
      return result;
    } catch (error) {
      const endTime = performance.now();

      const result: InteractionResult = {
        success: false,
        accuracy: 0,
        timingPrecision: 0,
        errorCode: 'KEYBOARD_INPUT_FAILED',
        errorMessage: error instanceof Error ? error.message : 'Unknown keyboard error',
        metadata: {
          startTime,
          endTime,
          deviation: 0,
        },
      };

      this.recordInteraction(result);
      return result;
    }
  }

  private async typeText(text: string, options: KeyboardInputOptions): Promise<void> {
    console.log(`📝 Typing text: "${text}"`);

    for (const char of text) {
      this.emit('key-press', { key: char, modifiers: options.modifiers || [] });

      // Apply timing based on options
      let delay = 50; // Default

      switch (options.timing) {
        case 'instant':
          delay = 0;
          break;
        case 'realistic':
          delay = 50 + Math.random() * 100; // 50-150ms realistic typing
          break;
        case 'custom':
          delay = options.customTiming?.betweenKeysDelay || 50;
          break;
      }

      if (delay > 0) {
        await this.delay(delay);
      }
    }
  }

  private async pressKeys(keys: string[], options: KeyboardInputOptions): Promise<void> {
    console.log(`🔑 Pressing keys: ${keys.join('+')}`);

    // Press modifiers first
    if (options.modifiers) {
      for (const modifier of options.modifiers) {
        this.emit('key-down', { key: modifier });
      }
    }

    // Press main keys
    for (const key of keys) {
      this.emit('key-down', { key });

      const holdDuration = options.customTiming?.keyDownDelay || 50;
      await this.delay(holdDuration);

      this.emit('key-up', { key });
    }

    // Release modifiers
    if (options.modifiers) {
      for (const modifier of options.modifiers.reverse()) {
        this.emit('key-up', { key: modifier });
      }
    }
  }

  private calculateAccuracy(expected: InteractionPoint, actual: InteractionPoint): number {
    const distance = Math.sqrt(
      Math.pow(actual.x - expected.x, 2) + Math.pow(actual.y - expected.y, 2)
    );

    // Accuracy decreases with distance (max 10px for perfect accuracy)
    return Math.max(0, 1 - distance / 10);
  }

  private calculateTimingPrecision(startTime: number, endTime: number, options: any): number {
    const actualDuration = endTime - startTime;
    const expectedDuration = options.duration || 100;

    const timingError = Math.abs(actualDuration - expectedDuration) / expectedDuration;
    return Math.max(0, 1 - timingError);
  }

  private calculateDeviation(expected: InteractionPoint, actual: InteractionPoint): number {
    return Math.sqrt(Math.pow(actual.x - expected.x, 2) + Math.pow(actual.y - expected.y, 2));
  }

  private recordInteraction(result: InteractionResult): void {
    this.interactionHistory.push(result);

    // Keep only last 1000 interactions
    if (this.interactionHistory.length > 1000) {
      this.interactionHistory.shift();
    }

    this.performanceMetrics.totalInteractions++;
  }

  private updatePerformanceMetrics(): void {
    if (this.interactionHistory.length === 0) return;

    const recentResults = this.interactionHistory.slice(-100); // Last 100 interactions

    this.performanceMetrics.accuracy =
      recentResults.reduce((sum, r) => sum + r.accuracy, 0) / recentResults.length;
    this.performanceMetrics.averageLatency =
      recentResults.reduce((sum, r) => sum + (r.metadata.endTime - r.metadata.startTime), 0) /
      recentResults.length;
    this.performanceMetrics.successRate =
      recentResults.filter(r => r.success).length / recentResults.length;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getPerformanceMetrics() {
    return { ...this.performanceMetrics };
  }

  getInteractionHistory() {
    return [...this.interactionHistory];
  }

  async dispose(): Promise<void> {
    this.removeAllListeners();
    this.interactionHistory.length = 0;
    this.gestureLibrary.clear();
    this.calibrationData.clear();

    console.log('✅ Precision Interaction Engine disposed');
  }
}

export interface PrecisionInteractionConfig {
  context?: Partial<InteractionContext>;
  safetyConstraints?: Partial<SafetyConstraints>;
  calibrationRequired?: boolean;
  performanceMonitoring?: boolean;
}

export default PrecisionInteractionEngine;
