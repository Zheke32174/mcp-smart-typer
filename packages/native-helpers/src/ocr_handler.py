"""
OCR Handler using pytesseract for text extraction from screenshots
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRHandler:
    """Handles OCR text extraction from screenshots using pytesseract."""

    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize OCR handler.

        Args:
            tesseract_path: Path to tesseract executable (optional)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results.

        Args:
            image: Input image as numpy array

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Apply morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Resize for better recognition (scale up small text)
        height, width = opening.shape
        if height < 100 or width < 100:
            scale_factor = max(2, 200 // min(height, width))
            opening = cv2.resize(
                opening, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC
            )

        return opening

    def extract_text(
        self, image_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """Extract text from image using OCR.

        Args:
            image_path: Path to image file
            region: Optional region tuple (x, y, width, height)

        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")

            # Crop to region if specified
            if region:
                x, y, w, h = region
                image = image[y : y + h, x : x + w]

            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Convert to PIL Image for tesseract
            pil_image = Image.fromarray(processed_image)

            # Configure tesseract for form field detection
            config = "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@._-+()[]{}:;,?!/\\|\"'`~#$%^&*=<> "

            # Extract text
            text = pytesseract.image_to_string(pil_image, config=config)

            # Get detailed data
            data = pytesseract.image_to_data(
                pil_image, config=config, output_type=pytesseract.Output.DICT
            )

            # Calculate confidence
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Extract word-level information
            words = []
            for i in range(len(data["text"])):
                if int(data["conf"][i]) > 30:  # Filter low-confidence words
                    words.append(
                        {
                            "text": data["text"][i],
                            "confidence": int(data["conf"][i]),
                            "bbox": {
                                "x": int(data["left"][i]),
                                "y": int(data["top"][i]),
                                "width": int(data["width"][i]),
                                "height": int(data["height"][i]),
                            },
                        }
                    )

            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "words": words,
                "success": True,
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {"text": "", "confidence": 0, "words": [], "success": False, "error": str(e)}

    def find_text_near_fields(
        self, image_path: str, field_bounds: List[Dict[str, int]]
    ) -> List[Dict[str, Any]]:
        """Find text near form fields for context analysis.

        Args:
            image_path: Path to screenshot image
            field_bounds: List of field bounding boxes

        Returns:
            List of text contexts found near each field
        """
        results = []

        for i, field in enumerate(field_bounds):
            try:
                # Expand search region around field
                padding = 100
                x = max(0, field["x"] - padding)
                y = max(0, field["y"] - padding)
                w = field["width"] + 2 * padding
                h = field["height"] + 2 * padding

                # Extract text from expanded region
                ocr_result = self.extract_text(image_path, (x, y, w, h))

                if ocr_result["success"] and ocr_result["text"] and ocr_result["confidence"] > 30:
                    results.append(
                        {
                            "field_index": i,
                            "nearby_text": ocr_result["text"],
                            "confidence": ocr_result["confidence"],
                            "words": ocr_result["words"],
                        }
                    )
                else:
                    results.append(
                        {"field_index": i, "nearby_text": "", "confidence": 0, "words": []}
                    )

            except Exception as e:
                logger.warning(f"Failed to extract text near field {i}: {e}")
                results.append(
                    {
                        "field_index": i,
                        "nearby_text": "",
                        "confidence": 0,
                        "words": [],
                        "error": str(e),
                    }
                )

        return results

    def analyze_field_labels(
        self, image_path: str, field_bounds: List[Dict[str, int]]
    ) -> List[Dict[str, Any]]:
        """Analyze text labels associated with form fields.

        Args:
            image_path: Path to screenshot image
            field_bounds: List of field bounding boxes

        Returns:
            List of analyzed labels for each field
        """
        nearby_texts = self.find_text_near_fields(image_path, field_bounds)
        analyzed_labels = []

        for text_data in nearby_texts:
            field_type = self._classify_field_from_text(text_data["nearby_text"])

            analyzed_labels.append(
                {
                    "field_index": text_data["field_index"],
                    "detected_text": text_data["nearby_text"],
                    "confidence": text_data["confidence"],
                    "predicted_type": field_type,
                    "words": text_data["words"],
                }
            )

        return analyzed_labels

    def _classify_field_from_text(self, text: str) -> str:
        """Classify field type based on nearby text.

        Args:
            text: Text found near the field

        Returns:
            Predicted field type
        """
        text_lower = text.lower()

        # Email field patterns
        if any(keyword in text_lower for keyword in ["email", "e-mail", "@", "mail"]):
            return "email"

        # Password field patterns
        if any(keyword in text_lower for keyword in ["password", "passwd", "pwd", "pass"]):
            return "password"

        # Search field patterns
        if any(keyword in text_lower for keyword in ["search", "find", "query", "lookup"]):
            return "search"

        # Comment/textarea patterns
        if any(
            keyword in text_lower
            for keyword in ["comment", "message", "description", "note", "feedback", "review"]
        ):
            return "comment"

        # Username field patterns
        if any(keyword in text_lower for keyword in ["username", "user", "login", "account"]):
            return "username"

        # Name field patterns
        if any(
            keyword in text_lower for keyword in ["name", "first name", "last name", "full name"]
        ):
            return "name"

        # Phone field patterns
        if any(keyword in text_lower for keyword in ["phone", "tel", "mobile", "number"]):
            return "phone"

        # Default to text
        return "text"


# Global OCR handler instance
_ocr_handler = None


def get_ocr_handler() -> OCRHandler:
    """Get singleton OCR handler instance."""
    global _ocr_handler
    if _ocr_handler is None:
        _ocr_handler = OCRHandler()
    return _ocr_handler
