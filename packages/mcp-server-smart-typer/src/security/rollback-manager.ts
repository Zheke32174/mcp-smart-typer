/**
 * Rollback Manager
 * Implements dry-run mode and rollback functionality (e.g., Ctrl+Z after failed verification)
 */

import { logger } from '../utils/logger.js';
import { getAuditLogger } from './audit-logger.js';

export interface RollbackState {
  id: string;
  operation: string;
  timestamp: string;
  fieldId: string;
  originalValue?: string;
  newValue?: string;
  metadata?: Record<string, any>;
}

export interface DryRunResult {
  wouldSucceed: boolean;
  predictedChanges: Array<{
    fieldId: string;
    currentValue?: string;
    proposedValue: string;
    changeType: 'type' | 'clear' | 'append';
  }>;
  warnings: string[];
  estimatedTime: number;
}

export class RollbackManager {
  private rollbackStates: Map<string, RollbackState>;
  private maxRollbackHistory: number;
  private dryRunMode: boolean;

  constructor() {
    this.rollbackStates = new Map();
    this.maxRollbackHistory = 50; // Keep last 50 operations
    this.dryRunMode = process.env.DRY_RUN_MODE === 'true';

    logger.info('Rollback Manager initialized', {
      dryRunMode: this.dryRunMode,
      maxRollbackHistory: this.maxRollbackHistory,
    });
  }

  /**
   * Enable or disable dry-run mode
   */
  setDryRunMode(enabled: boolean): void {
    this.dryRunMode = enabled;
    logger.info('Dry-run mode changed', { enabled });
  }

  /**
   * Check if dry-run mode is enabled
   */
  isDryRunMode(): boolean {
    return this.dryRunMode;
  }

  /**
   * Execute a typing operation with rollback support
   */
  async executeWithRollback<T>(
    operation: string,
    fieldId: string,
    executor: () => Promise<T>,
    rollbackExecutor?: () => Promise<void>,
    options?: {
      dryRun?: boolean;
      captureOriginalValue?: boolean;
    }
  ): Promise<{ result?: T; dryRunResult?: DryRunResult; error?: Error }> {
    const operationId = this.generateOperationId();
    const isDryRun = options?.dryRun ?? this.dryRunMode;

    logger.debug('Executing operation with rollback support', {
      operationId,
      operation,
      fieldId,
      isDryRun,
      captureOriginalValue: options?.captureOriginalValue,
    });

    try {
      // In dry-run mode, simulate the operation
      if (isDryRun) {
        const dryRunResult = await this.simulateOperation(operation, fieldId, options);

        getAuditLogger().logOperation('DRY_RUN', operation, {
          fieldId,
          success: dryRunResult.wouldSucceed,
          metadata: {
            operationId,
            predictedChanges: dryRunResult.predictedChanges,
            warnings: dryRunResult.warnings,
            estimatedTime: dryRunResult.estimatedTime,
          },
        });

        return { dryRunResult };
      }

      // Capture original state if requested
      let originalValue: string | undefined;
      if (options?.captureOriginalValue) {
        try {
          originalValue = await this.captureFieldValue(fieldId);
        } catch (error) {
          logger.warn('Failed to capture original field value', {
            fieldId,
            error: error instanceof Error ? error.message : String(error),
          });
        }
      }

      // Execute the actual operation
      const result = await executor();

      // Store rollback state
      const rollbackState: RollbackState = {
        id: operationId,
        operation,
        timestamp: new Date().toISOString(),
        fieldId,
        originalValue,
        metadata: { success: true },
      };

      this.storeRollbackState(rollbackState);

      logger.debug('Operation executed successfully', {
        operationId,
        operation,
        fieldId,
        hasOriginalValue: !!originalValue,
      });

      return { result };
    } catch (error) {
      logger.error('Operation failed', {
        operationId,
        operation,
        fieldId,
        error: error instanceof Error ? error.message : String(error),
      });

      // Store failed operation state (in case we need to clean up)
      const rollbackState: RollbackState = {
        id: operationId,
        operation,
        timestamp: new Date().toISOString(),
        fieldId,
        metadata: { success: false, error: error instanceof Error ? error.message : String(error) },
      };

      this.storeRollbackState(rollbackState);

      return { error: error instanceof Error ? error : new Error(String(error)) };
    }
  }

  /**
   * Simulate an operation for dry-run mode
   */
  private async simulateOperation(
    operation: string,
    fieldId: string,
    options?: any
  ): Promise<DryRunResult> {
    const warnings: string[] = [];
    let wouldSucceed = true;
    let estimatedTime = 100; // Base time in milliseconds

    // Simulate based on operation type
    const predictedChanges = [];

    switch (operation) {
      case 'type_text':
        const textLength = options?.text?.length || 0;
        estimatedTime = Math.max(100, textLength * 50); // 50ms per character

        predictedChanges.push({
          fieldId,
          currentValue: '[SIMULATED_CURRENT_VALUE]',
          proposedValue: options?.text || '[SIMULATED_TEXT]',
          changeType: options?.clearFirst ? 'type' : ('append' as const),
        });

        if (textLength > 1000) {
          warnings.push('Large text input may take significant time to type');
        }

        // Check for potential sensitive data
        if (this.containsSensitivePatterns(options?.text)) {
          warnings.push('Text appears to contain sensitive information');
        }
        break;

      case 'clear_field':
        predictedChanges.push({
          fieldId,
          currentValue: '[SIMULATED_CURRENT_VALUE]',
          proposedValue: '',
          changeType: 'clear' as const,
        });
        estimatedTime = 50;
        break;

      default:
        warnings.push(`Unknown operation type: ${operation}`);
        wouldSucceed = false;
    }

    // Add random simulation delay
    estimatedTime += Math.random() * 50;

    return {
      wouldSucceed,
      predictedChanges,
      warnings,
      estimatedTime,
    };
  }

