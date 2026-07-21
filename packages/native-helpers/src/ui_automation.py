"""
UI Automation Handler: Contains implementations of various UI operations.
"""

import asyncio
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

import pyautogui
import pygetwindow as gw
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController

from .ocr_handler import get_ocr_handler
from .vision_classifier import get_vision_classifier


class UIAutomationHandler:
    """Handles UI automation tasks such as typing text, clicking buttons, etc."""

    def __init__(self) - None:
        """Initialize the UI automation handler."""
        self._keyboard = KeyboardController()
        self._mouse = MouseController()

    async def type_text(self, text: str, delay: float) - None:
        """Type text with a given delay between keystrokes."""
        for char in text:
            self._keyboard.type(char)
            time.sleep(delay)

    async def send_keys(self, keys: str, modifiers: List[str]) - None:
        """Send key combinations."""
        modifier_keys = {
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'shift': Key.shift,
            'win': Key.cmd
        }
        # Press modifiers
        for mod in modifiers:
            self._keyboard.press(modifier_keys[mod])
        # Press and release the main keys
        for key in keys:
            self._keyboard.press(key)
            self._keyboard.release(key)
        # Release modifiers
        for mod in reversed(modifiers):
            self._keyboard.release(modifier_keys[mod])


    async def get_active_window(self) - Dict[str, Any]:
        """Get details of the currently active window."""
        window = gw.getActiveWindow()
        if window:
            return {
                'title': window.title,
                'class_name': window._hWnd,
                'pid': window.processId,
                'handle': window._hWnd,
                'bounds': {
                    'x': window.left,
                    'y': window.top,
                    'width': window.width,
                    'height': window.height
                },
                'is_active': window.isActive
            }
        return {}

    async def find_element(self, selector: str, method: str, timeout: float) - Dict[str, Any]:
        """Find an element on the screen matching given parameters."""
        # Example implementation; actual implementation may vary
        time.sleep(timeout)  # Simulate delay
        return {
            'id': 'mock_id',
            'name': 'mock_name',
            'class_name': 'mock_class',
            'bounds': {'x': 100, 'y': 100, 'width': 200, 'height': 200},
            'is_visible': True,
            'is_enabled': True,
            'text': 'mock_text',
            'element_type': 'mock_type'
        }

    async def click_element(self, x: int, y: int, button: str, double_click: bool) -> None:
        """Click at specific coordinates on the screen with the specified button."""
        mouse_button = {'left': Button.left, 'right': Button.right, 'middle': Button.middle}[button]
        self._mouse.position = (x, y)
        if double_click:
            self._mouse.click(mouse_button, 2)
        else:
            self._mouse.click(mouse_button)
    
    async def take_screenshot(self) -> str:
        """Take a screenshot and return the file path."""
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f'screenshot_{int(time.time())}.png')
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        return screenshot_path
    
    async def detect_fields_with_fallback(self, 
                                         context_hint: str,
                                         window_title: Optional[str] = None,
                                         include_hidden: bool = False,
                                         confidence: float = 0.8) -> Dict[str, Any]:
        """Enhanced field detection with OCR and vision fallback."""
        try:
            # Take screenshot for analysis
            screenshot_path = await self.take_screenshot()
            
            # First, try traditional UI automation detection (mock implementation)
            semantic_fields = await self._detect_semantic_fields(context_hint, window_title, include_hidden)
            
            # If semantic detection fails or has low confidence, use OCR + Vision fallback
            if not semantic_fields or self._needs_fallback_analysis(semantic_fields, confidence):
                fallback_fields = await self._detect_fields_with_ocr_vision(screenshot_path, semantic_fields)
                
                # Merge results
                enhanced_fields = self._merge_field_detections(semantic_fields, fallback_fields)
            else:
                enhanced_fields = semantic_fields
            
            # Clean up screenshot
            try:
                os.unlink(screenshot_path)
            except:
                pass
            
            return {
                'fields': enhanced_fields,
                'window_info': await self.get_active_window(),
                'detection_method': 'enhanced_with_fallback'
            }
            
        except Exception as e:
            return {
                'fields': [],
                'error': str(e),
                'detection_method': 'error'
            }
    
    async def _detect_semantic_fields(self, 
                                     context_hint: str,
                                     window_title: Optional[str],
                                     include_hidden: bool) -> List[Dict[str, Any]]:
        """Traditional semantic field detection (mock implementation)."""
        # This would be replaced with actual UI automation logic
        # For now, return mock data to simulate semantic detection
        return [
            {
                'id': 'field_1',
                'name': 'username',
                'type': 'input',
                'bounds': {'x': 100, 'y': 100, 'width': 200, 'height': 30},
                'confidence': 0.9,
                'semantic_type': 'username'
            },
            {
                'id': 'field_2', 
                'name': 'password',
                'type': 'password',
                'bounds': {'x': 100, 'y': 150, 'width': 200, 'height': 30},
                'confidence': 0.85,
                'semantic_type': 'password'
            }
        ]
    
    def _needs_fallback_analysis(self, fields: List[Dict[str, Any]], min_confidence: float) -> bool:
        """Determine if fallback analysis is needed."""
        if not fields:
            return True
            
        # Check if any field has low confidence or missing type
        for field in fields:
            if field.get('confidence', 0) < min_confidence or not field.get('semantic_type'):
                return True
                
        return False
    
    async def _detect_fields_with_ocr_vision(self, 
                                           screenshot_path: str,
                                           semantic_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use OCR and vision analysis to detect/enhance field information."""
        try:
            ocr_handler = get_ocr_handler()
            vision_classifier = get_vision_classifier()
            
            # Extract field bounds for analysis
            field_bounds = []
            for field in semantic_fields:
                bounds = field.get('bounds', {})
                if bounds:
                    field_bounds.append({
                        'x': bounds['x'],
                        'y': bounds['y'],
                        'width': bounds['width'],
                        'height': bounds['height']
                    })
            
            # If no semantic fields, try to detect fields from screenshot
            if not field_bounds:
                field_bounds = await self._detect_field_regions_from_screenshot(screenshot_path)
            
            # Analyze fields with OCR for context
            ocr_results = ocr_handler.analyze_field_labels(screenshot_path, field_bounds)
            
            # Classify fields with vision model
            vision_results = vision_classifier.classify_multiple_fields(screenshot_path, field_bounds)
            
            # Combine results
            enhanced_fields = []
            for i, bounds in enumerate(field_bounds):
                ocr_data = ocr_results[i] if i < len(ocr_results) else {}
                vision_data = vision_results[i] if i < len(vision_results) else {}
                
                # Determine best field type
                field_type = self._determine_field_type(ocr_data, vision_data)
                
                enhanced_fields.append({
                    'id': f'enhanced_field_{i}',
                    'name': f'field_{i}',
                    'type': field_type['type'],
                    'bounds': bounds,
                    'confidence': field_type['confidence'],
                    'ocr_context': ocr_data.get('detected_text', ''),
                    'ocr_confidence': ocr_data.get('confidence', 0),
                    'vision_type': vision_data.get('predicted_type', 'text'),
                    'vision_confidence': vision_data.get('confidence', 0),
                    'analysis_method': 'ocr_vision_fallback'
                })
            
            return enhanced_fields
            
        except Exception as e:
            # Return basic field structure if analysis fails
            return [{
                'id': f'fallback_field_{i}',
                'name': f'field_{i}',
                'type': 'text',
                'bounds': bounds,
                'confidence': 0.3,
                'error': str(e),
                'analysis_method': 'fallback_error'
            } for i, bounds in enumerate(field_bounds) if field_bounds]
    
    async def _detect_field_regions_from_screenshot(self, screenshot_path: str) -> List[Dict[str, int]]:
        """Detect potential field regions from screenshot (basic implementation)."""
        # This is a simplified implementation
        # In a real scenario, you'd use computer vision to detect form elements
        return [
            {'x': 100, 'y': 100, 'width': 200, 'height': 30},
            {'x': 100, 'y': 150, 'width': 200, 'height': 30},
            {'x': 100, 'y': 200, 'width': 200, 'height': 30}
        ]
    
    def _determine_field_type(self, ocr_data: Dict[str, Any], vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best field type from OCR and vision analysis."""
        # Prioritize OCR results if confident
        ocr_type = ocr_data.get('predicted_type', 'text')
        ocr_confidence = ocr_data.get('confidence', 0)
        
        # Vision results
        vision_type = vision_data.get('predicted_type', 'text')
        vision_confidence = vision_data.get('confidence', 0)
        
        # Decision logic
        if ocr_confidence > 0.7 and ocr_type != 'text':
            return {'type': ocr_type, 'confidence': ocr_confidence}
        elif vision_confidence > 0.6 and vision_type != 'text':
            return {'type': vision_type, 'confidence': vision_confidence}
        elif ocr_confidence > vision_confidence:
            return {'type': ocr_type, 'confidence': ocr_confidence}
        else:
            return {'type': vision_type, 'confidence': vision_confidence}
    
    def _merge_field_detections(self, 
                              semantic_fields: List[Dict[str, Any]], 
                              fallback_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge semantic and fallback field detections."""
        if not semantic_fields:
            return fallback_fields
            
        if not fallback_fields:
            return semantic_fields
        
        # Enhanced merge logic
        merged_fields = []
        
        for i, semantic_field in enumerate(semantic_fields):
            if i < len(fallback_fields):
                fallback_field = fallback_fields[i]
                
                # Use semantic data as base, enhance with fallback data
                merged_field = semantic_field.copy()
                
                # Update type if fallback has higher confidence
                if fallback_field.get('confidence', 0) > semantic_field.get('confidence', 0):
                    merged_field['type'] = fallback_field['type']
                    merged_field['confidence'] = fallback_field['confidence']
                
                # Add fallback metadata
                merged_field.update({
                    'ocr_context': fallback_field.get('ocr_context', ''),
                    'vision_type': fallback_field.get('vision_type', ''),
                    'analysis_method': 'merged_semantic_fallback'
                })
                
                merged_fields.append(merged_field)
            else:
                merged_fields.append(semantic_field)
        
        # Add any extra fallback fields
        if len(fallback_fields) > len(semantic_fields):
            merged_fields.extend(fallback_fields[len(semantic_fields):])
        
        return merged_fields
