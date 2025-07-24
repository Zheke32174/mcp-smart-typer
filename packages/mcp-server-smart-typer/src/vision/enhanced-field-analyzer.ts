/**
 * Enhanced Field Analyzer that integrates with Python Field Purpose Classifier
 * Combines DOM/UIA attributes, OCR text, placeholders, and ML model predictions
 */

import { FieldAnalyzer, FieldAnalysisResult, FieldBounds } from './field-analyzer.js';
import { logger } from '../utils/logger.js';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

export interface EnhancedFieldInfo {
  // DOM/UIA attributes
  tagName?: string;
  elementType?: string;
  name?: string;
  id?: string;
  className?: string;
  placeholder?: string;
  ariaLabel?: string;
  title?: string;
  autocomplete?: string;
  
  // Visual attributes
  x: number;
  y: number;
  width: number;
  height: number;
  
  // Text context
  labelText?: string;
  neighboringText?: string;
  parentText?: string;
  
  // Model predictions
  visionPrediction?: {
    predictedType: string;
    confidence: number;
    classProbabilities: Record<string, number>;
  };
  ocrConfidence: number;
}

export interface EnhancedAnalysisResult extends FieldAnalysisResult {
  enhancedClassification?: {
    predictedType: string;
    confidence: number;
    methodUsed: string;
    allProbabilities: Record<string, number>;
    featureImportance?: Record<string, number>;
  };
}

export class EnhancedFieldAnalyzer extends FieldAnalyzer {
  private pythonScriptPath: string;
  private isEnhancedMode: boolean;

  constructor(modelCacheDir?: string, enableEnhancedMode: boolean = true) {
    super(modelCacheDir);
    this.pythonScriptPath = path.join(__dirname, '..', '..', '..', 'native-helpers', 'src', 'field_purpose_classifier.py');
    this.isEnhancedMode = enableEnhancedMode;
  }

  async analyzeFieldsEnhanced(
    screenshotPath: string,
    fieldBounds: FieldBounds[],
    semanticData?: Array<{ type?: string; confidence?: number }>,
    fieldsInfo?: EnhancedFieldInfo[]
  ): Promise<EnhancedAnalysisResult[]> {
    // First run the original analysis
    const originalResults = await this.analyzeFields(screenshotPath, fieldBounds, semanticData);
    
    if (!this.isEnhancedMode) {
      return originalResults;
    }

    // Enhance with Python classifier if available
    const enhancedResults: EnhancedAnalysisResult[] = [];
    
    for (let i = 0; i < originalResults.length; i++) {
      const originalResult = originalResults[i];
      const fieldInfo = fieldsInfo?.[i];
      const bounds = fieldBounds[i];
      
      try {
        // Prepare field info for Python classifier
        const enhancedFieldInfo: EnhancedFieldInfo = {
          ...fieldInfo,
          x: bounds.x,
          y: bounds.y,
          width: bounds.width,
          height: bounds.height,
          visionPrediction: originalResult.visionClassification ? {
            predictedType: originalResult.visionClassification.predictedType,
            confidence: originalResult.visionClassification.confidence,
            classProbabilities: originalResult.visionClassification.classProbabilities,
          } : undefined,
          ocrConfidence: originalResult.ocrContext?.confidence || 0,
        };

        // Get enhanced classification
        const enhancedClassification = await this.getEnhancedClassification(enhancedFieldInfo);
        
        enhancedResults.push({
          ...originalResult,
          enhancedClassification,
        });
        
      } catch (error) {
        logger.warn(`Enhanced classification failed for field ${i}:`, error);
        enhancedResults.push(originalResult);
      }
    }

    return enhancedResults;
  }

