"""
Vision-based field classifier using CNN/ViT models for form field type classification
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    import tensorflow as tf
except ImportError:  # Optional accelerator; rule-based fallback remains available.
    tf = None
from PIL import Image

logger = logging.getLogger(__name__)


class VisionFieldClassifier:
    """Vision-based classifier for form field types using CNN/ViT models."""

    FIELD_TYPES = [
        "email",
        "password",
        "search",
        "comment",
        "username",
        "name",
        "phone",
        "text",
        "button",
        "checkbox",
    ]

    def __init__(self, model_cache_dir: str = None):
        """Initialize vision classifier.

        Args:
            model_cache_dir: Directory to cache model weights
        """
        self.model_cache_dir = model_cache_dir or os.path.join(
            os.path.expanduser("~"), ".mcp-smart-typer", "models"
        )
        os.makedirs(self.model_cache_dir, exist_ok=True)

        self.model = None
        self.is_loaded = False
        self.input_size = (224, 224)  # Standard input size for vision models

    def _create_cnn_model(self) -> Any:
        """Create a simple CNN model for field classification.

        Returns:
            Compiled CNN model
        """
        model = tf.keras.Sequential(
            [
                # Convolutional layers
                tf.keras.layers.Conv2D(
                    32, (3, 3), activation="relu", input_shape=(*self.input_size, 3)
                ),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation="relu"),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(128, (3, 3), activation="relu"),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(128, (3, 3), activation="relu"),
                tf.keras.layers.MaxPooling2D((2, 2)),
                # Dense layers
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dropout(0.5),
                tf.keras.layers.Dense(512, activation="relu"),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(len(self.FIELD_TYPES), activation="softmax"),
            ]
        )

        model.compile(
            optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
        )

        return model

    def _create_vision_transformer(self) -> Any:
        """Create a simplified Vision Transformer model.

        Returns:
            Compiled ViT model
        """
        # For simplicity, we'll use a pre-trained MobileNetV2 as base
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(*self.input_size, 3), include_top=False, weights="imagenet"
        )

        # Freeze base model layers
        base_model.trainable = False

        model = tf.keras.Sequential(
            [
                base_model,
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(len(self.FIELD_TYPES), activation="softmax"),
            ]
        )

        model.compile(
            optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
        )

        return model

    def _load_cached_model(self) -> Optional[tf.keras.Model]:
        """Load cached model from disk.

        Returns:
            Loaded model or None if not found
        """
        model_path = os.path.join(self.model_cache_dir, "field_classifier.h5")

        if os.path.exists(model_path):
            try:
                logger.info(f"Loading cached model from {model_path}")
                model = tf.keras.models.load_model(model_path)
                return model
            except Exception as e:
                logger.warning(f"Failed to load cached model: {e}")

        return None

    def _save_model(self, model: Any):
        """Save model to cache directory.

        Args:
            model: Model to save
        """
        try:
            model_path = os.path.join(self.model_cache_dir, "field_classifier.h5")
            model.save(model_path)
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def initialize_model(self, use_pretrained: bool = True):
        """Initialize or load the classification model.

        Args:
            use_pretrained: Whether to use pre-trained weights
        """
        if self.is_loaded:
            return

        if tf is None:
            logger.info("TensorFlow unavailable; using rule-based field classification")
            self.model = None
            self.is_loaded = False
            return

        try:
            # Try to load cached model first
            self.model = self._load_cached_model()

            if self.model is None:
                logger.info("Creating new vision model...")
                if use_pretrained:
                    self.model = self._create_vision_transformer()
                else:
                    self.model = self._create_cnn_model()

                # Create some synthetic training data for basic functionality
                self._create_basic_training_data()

                # Save the initialized model
                self._save_model(self.model)

            self.is_loaded = True
            logger.info("Vision classifier model initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize vision model: {e}")
            # Fall back to simple rule-based classification
            self.model = None
            self.is_loaded = False

    def _create_basic_training_data(self):
        """Create basic synthetic training data for model initialization."""
        try:
            # Generate synthetic training data
            X_train = np.random.random((100, *self.input_size, 3))
            y_train = np.random.randint(0, len(self.FIELD_TYPES), 100)

            # Train for a few epochs just to initialize weights properly
            self.model.fit(X_train, y_train, epochs=1, verbose=0)

            logger.info("Basic training data created and model initialized")

        except Exception as e:
            logger.error(f"Failed to create basic training data: {e}")

    def preprocess_field_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess field image for model input.

        Args:
            image: Input image as numpy array

        Returns:
            Preprocessed image
        """
        # Resize to model input size
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        # Resize
        resized = cv2.resize(image_rgb, self.input_size)

        # Normalize pixel values
        normalized = resized.astype(np.float32) / 255.0

        return normalized

    def classify_field(self, image_path: str, field_bounds: Dict[str, int]) -> Dict[str, Any]:
        """Classify a single field type from screenshot.

        Args:
            image_path: Path to screenshot image
            field_bounds: Field bounding box dictionary

        Returns:
            Classification results
        """
        try:
            # Load and crop image to field region
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")

            # Add padding around field for context
            padding = 20
            x = max(0, field_bounds["x"] - padding)
            y = max(0, field_bounds["y"] - padding)
            w = min(image.shape[1] - x, field_bounds["width"] + 2 * padding)
            h = min(image.shape[0] - y, field_bounds["height"] + 2 * padding)

            field_image = image[y : y + h, x : x + w]

            # Preprocess image
            processed_image = self.preprocess_field_image(field_image)

            if self.model is not None and self.is_loaded:
                # Use ML model for classification
                input_batch = np.expand_dims(processed_image, axis=0)
                predictions = self.model.predict(input_batch, verbose=0)

                predicted_class = np.argmax(predictions[0])
                confidence = float(predictions[0][predicted_class])
                predicted_type = self.FIELD_TYPES[predicted_class]

                # Get all class probabilities
                class_probabilities = {
                    self.FIELD_TYPES[i]: float(predictions[0][i])
                    for i in range(len(self.FIELD_TYPES))
                }

            else:
                # Fall back to rule-based classification based on visual features
                predicted_type, confidence = self._rule_based_classification(field_image)
                class_probabilities = {predicted_type: confidence}

            return {
                "predicted_type": predicted_type,
                "confidence": confidence,
                "class_probabilities": class_probabilities,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Field classification failed: {e}")
            return {
                "predicted_type": "text",
                "confidence": 0.1,
                "class_probabilities": {"text": 0.1},
                "success": False,
                "error": str(e),
            }

    def _rule_based_classification(self, field_image: np.ndarray) -> Tuple[str, float]:
        """Rule-based fallback classification based on visual features.

        Args:
            field_image: Field image as numpy array

        Returns:
            Tuple of (predicted_type, confidence)
        """
        height, width = field_image.shape[:2]
        aspect_ratio = width / height if height > 0 else 1

        # Analyze image properties
        gray = (
            cv2.cvtColor(field_image, cv2.COLOR_BGR2GRAY)
            if len(field_image.shape) == 3
            else field_image
        )

        # Check if field is likely a button (high contrast, rectangular)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            contour_aspect_ratio = w / h if h > 0 else 1

            # Button-like characteristics
            if contour_aspect_ratio > 2 and cv2.contourArea(largest_contour) > (
                width * height * 0.3
            ):
                return "button", 0.7

        # Check for password field characteristics (stars, dots, or solid fill)
        unique_pixels = len(np.unique(gray))
        if unique_pixels < 10 and aspect_ratio > 3:  # Few unique values, wide field
            return "password", 0.6

        # Large text areas (comments)
        if height > 100 and aspect_ratio > 2:
            return "comment", 0.6
        elif height > 60 and aspect_ratio > 3:
            return "comment", 0.5

        # Search fields tend to be wide and single-line
        if aspect_ratio > 4 and height < 50:
            return "search", 0.5

        # Default to text input
        return "text", 0.4

    def classify_multiple_fields(
        self, image_path: str, field_bounds_list: List[Dict[str, int]]
    ) -> List[Dict[str, Any]]:
        """Classify multiple fields from a screenshot.

        Args:
            image_path: Path to screenshot image
            field_bounds_list: List of field bounding boxes

        Returns:
            List of classification results
        """
        results = []

        for i, field_bounds in enumerate(field_bounds_list):
            try:
                classification = self.classify_field(image_path, field_bounds)
                classification["field_index"] = i
                results.append(classification)

            except Exception as e:
                logger.error(f"Failed to classify field {i}: {e}")
                results.append(
                    {
                        "field_index": i,
                        "predicted_type": "text",
                        "confidence": 0.1,
                        "class_probabilities": {"text": 0.1},
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def update_model_with_feedback(
        self,
        image_path: str,
        field_bounds: Dict[str, int],
        correct_type: str,
        confidence_threshold: float = 0.8,
    ):
        """Update model with user feedback (for future enhancement).

        Args:
            image_path: Path to screenshot image
            field_bounds: Field bounding box
            correct_type: Correct field type
            confidence_threshold: Minimum confidence to trigger update
        """
        # This would be implemented for online learning in a production system
        # For now, we'll just log the feedback
        logger.info(f"Feedback received: field type should be '{correct_type}'")


# Global classifier instance
_vision_classifier = None


def get_vision_classifier() -> VisionFieldClassifier:
    """Get singleton vision classifier instance."""
    global _vision_classifier
    if _vision_classifier is None:
        _vision_classifier = VisionFieldClassifier()
        _vision_classifier.initialize_model()
    return _vision_classifier
