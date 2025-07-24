/**
 * Combined OCR and Vision Analysis for Enhanced Field Detection
 */

import * as tf from '@tensorflow/tfjs-node';
import { getOCRInstance, analyzeFieldContext } from '../ocr/tesseract-ocr.js';
import { logger } from '../utils/logger.js';
import path from 'path';
import fs from 'fs/promises';
import sharp from 'sharp';

export interface FieldAnalysisResult {
  fieldIndex: number;
  semanticType?: string;
  ocrContext?: {
    text: string;
    confidence: number;
  };
  visionClassification?: {
    predictedType: string;
    confidence: number;
    classProbabilities: Record<string, number>;
  };
  combinedType: string;
  combinedConfidence: number;
  analysisMethod: 'semantic' | 'ocr' | 'vision' | 'combined';
}

export interface FieldBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export class FieldAnalyzer {
  private visionModel: tf.LayersModel | null = null;
  private modelLoaded = false;
  private readonly FIELD_TYPES = ['email', 'password', 'search', 'comment', 'username', 'name', 'phone', 'text', 'button'];
  private readonly modelCacheDir: string;

  constructor(modelCacheDir?: string) {
    this.modelCacheDir = modelCacheDir || path.join(process.cwd(), '.cache', 'models');
  }

  async initialize(): Promise<void> {
    try {
      await this.ensureCacheDir();
      await this.loadOrCreateModel();
      logger.info('Field analyzer initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize field analyzer:', error);
      throw error;
    }
  }

  private async ensureCacheDir(): Promise<void> {
    try {
      await fs.mkdir(this.modelCacheDir, { recursive: true });
    } catch (error) {
      logger.warn('Failed to create cache directory:', error);
    }
  }

  private async loadOrCreateModel(): Promise<void> {
    const modelPath = path.join(this.modelCacheDir, 'field-classifier');
    
    try {
      // Try to load cached model
      if (await this.modelExists(modelPath)) {
        this.visionModel = await tf.loadLayersModel(`file://${modelPath}/model.json`);
        logger.info('Loaded cached vision model');
      } else {
        // Create new model
        this.visionModel = this.createSimpleVisionModel();
        await this.saveModel(modelPath);
        logger.info('Created new vision model');
      }
      
      this.modelLoaded = true;
    } catch (error) {
      logger.warn('Failed to load/create vision model, using fallback:', error);
      this.visionModel = null;
      this.modelLoaded = false;
    }
  }

  private async modelExists(modelPath: string): Promise<boolean> {
    try {
      const modelJsonPath = path.join(modelPath, 'model.json');
      await fs.access(modelJsonPath);
      return true;
    } catch {
      return false;
    }
  }

  private createSimpleVisionModel(): tf.LayersModel {
    const model = tf.sequential({
      layers: [
        tf.layers.conv2d({
          inputShape: [224, 224, 3],
          filters: 32,
          kernelSize: 3,
          activation: 'relu',
        }),
        tf.layers.maxPooling2d({ poolSize: 2 }),
        tf.layers.conv2d({ filters: 64, kernelSize: 3, activation: 'relu' }),
        tf.layers.maxPooling2d({ poolSize: 2 }),
        tf.layers.conv2d({ filters: 128, kernelSize: 3, activation: 'relu' }),
        tf.layers.globalAveragePooling2d(),
        tf.layers.dropout({ rate: 0.5 }),
        tf.layers.dense({ units: 128, activation: 'relu' }),
        tf.layers.dropout({ rate: 0.3 }),
        tf.layers.dense({ units: this.FIELD_TYPES.length, activation: 'softmax' }),
      ],
    });

    model.compile({
      optimizer: 'adam',
      loss: 'sparseCategoricalCrossentropy',
      metrics: ['accuracy'],
    });

    return model;
  }

  private async saveModel(modelPath: string): Promise<void> {
    try {
      if (this.visionModel) {
        await this.visionModel.save(`file://${modelPath}`);
        logger.info(`Model saved to ${modelPath}`);
      }
    } catch (error) {
      logger.error('Failed to save model:', error);
    }
  }

  async analyzeFields(
    screenshotPath: string,
    fieldBounds: FieldBounds[],
    semanticData?: Array<{ type?: string; confidence?: number }>
  ): Promise<FieldAnalysisResult[]> {
    const results: FieldAnalysisResult[] = [];

    for (let i = 0; i < fieldBounds.length; i++) {
      const bounds = fieldBounds[i];
      const semantic = semanticData?.[i];

      try {
        const result = await this.analyzeField(screenshotPath, bounds, i, semantic);
        results.push(result);
      } catch (error) {
        logger.error(`Failed to analyze field ${i}:`, error);
        results.push({
          fieldIndex: i,
          combinedType: 'text',
          combinedConfidence: 0.1,
          analysisMethod: 'semantic',
        });
      }
    }

    return results;
  }