  private async getEnhancedClassification(fieldInfo: EnhancedFieldInfo): Promise<{
    predictedType: string;
    confidence: number;
    methodUsed: string;
    allProbabilities: Record<string, number>;
    featureImportance?: Record<string, number>;
  }> {
    return new Promise((resolve, reject) => {
      // Prepare Python script arguments
      const scriptArgs = [
        'classify_single_field',
        JSON.stringify(fieldInfo)
      ];

      // Spawn Python process
      const pythonProcess = spawn('python', [this.pythonScriptPath, ...scriptArgs], {
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
          return;
        }

        try {
          const result = JSON.parse(stdout.trim());
          resolve({
            predictedType: result.predicted_type,
            confidence: result.confidence,
            methodUsed: result.method_used,
            allProbabilities: result.all_probabilities,
            featureImportance: result.feature_importance,
          });
        } catch (error) {
          reject(new Error(`Failed to parse Python script output: ${error}`));
        }
      });

      pythonProcess.on('error', (error) => {
        reject(new Error(`Failed to spawn Python process: ${error}`));
      });
    });
  }

  /**
   * Analyze a single field with enhanced classification
   */
  async analyzeFieldEnhanced(
    screenshotPath: string,
    bounds: FieldBounds,
    fieldIndex: number,
    semanticData?: { type?: string; confidence?: number },
    fieldInfo?: EnhancedFieldInfo
  ): Promise<EnhancedAnalysisResult> {
    const results = await this.analyzeFieldsEnhanced(
      screenshotPath,
      [bounds],
      semanticData ? [semanticData] : undefined,
      fieldInfo ? [fieldInfo] : undefined
    );
    
    return results[0];
  }

  /**
   * Extract DOM/UIA information from browser automation or UI Automation APIs
   */
  static extractDOMInfo(element: any): Partial<EnhancedFieldInfo> {
    return {
      tagName: element.tagName?.toLowerCase(),
      elementType: element.type?.toLowerCase(),
      name: element.name,
      id: element.id,
      className: element.className,
      placeholder: element.placeholder,
      ariaLabel: element.getAttribute?.('aria-label'),
      title: element.title,
      autocomplete: element.autocomplete,
    };
  }

  /**
   * Extract neighboring text context
   */
  static extractTextContext(element: any): Partial<EnhancedFieldInfo> {
    const context: Partial<EnhancedFieldInfo> = {};
    
    // Try to find associated label
    if (element.id) {
      const label = document.querySelector(`label[for="${element.id}"]`);
      if (label) {
        context.labelText = label.textContent?.trim();
      }
    }

    // Get parent text content
    const parent = element.parentElement;
    if (parent) {
      context.parentText = parent.textContent?.trim();
    }

    // Get neighboring text (previous and next siblings)
    const neighbors: string[] = [];
    
    if (element.previousElementSibling) {
      const prevText = element.previousElementSibling.textContent?.trim();
      if (prevText) neighbors.push(prevText);
    }
    
    if (element.nextElementSibling) {
      const nextText = element.nextElementSibling.textContent?.trim();
      if (nextText) neighbors.push(nextText);
    }
    
    if (neighbors.length > 0) {
      context.neighboringText = neighbors.join(' ');
    }

    return context;
  }

  /**
   * Create comprehensive field info from DOM element
   */
  static createFieldInfo(element: any, bounds: FieldBounds): EnhancedFieldInfo {
    const domInfo = this.extractDOMInfo(element);
    const textContext = this.extractTextContext(element);
    
    return {
      ...domInfo,
      ...textContext,
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
      ocrConfidence: 0,
    };
  }

  /**
   * Batch process multiple fields with enhanced classification
   */
  async batchAnalyzeFields(
    screenshotPath: string,
    fieldsData: Array<{
      bounds: FieldBounds;
      semanticData?: { type?: string; confidence?: number };
      fieldInfo?: EnhancedFieldInfo;
    }>
  ): Promise<EnhancedAnalysisResult[]> {
    const bounds = fieldsData.map(f => f.bounds);
    const semanticData = fieldsData.map(f => f.semanticData);
    const fieldsInfo = fieldsData.map(f => f.fieldInfo);
    
    return this.analyzeFieldsEnhanced(
      screenshotPath,
      bounds,
      semanticData.filter(Boolean) as Array<{ type?: string; confidence?: number }>,
      fieldsInfo.filter(Boolean) as EnhancedFieldInfo[]
    );
  }

  /**
   * Get classification confidence threshold recommendations
   */
  getConfidenceThresholds(): Record<string, number> {
    return {
      'email': 0.7,
      'password': 0.8,
      'search': 0.6,
      'username': 0.7,
      'name': 0.6,
      'phone': 0.7,
      'address': 0.6,
      'comment': 0.5,
      'text': 0.3,
      'button': 0.8,
      'submit': 0.8,
    };
  }

  /**
   * Filter results by confidence threshold
   */
  filterByConfidence(results: EnhancedAnalysisResult[], useEnhanced: boolean = true): EnhancedAnalysisResult[] {
    const thresholds = this.getConfidenceThresholds();
    
    return results.filter(result => {
      const classification = useEnhanced && result.enhancedClassification 
        ? result.enhancedClassification 
        : { predictedType: result.combinedType, confidence: result.combinedConfidence };
      
      const threshold = thresholds[classification.predictedType] || 0.5;
      return classification.confidence >= threshold;
    });
  }

  /**
   * Get model performance statistics
   */
  async getModelStats(): Promise<{
    modelInfo: any;
    analysisCount: number;
    averageConfidence: number;
    methodDistribution: Record<string, number>;
  }> {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', [this.pythonScriptPath, 'get_model_info'], {
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script failed: ${stderr}`));
          return;
        }

        try {
          const modelInfo = JSON.parse(stdout.trim());
          resolve({
            modelInfo,
            analysisCount: 0, // Would be tracked in production
            averageConfidence: 0, // Would be calculated from history
            methodDistribution: {}, // Would be tracked in production
          });
        } catch (error) {
          reject(new Error(`Failed to parse model info: ${error}`));
        }
      });
    });
  }
}

// Singleton instance
let enhancedAnalyzerInstance: EnhancedFieldAnalyzer | null = null;

export function getEnhancedFieldAnalyzer(): EnhancedFieldAnalyzer {
  if (!enhancedAnalyzerInstance) {
    enhancedAnalyzerInstance = new EnhancedFieldAnalyzer();
  }
  return enhancedAnalyzerInstance;
}

// Export for backward compatibility
export { FieldBounds, FieldAnalysisResult };
