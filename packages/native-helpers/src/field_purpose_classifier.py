"""
Advanced Field Purpose Classifier

Combines features from DOM/UIA attributes, neighboring OCR text, placeholder, 
and model predictions using LightGBM classifier with rule-based fallbacks.
"""

import json
import logging
import os
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pandas as pd
from PIL import Image

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM not available, using gradient boosting fallback")

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available, using rule-based classification only")

from ocr_handler import OCRHandler
from vision_classifier import get_vision_classifier

logger = logging.getLogger(__name__)


@dataclass
class FieldInfo:
    """Field information structure."""

    # DOM/UIA attributes
    tag_name: Optional[str] = None
    element_type: Optional[str] = None
    name: Optional[str] = None
    id: Optional[str] = None
    class_name: Optional[str] = None
    placeholder: Optional[str] = None
    aria_label: Optional[str] = None
    title: Optional[str] = None
    autocomplete: Optional[str] = None

    # Visual attributes
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    # Text context
    label_text: Optional[str] = None
    neighboring_text: Optional[str] = None
    parent_text: Optional[str] = None

    # Model predictions
    vision_prediction: Optional[Dict[str, Any]] = None
    ocr_confidence: float = 0.0


@dataclass
class ClassificationResult:
    """Classification result with confidence score."""

    predicted_type: str
    confidence: float
    method_used: str
    all_probabilities: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None