  private async analyzeField(
    screenshotPath: string,
    bounds: FieldBounds,
    fieldIndex: number,
    semanticData?: { type?: string; confidence?: number }
  ): Promise<FieldAnalysisResult> {
    const result: FieldAnalysisResult = {
      fieldIndex,
      combinedType: 'text',
      combinedConfidence: 0.1,
      analysisMethod: 'semantic',
    };

    // Step 1: Use semantic data if available and confident
    if (semanticData?.type && semanticData.confidence && semanticData.confidence > 0.8) {
      result.semanticType = semanticData.type;
      result.combinedType = semanticData.type;
      result.combinedConfidence = semanticData.confidence;
      result.analysisMethod = 'semantic';
      return result;
    }

    // Step 2: OCR analysis for missing semantic data
    const ocrContext = await this.getOCRContext(screenshotPath, bounds);
    if (ocrContext) {
      result.ocrContext = ocrContext;
      
      const ocrBasedType = this.classifyFromOCRText(ocrContext.text);
      if (ocrBasedType.confidence > 0.6) {
        result.combinedType = ocrBasedType.type;
        result.combinedConfidence = ocrBasedType.confidence;
        result.analysisMethod = 'ocr';
        return result;
      }
    }

    // Step 3: Vision-based classification
    const visionResult = await this.getVisionClassification(screenshotPath, bounds);
    if (visionResult) {
      result.visionClassification = visionResult;
      
      if (visionResult.confidence > 0.5) {
        result.combinedType = visionResult.predictedType;
        result.combinedConfidence = visionResult.confidence;
        result.analysisMethod = 'vision';
        return result;
      }
    }

    // Step 4: Combine all available information
    const combinedResult = this.combineAnalyses(semanticData, ocrContext, visionResult);
    result.combinedType = combinedResult.type;
    result.combinedConfidence = combinedResult.confidence;
    result.analysisMethod = 'combined';

    return result;
  }

  private async getOCRContext(screenshotPath: string, bounds: FieldBounds): Promise<{ text: string; confidence: number } | null> {
    try {
      const ocr = getOCRInstance();
      const contextResults = await analyzeFieldContext(screenshotPath, [bounds]);
      
      if (contextResults.length > 0 && contextResults[0].confidence > 30) {
        return {
          text: contextResults[0].context,
          confidence: contextResults[0].confidence / 100, // Convert to 0-1 range
        };
      }
    } catch (error) {
      logger.warn('OCR context extraction failed:', error);
    }
    
    return null;
  }

  private classifyFromOCRText(text: string): { type: string; confidence: number } {
    const lowerText = text.toLowerCase();
    
    // Email patterns
    if (lowerText.includes('email') || lowerText.includes('e-mail') || lowerText.includes('@')) {
      return { type: 'email', confidence: 0.9 };
    }
    
    // Password patterns
    if (lowerText.includes('password') || lowerText.includes('passwd') || lowerText.includes('pwd')) {
      return { type: 'password', confidence: 0.9 };
    }
    
    // Search patterns
    if (lowerText.includes('search') || lowerText.includes('find') || lowerText.includes('query')) {
      return { type: 'search', confidence: 0.8 };
    }
    
    // Comment patterns
    if (lowerText.includes('comment') || lowerText.includes('message') || lowerText.includes('description')) {
      return { type: 'comment', confidence: 0.8 };
    }
    
    // Username patterns
    if (lowerText.includes('username') || lowerText.includes('user') || lowerText.includes('login')) {
      return { type: 'username', confidence: 0.8 };
    }
    
    // Name patterns
    if (lowerText.includes('name') || lowerText.includes('first name') || lowerText.includes('last name')) {
      return { type: 'name', confidence: 0.7 };
    }
    
    // Phone patterns
    if (lowerText.includes('phone') || lowerText.includes('tel') || lowerText.includes('mobile')) {
      return { type: 'phone', confidence: 0.7 };
    }
    
    return { type: 'text', confidence: 0.3 };
  }

