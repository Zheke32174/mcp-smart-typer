#!/usr/bin/env python3
"""
CLI wrapper for the Field Purpose Classifier
Enables integration with TypeScript/Node.js applications
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict

from field_purpose_classifier import (
    ClassificationResult,
    FieldInfo,
    classify_field_purpose,
    get_field_purpose_classifier,
)

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Only show errors in CLI output
logger = logging.getLogger(__name__)


def classify_single_field(field_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a single field from JSON data."""
    try:
        # Convert dict to FieldInfo
        field_info = FieldInfo(
            tag_name=field_data.get("tagName"),
            element_type=field_data.get("elementType"),
            name=field_data.get("name"),
            id=field_data.get("id"),
            class_name=field_data.get("className"),
            placeholder=field_data.get("placeholder"),
            aria_label=field_data.get("ariaLabel"),
            title=field_data.get("title"),
            autocomplete=field_data.get("autocomplete"),
            x=field_data.get("x", 0),
            y=field_data.get("y", 0),
            width=field_data.get("width", 0),
            height=field_data.get("height", 0),
            label_text=field_data.get("labelText"),
            neighboring_text=field_data.get("neighboringText"),
            parent_text=field_data.get("parentText"),
            vision_prediction=field_data.get("visionPrediction"),
            ocr_confidence=field_data.get("ocrConfidence", 0.0),
        )

        # Get classifier and classify
        classifier = get_field_purpose_classifier()
        result = classifier.classify_field(field_info)

        # Convert result to dict
        return {
            "predicted_type": result.predicted_type,
            "confidence": result.confidence,
            "method_used": result.method_used,
            "all_probabilities": result.all_probabilities,
            "feature_importance": result.feature_importance,
        }

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {
            "predicted_type": "text",
            "confidence": 0.1,
            "method_used": "fallback",
            "all_probabilities": {"text": 0.1},
            "error": str(e),
        }


def classify_multiple_fields(fields_data: list) -> list:
    """Classify multiple fields from JSON data."""
    results = []

    for i, field_data in enumerate(fields_data):
        try:
            result = classify_single_field(field_data)
            result["field_index"] = i
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to classify field {i}: {e}")
            results.append(
                {
                    "field_index": i,
                    "predicted_type": "text",
                    "confidence": 0.1,
                    "method_used": "fallback",
                    "all_probabilities": {"text": 0.1},
                    "error": str(e),
                }
            )

    return results


def get_model_info() -> Dict[str, Any]:
    """Get model information."""
    try:
        classifier = get_field_purpose_classifier()
        return classifier.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        return {"error": str(e)}


def batch_classify_with_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """Batch classify fields with full context."""
    try:
        screenshot_path = data.get("screenshot_path")
        fields_data = data.get("fields", [])

        # Process each field
        results = []
        for field_data in fields_data:
            # Add screenshot context if available
            if screenshot_path:
                field_data["screenshot_path"] = screenshot_path

            result = classify_single_field(field_data)
            results.append(result)

        return {"success": True, "results": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Batch classification failed: {e}")
        return {"success": False, "error": str(e), "results": []}


def train_with_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process user feedback for model improvement."""
    try:
        field_data = feedback_data.get("field_data", {})
        correct_type = feedback_data.get("correct_type")

        if not correct_type:
            return {"success": False, "error": "Missing correct_type"}

        # Convert to FieldInfo
        field_info = FieldInfo(
            tag_name=field_data.get("tagName"),
            element_type=field_data.get("elementType"),
            name=field_data.get("name"),
            id=field_data.get("id"),
            class_name=field_data.get("className"),
            placeholder=field_data.get("placeholder"),
            aria_label=field_data.get("ariaLabel"),
            title=field_data.get("title"),
            autocomplete=field_data.get("autocomplete"),
            x=field_data.get("x", 0),
            y=field_data.get("y", 0),
            width=field_data.get("width", 0),
            height=field_data.get("height", 0),
            label_text=field_data.get("labelText"),
            neighboring_text=field_data.get("neighboringText"),
            parent_text=field_data.get("parentText"),
            vision_prediction=field_data.get("visionPrediction"),
            ocr_confidence=field_data.get("ocrConfidence", 0.0),
        )

        # Update model with feedback
        classifier = get_field_purpose_classifier()
        classifier.update_model_with_feedback(field_info, correct_type)

        return {"success": True, "message": f"Feedback recorded for field type: {correct_type}"}

    except Exception as e:
        logger.error(f"Feedback processing failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Field Purpose Classifier CLI")
    parser.add_argument(
        "command",
        choices=[
            "classify_single_field",
            "classify_multiple_fields",
            "get_model_info",
            "batch_classify",
            "train_feedback",
        ],
        help="Command to execute",
    )
    parser.add_argument("data", nargs="?", help="JSON data for the command")
    parser.add_argument("--file", "-f", help="Read data from file instead of argument")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Get input data
    input_data = None
    if args.file:
        try:
            with open(args.file, "r") as f:
                input_data = json.load(f)
        except Exception as e:
            print(json.dumps({"error": f"Failed to read file: {e}"}))
            sys.exit(1)
    elif args.data:
        try:
            input_data = json.loads(args.data)
        except Exception as e:
            print(json.dumps({"error": f"Failed to parse JSON: {e}"}))
            sys.exit(1)

    # Execute command
    try:
        if args.command == "classify_single_field":
            if not input_data:
                print(json.dumps({"error": "No field data provided"}))
                sys.exit(1)
            result = classify_single_field(input_data)

        elif args.command == "classify_multiple_fields":
            if not input_data or not isinstance(input_data, list):
                print(json.dumps({"error": "Invalid fields data provided"}))
                sys.exit(1)
            result = classify_multiple_fields(input_data)

        elif args.command == "get_model_info":
            result = get_model_info()

        elif args.command == "batch_classify":
            if not input_data:
                print(json.dumps({"error": "No batch data provided"}))
                sys.exit(1)
            result = batch_classify_with_context(input_data)

        elif args.command == "train_feedback":
            if not input_data:
                print(json.dumps({"error": "No feedback data provided"}))
                sys.exit(1)
            result = train_with_feedback(input_data)

        # Output result as JSON
        print(json.dumps(result, indent=2 if args.verbose else None))

    except Exception as e:
        error_result = {"error": f"Command execution failed: {e}"}
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