class FieldPurposeClassifier:
    """Advanced field purpose classifier using multiple feature sources."""

    # Standard field types
    FIELD_TYPES = [
        "email",
        "password",
        "search",
        "username",
        "name",
        "firstname",
        "lastname",
        "phone",
        "address",
        "city",
        "state",
        "zipcode",
        "country",
        "comment",
        "message",
        "description",
        "text",
        "number",
        "date",
        "time",
        "url",
        "file",
        "checkbox",
        "radio",
        "select",
        "button",
        "submit",
    ]

    def __init__(self, model_cache_dir: Optional[str] = None):
        """Initialize the field purpose classifier."""
        self.model_cache_dir = Path(
            model_cache_dir or os.path.join(os.path.expanduser("~"), ".mcp-smart-typer", "models")
        )
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.lgb_model = None
        self.gb_model = None
        self.label_encoder = None
        self.tfidf_vectorizer = None
        self.feature_names = []
        self.is_trained = False

        # Rule-based patterns
        self._compile_patterns()

        # Initialize external classifiers
        self.vision_classifier = get_vision_classifier()
        self.ocr_handler = OCRHandler()

        # Load pre-trained model if available
        self._load_model()

    def _compile_patterns(self):
        """Compile regex patterns for rule-based classification."""
        self.patterns = {
            "email": [r"(?i)e.?mail", r"(?i)email", r"@", r"(?i)login.?email", r"(?i)user.?email"],
            "password": [
                r"(?i)password",
                r"(?i)passwd",
                r"(?i)pwd",
                r"(?i)pass",
                r"(?i)secret",
                r"(?i)pin",
            ],
            "username": [
                r"(?i)username",
                r"(?i)user.?name",
                r"(?i)login",
                r"(?i)userid",
                r"(?i)account",
            ],
            "search": [r"(?i)search", r"(?i)find", r"(?i)query", r"(?i)filter", r"(?i)lookup"],
            "name": [r"(?i)^name$", r"(?i)full.?name", r"(?i)your.?name", r"(?i)display.?name"],
            "firstname": [r"(?i)first.?name", r"(?i)fname", r"(?i)given.?name", r"(?i)forename"],
            "lastname": [r"(?i)last.?name", r"(?i)lname", r"(?i)surname", r"(?i)family.?name"],
            "phone": [r"(?i)phone", r"(?i)tel", r"(?i)mobile", r"(?i)cell", r"(?i)contact.?number"],
            "address": [r"(?i)address", r"(?i)street", r"(?i)location", r"(?i)residence"],
            "city": [r"(?i)city", r"(?i)town", r"(?i)municipality"],
            "state": [r"(?i)state", r"(?i)province", r"(?i)region"],
            "zipcode": [r"(?i)zip", r"(?i)postal", r"(?i)post.?code", r"(?i)zip.?code"],
            "country": [r"(?i)country", r"(?i)nation", r"(?i)nationality"],
            "comment": [
                r"(?i)comment",
                r"(?i)message",
                r"(?i)note",
                r"(?i)feedback",
                r"(?i)review",
            ],
            "description": [r"(?i)description", r"(?i)desc", r"(?i)detail", r"(?i)summary"],
            "date": [r"(?i)date", r"(?i)birthday", r"(?i)birth.?date", r"(?i)dob"],
            "time": [r"(?i)time", r"(?i)hour", r"(?i)minute"],
            "url": [r"(?i)url", r"(?i)website", r"(?i)link", r"(?i)http"],
            "number": [r"(?i)number", r"(?i)num", r"(?i)quantity", r"(?i)amount"],
        }

        # Compile patterns for performance
        self.compiled_patterns = {}
        for field_type, patterns in self.patterns.items():
            self.compiled_patterns[field_type] = [re.compile(p) for p in patterns]

    def extract_features(self, field_info: FieldInfo) -> Dict[str, Any]:
        """Extract comprehensive features from field information."""
        features = {}

        # Basic DOM/UIA features
        features["has_name"] = 1 if field_info.name else 0
        features["has_id"] = 1 if field_info.id else 0
        features["has_class"] = 1 if field_info.class_name else 0
        features["has_placeholder"] = 1 if field_info.placeholder else 0
        features["has_aria_label"] = 1 if field_info.aria_label else 0
        features["has_title"] = 1 if field_info.title else 0
        features["has_autocomplete"] = 1 if field_info.autocomplete else 0

        # Visual features
        features["width"] = field_info.width
        features["height"] = field_info.height
        features["aspect_ratio"] = field_info.width / max(field_info.height, 1)
        features["area"] = field_info.width * field_info.height

        # Size categories
        features["is_small"] = 1 if field_info.area < 5000 else 0
        features["is_large"] = 1 if field_info.area > 50000 else 0
        features["is_wide"] = 1 if features["aspect_ratio"] > 4 else 0
        features["is_tall"] = 1 if features["aspect_ratio"] < 0.5 else 0

        # Text-based features
        all_text = self._combine_text_fields(field_info)

        # Pattern matching features
        for field_type, patterns in self.compiled_patterns.items():
            feature_name = f"pattern_{field_type}"
            features[feature_name] = self._match_patterns(all_text, patterns)

        # Text length and characteristics
        features["text_length"] = len(all_text)
        features["has_uppercase"] = 1 if any(c.isupper() for c in all_text) else 0
        features["has_lowercase"] = 1 if any(c.islower() for c in all_text) else 0
        features["has_digits"] = 1 if any(c.isdigit() for c in all_text) else 0
        features["has_special_chars"] = (
            1 if any(not c.isalnum() and not c.isspace() for c in all_text) else 0
        )

        # Element type features (one-hot encoding)
        element_types = ["input", "textarea", "select", "button", "checkbox", "radio"]
        for elem_type in element_types:
            features[f"element_{elem_type}"] = 1 if field_info.element_type == elem_type else 0

        # Input type features (if available)
        input_types = [
            "text",
            "email",
            "password",
            "search",
            "tel",
            "url",
            "number",
            "date",
            "time",
        ]
        for input_type in input_types:
            features[f"input_{input_type}"] = 1 if field_info.element_type == input_type else 0

        # Vision model features (if available)
        if field_info.vision_prediction:
            vision_pred = field_info.vision_prediction
            features["vision_confidence"] = vision_pred.get("confidence", 0)

            # Top prediction features
            for field_type in self.FIELD_TYPES:
                prob_key = f"vision_prob_{field_type}"
                features[prob_key] = vision_pred.get("class_probabilities", {}).get(field_type, 0)
        else:
            features["vision_confidence"] = 0
            for field_type in self.FIELD_TYPES:
                features[f"vision_prob_{field_type}"] = 0

        # OCR confidence
        features["ocr_confidence"] = field_info.ocr_confidence

        # Autocomplete attribute parsing
        if field_info.autocomplete:
            autocomplete_tokens = field_info.autocomplete.lower().split()
            common_autocomplete = [
                "name",
                "email",
                "username",
                "password",
                "tel",
                "address",
                "postal-code",
            ]
            for token in common_autocomplete:
                features[f"autocomplete_{token}"] = 1 if token in autocomplete_tokens else 0
        else:
            for token in ["name", "email", "username", "password", "tel", "address", "postal-code"]:
                features[f"autocomplete_{token}"] = 0

        return features

    def _combine_text_fields(self, field_info: FieldInfo) -> str:
        """Combine all text fields into a single string for analysis."""
        text_parts = []

        if field_info.name:
            text_parts.append(field_info.name)
        if field_info.id:
            text_parts.append(field_info.id)
        if field_info.class_name:
            text_parts.append(field_info.class_name)
        if field_info.placeholder:
            text_parts.append(field_info.placeholder)
        if field_info.aria_label:
            text_parts.append(field_info.aria_label)
        if field_info.title:
            text_parts.append(field_info.title)
        if field_info.label_text:
            text_parts.append(field_info.label_text)
        if field_info.neighboring_text:
            text_parts.append(field_info.neighboring_text)
        if field_info.parent_text:
            text_parts.append(field_info.parent_text)

        return " ".join(text_parts).lower()

    def _match_patterns(self, text: str, patterns: List[re.Pattern]) -> float:
        """Match patterns against text and return confidence score."""
        if not text:
            return 0.0

        matches = 0
        total_patterns = len(patterns)

        for pattern in patterns:
            if pattern.search(text):
                matches += 1

        return matches / total_patterns if total_patterns > 0 else 0.0

    def _rule_based_classification(self, field_info: FieldInfo) -> ClassificationResult:
        """Rule-based classification as fallback."""
        all_text = self._combine_text_fields(field_info)
        scores = {}

        # Pattern matching
        for field_type, patterns in self.compiled_patterns.items():
            scores[field_type] = self._match_patterns(all_text, patterns)

        # Visual heuristics
        aspect_ratio = field_info.width / max(field_info.height, 1)
        area = field_info.width * field_info.height

        # Button detection
        if field_info.element_type == "button" or (
            aspect_ratio < 3 and area < 10000 and field_info.height < 50
        ):
            if "submit" in all_text or "send" in all_text or "login" in all_text:
                scores["submit"] = max(scores.get("submit", 0), 0.8)
            else:
                scores["button"] = max(scores.get("button", 0), 0.7)

        # Large text area detection
        if field_info.element_type == "textarea" or (field_info.height > 100 and aspect_ratio > 2):
            if "comment" in all_text or "message" in all_text:
                scores["comment"] = max(scores.get("comment", 0), 0.8)
            else:
                scores["description"] = max(scores.get("description", 0), 0.6)

        # Search field detection
        if aspect_ratio > 4 and field_info.height < 50:
            if any(term in all_text for term in ["search", "find", "query"]):
                scores["search"] = max(scores.get("search", 0), 0.8)

        # Password field detection (visual cues)
        if field_info.element_type == "password" or "password" in all_text:
            scores["password"] = max(scores.get("password", 0), 0.9)

        # Email field detection
        if field_info.element_type == "email" or "@" in all_text or "email" in all_text:
            scores["email"] = max(scores.get("email", 0), 0.9)

        # Find best match
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            predicted_type = best_type[0]
            confidence = best_type[1]
        else:
            predicted_type = "text"
            confidence = 0.1
            scores["text"] = 0.1

        # Ensure minimum confidence for prediction
        if confidence < 0.3:
            predicted_type = "text"
            confidence = 0.1
            scores["text"] = 0.1

        return ClassificationResult(
            predicted_type=predicted_type,
            confidence=confidence,
            method_used="rule_based",
            all_probabilities=scores,
        )

    def _train_synthetic_model(self):
        """Train model with synthetic data for basic functionality."""
        logger.info("Training synthetic model for initialization...")

        # Generate synthetic training data
        synthetic_data = self._generate_synthetic_training_data()

        if not synthetic_data:
            logger.warning("No synthetic data generated")
            return

        features_df = pd.DataFrame([d["features"] for d in synthetic_data])
        labels = [d["label"] for d in synthetic_data]

        # Initialize label encoder
        self.label_encoder = LabelEncoder()
        encoded_labels = self.label_encoder.fit_transform(labels)

        self.feature_names = list(features_df.columns)

        # Train model
        if LIGHTGBM_AVAILABLE:
            train_data = lgb.Dataset(features_df, label=encoded_labels)
            params = {
                "objective": "multiclass",
                "num_class": len(self.FIELD_TYPES),
                "metric": "multi_logloss",
                "boosting_type": "gbdt",
                "num_leaves": 31,
                "learning_rate": 0.05,
                "feature_fraction": 0.9,
                "bagging_fraction": 0.8,
                "bagging_freq": 5,
                "verbose": -1,
            }

            self.lgb_model = lgb.train(
                params,
                train_data,
                num_boost_round=100,
                valid_sets=[train_data],
                callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)],
            )

        elif SKLEARN_AVAILABLE:
            self.gb_model = GradientBoostingClassifier(
                n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42
            )
            self.gb_model.fit(features_df, encoded_labels)

        self.is_trained = True
        logger.info("Synthetic model training completed")

        # Save model
        self._save_model()

    def _generate_synthetic_training_data(self) -> List[Dict[str, Any]]:
        """Generate synthetic training data based on common patterns."""
        synthetic_data = []

        # Email field examples
        email_examples = [
            {"name": "email", "placeholder": "Enter your email", "element_type": "email"},
            {"id": "user_email", "aria_label": "Email address", "element_type": "input"},
            {"class_name": "email-input", "label_text": "E-mail", "element_type": "input"},
        ]

        for example in email_examples:
            field_info = FieldInfo(**example, width=300, height=40)
            features = self.extract_features(field_info)
            synthetic_data.append({"features": features, "label": "email"})

        # Password field examples
        password_examples = [
            {"name": "password", "placeholder": "Password", "element_type": "password"},
            {"id": "user_pwd", "aria_label": "Enter password", "element_type": "password"},
            {"class_name": "password-field", "label_text": "Password", "element_type": "input"},
        ]

        for example in password_examples:
            field_info = FieldInfo(**example, width=300, height=40)
            features = self.extract_features(field_info)
            synthetic_data.append({"features": features, "label": "password"})

        # Search field examples
        search_examples = [
            {"name": "search", "placeholder": "Search...", "element_type": "search"},
            {"id": "search_box", "aria_label": "Search", "element_type": "input"},
            {"class_name": "search-input", "label_text": "Find", "element_type": "input"},
        ]

        for example in search_examples:
            field_info = FieldInfo(**example, width=400, height=35)
            features = self.extract_features(field_info)
            synthetic_data.append({"features": features, "label": "search"})

        # Comment field examples
        comment_examples = [
            {"name": "comment", "placeholder": "Enter your comment", "element_type": "textarea"},
            {"id": "message_box", "aria_label": "Message", "element_type": "textarea"},
            {"class_name": "comment-area", "label_text": "Comments", "element_type": "textarea"},
        ]

        for example in comment_examples:
            field_info = FieldInfo(**example, width=400, height=120)
            features = self.extract_features(field_info)
            synthetic_data.append({"features": features, "label": "comment"})

        # Add more field types...
        name_examples = [
            {"name": "firstname", "placeholder": "First name", "element_type": "input"},
            {"name": "lastname", "placeholder": "Last name", "element_type": "input"},
            {"name": "fullname", "placeholder": "Full name", "element_type": "input"},
        ]

        for example in name_examples:
            field_info = FieldInfo(**example, width=250, height=40)
            features = self.extract_features(field_info)
            if "first" in example.get("name", ""):
                synthetic_data.append({"features": features, "label": "firstname"})
            elif "last" in example.get("name", ""):
                synthetic_data.append({"features": features, "label": "lastname"})
            else:
                synthetic_data.append({"features": features, "label": "name"})

        return synthetic_data

    def classify_field(self, field_info: FieldInfo) -> ClassificationResult:
        """Classify a single field using all available methods."""
        try:
            # Try ML model first if available
            if self.is_trained and (self.lgb_model or self.gb_model):
                features = self.extract_features(field_info)
                features_df = pd.DataFrame([features])

                # Ensure all feature columns are present
                for feature_name in self.feature_names:
                    if feature_name not in features_df.columns:
                        features_df[feature_name] = 0

                # Reorder columns to match training data
                features_df = features_df[self.feature_names]

                if self.lgb_model:
                    predictions = self.lgb_model.predict(
                        features_df, num_iteration=self.lgb_model.best_iteration
                    )
                    predicted_class = np.argmax(predictions[0])
                    confidence = float(np.max(predictions[0]))

                    # Get feature importance
                    feature_importance = dict(
                        zip(self.feature_names, self.lgb_model.feature_importance())
                    )

                elif self.gb_model:
                    predictions = self.gb_model.predict_proba(features_df)
                    predicted_class = np.argmax(predictions[0])
                    confidence = float(np.max(predictions[0]))

                    # Get feature importance
                    feature_importance = dict(
                        zip(self.feature_names, self.gb_model.feature_importances_)
                    )

                predicted_type = self.label_encoder.inverse_transform([predicted_class])[0]

                # Get all class probabilities
                all_probabilities = {}
                for i, class_name in enumerate(self.label_encoder.classes_):
                    if self.lgb_model:
                        all_probabilities[class_name] = float(predictions[0][i])
                    else:
                        all_probabilities[class_name] = float(predictions[0][i])

                return ClassificationResult(
                    predicted_type=predicted_type,
                    confidence=confidence,
                    method_used="ml_model",
                    all_probabilities=all_probabilities,
                    feature_importance=feature_importance,
                )

            # Fall back to rule-based classification
            return self._rule_based_classification(field_info)

        except Exception as e:
            logger.error(f"Field classification failed: {e}")
            return ClassificationResult(
                predicted_type="text",
                confidence=0.1,
                method_used="fallback",
                all_probabilities={"text": 0.1},
            )

    def classify_multiple_fields(self, fields_info: List[FieldInfo]) -> List[ClassificationResult]:
        """Classify multiple fields efficiently."""
        return [self.classify_field(field_info) for field_info in fields_info]

    def _save_model(self):
        """Save trained model to cache."""
        try:
            model_data = {
                "label_encoder": self.label_encoder,
                "feature_names": self.feature_names,
                "is_trained": self.is_trained,
            }

            # Save LightGBM model
            if self.lgb_model:
                lgb_model_path = self.model_cache_dir / "field_classifier_lgb.txt"
                self.lgb_model.save_model(str(lgb_model_path))
                model_data["lgb_model_path"] = str(lgb_model_path)

            # Save scikit-learn model
            if self.gb_model:
                gb_model_path = self.model_cache_dir / "field_classifier_gb.pkl"
                with open(gb_model_path, "wb") as f:
                    pickle.dump(self.gb_model, f)
                model_data["gb_model_path"] = str(gb_model_path)

            # Save metadata
            metadata_path = self.model_cache_dir / "field_classifier_metadata.pkl"
            with open(metadata_path, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {self.model_cache_dir}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def _load_model(self):
        """Load pre-trained model from cache."""
        try:
            metadata_path = self.model_cache_dir / "field_classifier_metadata.pkl"

            if not metadata_path.exists():
                logger.info("No cached model found, will train new model")
                self._train_synthetic_model()
                return

            with open(metadata_path, "rb") as f:
                model_data = pickle.load(f)

            self.label_encoder = model_data.get("label_encoder")
            self.feature_names = model_data.get("feature_names", [])
            self.is_trained = model_data.get("is_trained", False)

            # Load LightGBM model
            if "lgb_model_path" in model_data and LIGHTGBM_AVAILABLE:
                lgb_model_path = model_data["lgb_model_path"]
                if os.path.exists(lgb_model_path):
                    self.lgb_model = lgb.Booster(model_file=lgb_model_path)
                    logger.info("LightGBM model loaded successfully")

            # Load scikit-learn model
            if "gb_model_path" in model_data and SKLEARN_AVAILABLE:
                gb_model_path = model_data["gb_model_path"]
                if os.path.exists(gb_model_path):
                    with open(gb_model_path, "rb") as f:
                        self.gb_model = pickle.load(f)
                    logger.info("Gradient Boosting model loaded successfully")

            if not (self.lgb_model or self.gb_model):
                logger.warning("No valid model found, training new model")
                self._train_synthetic_model()

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._train_synthetic_model()

    def update_model_with_feedback(self, field_info: FieldInfo, correct_type: str):
        """Update model with user feedback (placeholder for online learning)."""
        logger.info(f"Feedback received: field should be '{correct_type}'")
        # In a production system, this would implement online learning
        # For now, we just log the feedback for future training data collection

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "is_trained": self.is_trained,
            "has_lgb_model": self.lgb_model is not None,
            "has_gb_model": self.gb_model is not None,
            "num_features": len(self.feature_names),
            "supported_types": self.FIELD_TYPES,
            "cache_dir": str(self.model_cache_dir),
        }