  private async getVisionClassification(screenshotPath: string, bounds: FieldBounds): Promise<{
    predictedType: string;
    confidence: number;
    classProbabilities: Record<string, number>;
  } | null> {
    if (!this.modelLoaded || !this.visionModel) {
      return this.ruleBasedVisionClassification(screenshotPath, bounds);
    }

    try {
      // Extract and preprocess field image
      const fieldImageBuffer = await sharp(screenshotPath)
        .extract({
          left: Math.max(0, bounds.x - 10),
          top: Math.max(0, bounds.y - 10),
          width: bounds.width + 20,
          height: bounds.height + 20,
        })
        .resize(224, 224)
        .png()
        .toBuffer();

      // Convert to tensor
      const imageTensor = tf.node.decodeImage(fieldImageBuffer, 3)
        .expandDims(0)
        .div(255.0) as tf.Tensor4D;

      // Get predictions
      const predictions = this.visionModel.predict(imageTensor) as tf.Tensor;
      const probabilities = await predictions.data();

      // Find best prediction
      let maxIndex = 0;
      let maxProb = probabilities[0];
      for (let i = 1; i < probabilities.length; i++) {
        if (probabilities[i] > maxProb) {
          maxProb = probabilities[i];
          maxIndex = i;
        }
      }

      // Build class probabilities
      const classProbabilities: Record<string, number> = {};
      for (let i = 0; i < this.FIELD_TYPES.length; i++) {
        classProbabilities[this.FIELD_TYPES[i]] = probabilities[i];
      }

      // Cleanup tensors
      imageTensor.dispose();
      predictions.dispose();

      return {
        predictedType: this.FIELD_TYPES[maxIndex],
        confidence: maxProb,
        classProbabilities,
      };

    } catch (error) {
      logger.warn('Vision classification failed, using rule-based fallback:', error);
      return this.ruleBasedVisionClassification(screenshotPath, bounds);
    }
  }

  private async ruleBasedVisionClassification(screenshotPath: string, bounds: FieldBounds): Promise<{
    predictedType: string;
    confidence: number;
    classProbabilities: Record<string, number>;
  }> {
    const aspectRatio = bounds.width / bounds.height;
    
    // Rule-based classification based on field dimensions
    let predictedType = 'text';
    let confidence = 0.4;
    
    if (bounds.height > 100 && aspectRatio > 2) {
      predictedType = 'comment';
      confidence = 0.6;
    } else if (aspectRatio > 4 && bounds.height < 40) {
      predictedType = 'search';
      confidence = 0.5;
    } else if (aspectRatio < 1.5 && bounds.width < 100 && bounds.height < 50) {
      predictedType = 'button';
      confidence = 0.5;
    }
    
    const classProbabilities: Record<string, number> = {};
    this.FIELD_TYPES.forEach(type => {
      classProbabilities[type] = type === predictedType ? confidence : 0.1;
    });
    
    return { predictedType, confidence, classProbabilities };
  }

  private combineAnalyses(
    semanticData?: { type?: string; confidence?: number },
    ocrContext?: { text: string; confidence: number } | null,
    visionResult?: { predictedType: string; confidence: number } | null
  ): { type: string; confidence: number } {
    const scores: Record<string, number> = {};
    
    // Add semantic score
    if (semanticData?.type && semanticData.confidence) {
      scores[semanticData.type] = (scores[semanticData.type] || 0) + semanticData.confidence * 0.5;
    }
    
    // Add OCR score
    if (ocrContext) {
      const ocrType = this.classifyFromOCRText(ocrContext.text);
      scores[ocrType.type] = (scores[ocrType.type] || 0) + ocrType.confidence * 0.3;
    }
    
    // Add vision score
    if (visionResult) {
      scores[visionResult.predictedType] = (scores[visionResult.predictedType] || 0) + visionResult.confidence * 0.2;
    }
    
    // Find the type with highest combined score
    let bestType = 'text';
    let bestScore = 0;
    
    for (const [type, score] of Object.entries(scores)) {
      if (score > bestScore) {
        bestScore = score;
        bestType = type;
      }
    }
    
    return { type: bestType, confidence: Math.min(bestScore, 1.0) };
  }

  async dispose(): Promise<void> {
    if (this.visionModel) {
      this.visionModel.dispose();
      this.visionModel = null;
      this.modelLoaded = false;
    }
    
    const ocr = getOCRInstance();
    await ocr.terminate();
    
    logger.info('Field analyzer disposed');
  }
}

// Singleton instance
let analyzerInstance: FieldAnalyzer | null = null;

export function getFieldAnalyzer(): FieldAnalyzer {
  if (!analyzerInstance) {
    analyzerInstance = new FieldAnalyzer();
  }
  return analyzerInstance;
}