  /**
   * Check if text contains sensitive patterns
   */
  private containsSensitivePatterns(text?: string): boolean {
    if (!text) return false;

    const sensitivePatterns = [
      /password/i,
      /\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b/, // Credit card
      /\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/, // SSN
      /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}/, // Email
    ];

    return sensitivePatterns.some(pattern => pattern.test(text));
  }

  /**
   * Attempt to rollback the last operation
   */
  async rollbackLastOperation(): Promise<{
    success: boolean;
    error?: string;
    rollbackState?: RollbackState;
  }> {
    const lastOperationId = Array.from(this.rollbackStates.keys()).pop();

    if (!lastOperationId) {
      return { success: false, error: 'No operations to rollback' };
    }

    return this.rollbackOperation(lastOperationId);
  }

  /**
   * Rollback a specific operation by ID
   */
  async rollbackOperation(
    operationId: string
  ): Promise<{ success: boolean; error?: string; rollbackState?: RollbackState }> {
    const rollbackState = this.rollbackStates.get(operationId);

    if (!rollbackState) {
      return { success: false, error: `Operation ${operationId} not found in rollback history` };
    }

    logger.info('Attempting to rollback operation', {
      operationId,
      operation: rollbackState.operation,
      fieldId: rollbackState.fieldId,
    });

    try {
      // Attempt to restore original value if available
      if (rollbackState.originalValue) {
        await this.restoreFieldValue(rollbackState.fieldId, rollbackState.originalValue);
      } else {
        // If no original value, try to clear the field
        await this.clearField(rollbackState.fieldId);
      }

      // Log successful rollback
      getAuditLogger().logRollback(rollbackState.operation, true, {
        operationId,
        fieldId: rollbackState.fieldId,
        originalValue: rollbackState.originalValue,
        rollbackMethod: rollbackState.originalValue ? 'restore' : 'clear',
      });

      logger.info('Operation rolled back successfully', {
        operationId,
        operation: rollbackState.operation,
        fieldId: rollbackState.fieldId,
      });

      return { success: true, rollbackState };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);

      // Log failed rollback
      getAuditLogger().logRollback(rollbackState.operation, false, {
        operationId,
        fieldId: rollbackState.fieldId,
        error: errorMessage,
      });

      logger.error('Failed to rollback operation', {
        operationId,
        operation: rollbackState.operation,
        fieldId: rollbackState.fieldId,
        error: errorMessage,
      });

      return { success: false, error: errorMessage, rollbackState };
    }
  }

  /**
   * Get rollback history
   */
  getRollbackHistory(): RollbackState[] {
    return Array.from(this.rollbackStates.values()).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  /**
   * Clear rollback history
   */
  clearRollbackHistory(): void {
    const count = this.rollbackStates.size;
    this.rollbackStates.clear();

    logger.info('Rollback history cleared', { clearedOperations: count });
  }

  /**
   * Store rollback state with history management
   */
  private storeRollbackState(state: RollbackState): void {
    this.rollbackStates.set(state.id, state);

    // Manage history size
    if (this.rollbackStates.size > this.maxRollbackHistory) {
      const oldestId = Array.from(this.rollbackStates.keys())[0];
      this.rollbackStates.delete(oldestId);
    }
  }

  /**
   * Generate unique operation ID
   */
  private generateOperationId(): string {
    return `rollback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Capture current field value (to be implemented with actual UI automation)
   */
  private async captureFieldValue(fieldId: string): Promise<string> {
    // This would integrate with the actual UI automation client
    // For now, return a placeholder
    logger.debug('Capturing field value', { fieldId });
    return '[CAPTURED_VALUE]';
  }

  /**
   * Restore field value (to be implemented with actual UI automation)
   */
  private async restoreFieldValue(fieldId: string, value: string): Promise<void> {
    // This would integrate with the actual UI automation client to restore the value
    logger.debug('Restoring field value', { fieldId, valueLength: value.length });

    // Simulate the restore operation
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  /**
   * Clear field (to be implemented with actual UI automation)
   */
  private async clearField(fieldId: string): Promise<void> {
    // This would integrate with the actual UI automation client to clear the field
    logger.debug('Clearing field', { fieldId });

    // Simulate the clear operation
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  /**
   * Get rollback statistics
   */
  getRollbackStats(): {
    totalOperations: number;
    dryRunMode: boolean;
    maxHistorySize: number;
    oldestOperation?: string;
    newestOperation?: string;
  } {
    const operations = Array.from(this.rollbackStates.values());
    const sortedByTime = operations.sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    return {
      totalOperations: this.rollbackStates.size,
      dryRunMode: this.dryRunMode,
      maxHistorySize: this.maxRollbackHistory,
      oldestOperation: sortedByTime[0]?.timestamp,
      newestOperation: sortedByTime[sortedByTime.length - 1]?.timestamp,
    };
  }
}

export const rollbackManager = new RollbackManager();
