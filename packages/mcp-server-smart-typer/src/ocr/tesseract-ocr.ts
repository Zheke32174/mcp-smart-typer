/**
 * OCR module using Tesseract.js for Node.js screenshot text extraction
 */

import { createWorker, Worker } from 'tesseract.js';
import sharp from 'sharp';
import { logger } from '../utils/logger.js';

export interface OCRResult {
  text: string;
  confidence: number;
  words: Array<{
    text: string;
    confidence: number;
    bbox: {
      x0: number;
      y0: number;
      x1: number;
      y1: number;
    };
  }>;
  blocks: Array<{
    text: string;
    confidence: number;
    bbox: {
      x0: number;
      y0: number;
      x1: number;
      y1: number;
    };
  }>;
}

export interface OCRRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

export class TesseractOCR {
  private worker: Worker | null = null;
  private initialized = false;

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      logger.info('Initializing Tesseract OCR worker...');
      this.worker = await createWorker('eng');

      // Configure for better field detection
      await this.worker.setParameters({
        tessedit_char_whitelist:
          '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@._-+()[]{}:;,?!/\\|"\'`~#$%^&*=<> ',
        tessedit_pageseg_mode: '6', // Uniform block of text
      });

      this.initialized = true;
      logger.info('Tesseract OCR worker initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Tesseract OCR worker:', error);
      throw error;
    }
  }

  async extractText(imagePath: string, region?: OCRRegion): Promise<OCRResult> {
    if (!this.worker) {
      await this.initialize();
    }

    try {
      let imageBuffer: Buffer;

      if (region) {
        // Crop image to region if specified
        imageBuffer = await sharp(imagePath)
          .extract({
            left: region.x,
            top: region.y,
            width: region.width,
            height: region.height,
          })
          .png()
          .toBuffer();
      } else {
        // Process full image
        imageBuffer = await sharp(imagePath).png().toBuffer();
      }

      // Enhance image for better OCR
      const enhancedBuffer = await sharp(imageBuffer)
        .resize({ width: 800 }) // Scale up for better recognition
        .sharpen()
        .normalize()
        .toBuffer();

      const result = await this.worker!.recognize(enhancedBuffer);

      return {
        text: result.data.text.trim(),
        confidence: result.data.confidence,
        words: result.data.words.map(word => ({
          text: word.text,
          confidence: word.confidence,
          bbox: word.bbox,
        })),
        blocks: result.data.blocks.map(block => ({
          text: block.text,
          confidence: block.confidence,
          bbox: block.bbox,
        })),
      };
    } catch (error) {
      logger.error('OCR text extraction failed:', error);
      return {
        text: '',
        confidence: 0,
        words: [],
        blocks: [],
      };
    }
  }

  async findTextNearFields(
    imagePath: string,
    fieldBounds: Array<{
      x: number;
      y: number;
      width: number;
      height: number;
    }>
  ): Promise<Array<{ fieldIndex: number; nearbyText: string; confidence: number }>> {
    const results: Array<{ fieldIndex: number; nearbyText: string; confidence: number }> = [];

    for (let i = 0; i < fieldBounds.length; i++) {
      const field = fieldBounds[i];

      // Define search region around the field (expand by 100px in each direction)
      const searchRegion: OCRRegion = {
        x: Math.max(0, field.x - 100),
        y: Math.max(0, field.y - 100),
        width: field.width + 200,
        height: field.height + 200,
      };

      try {
        const ocrResult = await this.extractText(imagePath, searchRegion);

        if (ocrResult.text && ocrResult.confidence > 30) {
          results.push({
            fieldIndex: i,
            nearbyText: ocrResult.text,
            confidence: ocrResult.confidence,
          });
        }
      } catch (error) {
        logger.warn(`Failed to extract text near field ${i}:`, error);
      }
    }

    return results;
  }

  async terminate(): Promise<void> {
    if (this.worker) {
      await this.worker.terminate();
      this.worker = null;
      this.initialized = false;
      logger.info('Tesseract OCR worker terminated');
    }
  }
}

// Singleton instance
let ocrInstance: TesseractOCR | null = null;

export function getOCRInstance(): TesseractOCR {
  if (!ocrInstance) {
    ocrInstance = new TesseractOCR();
  }
  return ocrInstance;
}

export async function analyzeFieldContext(
  imagePath: string,
  fieldBounds: Array<{ x: number; y: number; width: number; height: number }>
): Promise<Array<{ fieldIndex: number; context: string; confidence: number }>> {
  const ocr = getOCRInstance();
  const nearbyTexts = await ocr.findTextNearFields(imagePath, fieldBounds);

  return nearbyTexts.map(result => ({
    fieldIndex: result.fieldIndex,
    context: result.nearbyText,
    confidence: result.confidence,
  }));
}
