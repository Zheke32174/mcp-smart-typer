#!/usr/bin/env python3
"""
Test script for Field Purpose Classifier
Demonstrates classification capabilities with various field types
"""

import json
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from field_purpose_classifier import (
    ClassificationResult,
    FieldInfo,
    classify_field_purpose,
    get_field_purpose_classifier,
)


def test_email_fields():
    """Test email field classification."""
    print("=== Testing Email Fields ===")

    test_cases = [
        {
            "name": "email",
            "placeholder": "Enter your email address",
            "element_type": "email",
            "width": 300,
            "height": 40,
        },
        {
            "id": "user_email",
            "aria_label": "Email",
            "element_type": "input",
            "width": 250,
            "height": 35,
        },
        {
            "class_name": "email-input",
            "label_text": "E-mail Address",
            "neighboring_text": "Please enter your email",
            "width": 280,
            "height": 38,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print(
            f"  Top probabilities: {dict(sorted(result.all_probabilities.items(), key=lambda x: x[1], reverse=True)[:3])}"
        )
        print()


def test_password_fields():
    """Test password field classification."""
    print("=== Testing Password Fields ===")

    test_cases = [
        {
            "name": "password",
            "element_type": "password",
            "placeholder": "Password",
            "width": 300,
            "height": 40,
        },
        {
            "id": "user_pwd",
            "element_type": "input",
            "label_text": "Enter your password",
            "width": 280,
            "height": 38,
        },
        {
            "class_name": "password-field",
            "aria_label": "Password",
            "neighboring_text": "Must be 8+ characters",
            "width": 320,
            "height": 42,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_search_fields():
    """Test search field classification."""
    print("=== Testing Search Fields ===")

    test_cases = [
        {
            "name": "search",
            "placeholder": "Search...",
            "element_type": "search",
            "width": 400,
            "height": 35,
        },
        {
            "id": "search_box",
            "element_type": "input",
            "aria_label": "Search products",
            "width": 450,
            "height": 30,
        },
        {
            "class_name": "search-input",
            "label_text": "Find",
            "neighboring_text": "Type to search",
            "width": 380,
            "height": 36,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_name_fields():
    """Test name field classification."""
    print("=== Testing Name Fields ===")

    test_cases = [
        {
            "name": "firstname",
            "placeholder": "First name",
            "element_type": "input",
            "width": 200,
            "height": 40,
        },
        {
            "name": "lastname",
            "placeholder": "Last name",
            "element_type": "input",
            "width": 200,
            "height": 40,
        },
        {
            "id": "fullname",
            "label_text": "Full Name",
            "element_type": "input",
            "width": 300,
            "height": 40,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_comment_fields():
    """Test comment/textarea field classification."""
    print("=== Testing Comment Fields ===")

    test_cases = [
        {
            "name": "comment",
            "element_type": "textarea",
            "placeholder": "Enter your comments",
            "width": 400,
            "height": 120,
        },
        {
            "id": "message",
            "element_type": "textarea",
            "label_text": "Message",
            "width": 450,
            "height": 100,
        },
        {
            "class_name": "feedback-box",
            "aria_label": "Feedback",
            "neighboring_text": "Tell us what you think",
            "width": 380,
            "height": 150,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_button_fields():
    """Test button field classification."""
    print("=== Testing Button Fields ===")

    test_cases = [
        {
            "element_type": "button",
            "class_name": "btn-submit",
            "neighboring_text": "Submit",
            "width": 100,
            "height": 40,
        },
        {
            "element_type": "button",
            "aria_label": "Login",
            "label_text": "Sign In",
            "width": 80,
            "height": 35,
        },
        {
            "name": "send_btn",
            "element_type": "button",
            "title": "Send Message",
            "width": 120,
            "height": 42,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_phone_fields():
    """Test phone field classification."""
    print("=== Testing Phone Fields ===")

    test_cases = [
        {
            "name": "phone",
            "element_type": "tel",
            "placeholder": "Phone number",
            "width": 250,
            "height": 40,
        },
        {
            "id": "mobile_number",
            "label_text": "Mobile",
            "element_type": "input",
            "width": 220,
            "height": 38,
        },
        {
            "class_name": "phone-input",
            "aria_label": "Contact number",
            "neighboring_text": "Enter your phone",
            "width": 260,
            "height": 40,
        },
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Input: {json.dumps(case, indent=2)}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_with_vision_predictions():
    """Test classification with vision model predictions."""
    print("=== Testing with Vision Predictions ===")

    # Simulate vision model predictions
    vision_prediction = {
        "predicted_type": "email",
        "confidence": 0.8,
        "class_probabilities": {"email": 0.8, "text": 0.1, "username": 0.05, "search": 0.05},
    }

    test_case = {
        "id": "user_input",
        "element_type": "input",
        "width": 300,
        "height": 40,
        "vision_prediction": vision_prediction,
        "ocr_confidence": 0.7,
    }

    field_info = FieldInfo(**test_case)
    result = get_field_purpose_classifier().classify_field(field_info)

    print("Test with Vision Prediction:")
    print(
        f"  Vision says: {vision_prediction['predicted_type']} ({vision_prediction['confidence']:.3f})"
    )
    print(f"  Final result: {result.predicted_type} (confidence: {result.confidence:.3f})")
    print(f"  Method: {result.method_used}")
    print(f"  Feature importance: {result.feature_importance}")
    print()


def test_autocomplete_attributes():
    """Test classification with autocomplete attributes."""
    print("=== Testing Autocomplete Attributes ===")

    test_cases = [
        {"element_type": "input", "autocomplete": "email", "width": 300, "height": 40},
        {"element_type": "input", "autocomplete": "current-password", "width": 300, "height": 40},
        {"element_type": "input", "autocomplete": "given-name", "width": 200, "height": 40},
        {"element_type": "input", "autocomplete": "tel", "width": 250, "height": 40},
    ]

    for i, case in enumerate(test_cases):
        field_info = FieldInfo(**case)
        result = get_field_purpose_classifier().classify_field(field_info)

        print(f"Test {i+1}:")
        print(f"  Autocomplete: {case['autocomplete']}")
        print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
        print(f"  Method: {result.method_used}")
        print()


def test_batch_classification():
    """Test batch classification of multiple fields."""
    print("=== Testing Batch Classification ===")

    fields = [
        FieldInfo(name="email", element_type="email", width=300, height=40),
        FieldInfo(name="password", element_type="password", width=300, height=40),
        FieldInfo(name="search", element_type="search", width=400, height=35),
        FieldInfo(element_type="textarea", width=400, height=120),
        FieldInfo(element_type="button", width=100, height=40),
    ]

    classifier = get_field_purpose_classifier()
    results = classifier.classify_multiple_fields(fields)

    print("Batch Classification Results:")
    for i, result in enumerate(results):
        print(
            f"  Field {i+1}: {result.predicted_type} (confidence: {result.confidence:.3f}, method: {result.method_used})"
        )
    print()


def test_model_info():
    """Test getting model information."""
    print("=== Model Information ===")

    classifier = get_field_purpose_classifier()
    info = classifier.get_model_info()

    print("Model Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()


def test_convenience_function():
    """Test the convenience function for direct classification."""
    print("=== Testing Convenience Function ===")

    result = classify_field_purpose(
        name="email",
        placeholder="Enter your email",
        element_type="email",
        width=300,
        height=40,
        label_text="Email Address",
    )

    print("Convenience Function Result:")
    print(f"  Predicted: {result.predicted_type} (confidence: {result.confidence:.3f})")
    print(f"  Method: {result.method_used}")
    print()


def main():
    """Run all tests."""
    print("Field Purpose Classifier Test Suite")
    print("=" * 50)
    print()

    try:
        # Test different field types
        test_email_fields()
        test_password_fields()
        test_search_fields()
        test_name_fields()
        test_comment_fields()
        test_button_fields()
        test_phone_fields()

        # Test advanced features
        test_with_vision_predictions()
        test_autocomplete_attributes()
        test_batch_classification()
        test_convenience_function()
        test_model_info()

        print("=" * 50)
        print("All tests completed successfully!")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