# Global classifier instance
_field_purpose_classifier = None


def get_field_purpose_classifier() -> FieldPurposeClassifier:
    """Get singleton field purpose classifier instance."""
    global _field_purpose_classifier
    if _field_purpose_classifier is None:
        _field_purpose_classifier = FieldPurposeClassifier()
    return _field_purpose_classifier


# Convenience function for direct classification
def classify_field_purpose(
    # DOM/UIA attributes
    tag_name: Optional[str] = None,
    element_type: Optional[str] = None,
    name: Optional[str] = None,
    id: Optional[str] = None,
    class_name: Optional[str] = None,
    placeholder: Optional[str] = None,
    aria_label: Optional[str] = None,
    title: Optional[str] = None,
    autocomplete: Optional[str] = None,
    # Visual attributes
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 0,
    # Text context
    label_text: Optional[str] = None,
    neighboring_text: Optional[str] = None,
    parent_text: Optional[str] = None,
    # Model predictions
    vision_prediction: Optional[Dict[str, Any]] = None,
    ocr_confidence: float = 0.0,
) -> ClassificationResult:
    """Classify field purpose with all available information."""

    field_info = FieldInfo(
        tag_name=tag_name,
        element_type=element_type,
        name=name,
        id=id,
        class_name=class_name,
        placeholder=placeholder,
        aria_label=aria_label,
        title=title,
        autocomplete=autocomplete,
        x=x,
        y=y,
        width=width,
        height=height,
        label_text=label_text,
        neighboring_text=neighboring_text,
        parent_text=parent_text,
        vision_prediction=vision_prediction,
        ocr_confidence=ocr_confidence,
    )

    classifier = get_field_purpose_classifier()
    return classifier.classify_field(field_info)
