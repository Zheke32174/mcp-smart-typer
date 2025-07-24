#!/usr/bin/env python3
"""
Enhanced gRPC Server for Desktop UI Automation
Implements field detection with OCR/vision fallback and comprehensive desktop automation
"""

import asyncio
import logging
import time
from concurrent import futures
from typing import List, Optional, Dict, Any

import grpc
import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import uiautomation as uia
from pathlib import Path

# Import generated protobuf classes
import sys
sys.path.append('src/generated')
import ui_automation_pb2
import ui_automation_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FieldDetector:
    """Enhanced field detection with multiple methods"""
    
    def __init__(self):
        self.field_cache = {}
        self.detection_methods = [
            self._detect_uia_fields,
            self._detect_ocr_fields,
            self._detect_visual_fields,
        ]
    
    def detect_fields(self, context_hint: str, window_title: Optional[str] = None, 
                     include_hidden: bool = False, confidence: float = 0.8) -> List[Dict[str, Any]]:
        """Detect fields using multiple methods with fallback"""
        
        logger.info(f"Detecting fields with context: {context_hint}")
        all_fields = []
        
        # Try each detection method
        for method in self.detection_methods:
            try:
                fields = method(context_hint, window_title, include_hidden, confidence)
                logger.info(f"Method {method.__name__} found {len(fields)} fields")
                all_fields.extend(fields)
            except Exception as e:
                logger.warning(f"Detection method {method.__name__} failed: {e}")
        
        # Deduplicate and merge fields
        return self._merge_detected_fields(all_fields)
    
    def _detect_uia_fields(self, context_hint: str, window_title: Optional[str], 
                          include_hidden: bool, confidence: float) -> List[Dict[str, Any]]:
        """Detect fields using UI Automation"""
        
        fields = []
        
        # Get the active window or search by title
        if window_title:
            window = uia.FindWindow(searchDepth=1, Name=window_title)
        else:
            window = uia.GetForegroundWindow()
        
        if not window:
            logger.warning("No target window found for UIA detection")
            return fields
        
        # Find input controls
        control_types = [
            uia.ControlType.EditControl,
            uia.ControlType.ComboBoxControl,
            uia.ControlType.ListItemControl,
            uia.ControlType.DocumentControl,
        ]
        
        for control_type in control_types:
            try:
                controls = window.FindAll(searchDepth=10, ControlType=control_type)
                
                for control in controls:
                    if not include_hidden and not control.IsVisible:
                        continue
                    
                    # Get control properties
                    rect = control.BoundingRectangle
                    
                    field_info = {
                        'id': f"uia_{control.AutomationId or id(control)}",
                        'name': control.Name or "unnamed_field",
                        'type': self._map_uia_control_type(control_type),
                        'description': control.HelpText or control.Name,
                        'bounds': {
                            'x': rect.left,
                            'y': rect.top,
                            'width': rect.width(),
                            'height': rect.height(),
                        },
                        'confidence': 0.9,
                        'window_handle': str(window.Handle),
                        'control_id': control.AutomationId,
                        'analysis_method': 'uia',
                        'semantic_type': self._detect_semantic_type(control.Name or ""),
                        'required': self._is_required_field(control),
                        'placeholder': self._get_placeholder_text(control),
                    }
                    
                    fields.append(field_info)
                    
            except Exception as e:
                logger.warning(f"UIA detection error for {control_type}: {e}")
        
        return fields
    
    def _detect_ocr_fields(self, context_hint: str, window_title: Optional[str], 
                          include_hidden: bool, confidence: float) -> List[Dict[str, Any]]:
        """Detect fields using OCR on screenshot"""
        
        fields = []
        
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours for potential input fields
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                # Filter contours by size (potential input fields)
                x, y, w, h = cv2.boundingRect(contour)
                
                # Skip very small or very large areas
                if w < 50 or h < 15 or w > 500 or h > 100:
                    continue
                
                # Extract region for OCR
                roi = gray[y:y+h, x:x+w]
                
                # Enhance the region
                roi_pil = Image.fromarray(roi)
                enhancer = ImageEnhance.Contrast(roi_pil)
                roi_enhanced = enhancer.enhance(2.0)
                
                # Perform OCR
                try:
                    ocr_text = pytesseract.image_to_string(
                        roi_enhanced, 
                        config='--psm 8 --oem 3'
                    ).strip()
                    
                    ocr_confidence = self._get_ocr_confidence(roi_enhanced)
                    
                    if ocr_confidence < confidence:
                        continue
                    
                    # Check if this looks like an input field context
                    if self._is_field_context(ocr_text, context_hint):
                        field_info = {
                            'id': f"ocr_field_{x}_{y}_{i}",
                            'name': ocr_text or f"ocr_field_{i}",
                            'type': self._detect_field_type_from_ocr(ocr_text),
                            'description': f"OCR detected field: {ocr_text}",
                            'bounds': {'x': x, 'y': y, 'width': w, 'height': h},
                            'confidence': ocr_confidence,
                            'analysis_method': 'ocr',
                            'ocr_context': ocr_text,
                            'ocr_confidence': ocr_confidence,
                            'semantic_type': self._detect_semantic_type(ocr_text),
                        }
                        fields.append(field_info)
                        
                except Exception as e:
                    logger.debug(f"OCR failed for region {x},{y},{w},{h}: {e}")
                    
        except Exception as e:
            logger.error(f"OCR field detection failed: {e}")
        
        return fields
    
    def _detect_visual_fields(self, context_hint: str, window_title: Optional[str], 
                             include_hidden: bool, confidence: float) -> List[Dict[str, Any]]:
        """Detect fields using visual pattern matching"""
        
        fields = []
        
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
            
            # Look for typical input field patterns
            # 1. Rectangular shapes with borders
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find rectangles
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Look for rectangular shapes (4 vertices)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Filter by typical input field dimensions
                    if 100 <= w <= 400 and 20 <= h <= 50:
                        # Calculate visual confidence based on shape regularity
                        visual_confidence = self._calculate_visual_confidence(approx, w, h)
                        
                        if visual_confidence >= confidence:
                            field_info = {
                                'id': f"visual_field_{x}_{y}_{i}",
                                'name': f"visual_field_{i}",
                                'type': 'text',  # Default assumption
                                'description': f"Visually detected input field",
                                'bounds': {'x': x, 'y': y, 'width': w, 'height': h},
                                'confidence': visual_confidence,
                                'analysis_method': 'visual',
                                'vision_type': 'rectangle_detection',
                                'vision_confidence': visual_confidence,
                            }
                            fields.append(field_info)
                            
        except Exception as e:
            logger.error(f"Visual field detection failed: {e}")
        
        return fields
    
    def _merge_detected_fields(self, all_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping fields from different detection methods"""
        
        if not all_fields:
            return []
        
        merged_fields = []
        
        # Sort by confidence descending
        all_fields.sort(key=lambda f: f.get('confidence', 0), reverse=True)
        
        for field in all_fields:
            # Check if this field overlaps significantly with existing fields
            is_duplicate = False
            
            for existing in merged_fields:
                if self._fields_overlap(field, existing, threshold=0.7):
                    # Merge information from both fields
                    self._merge_field_info(existing, field)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged_fields.append(field)
        
        return merged_fields
    
    def _fields_overlap(self, field1: Dict[str, Any], field2: Dict[str, Any], threshold: float = 0.7) -> bool:
        """Check if two fields overlap significantly"""
        
        b1 = field1.get('bounds', {})
        b2 = field2.get('bounds', {})
        
        if not b1 or not b2:
            return False
        
        # Calculate intersection area
        x_overlap = max(0, min(b1['x'] + b1['width'], b2['x'] + b2['width']) - max(b1['x'], b2['x']))
        y_overlap = max(0, min(b1['y'] + b1['height'], b2['y'] + b2['height']) - max(b1['y'], b2['y']))
        
        intersection_area = x_overlap * y_overlap
        
        # Calculate union area
        area1 = b1['width'] * b1['height']
        area2 = b2['width'] * b2['height']
        union_area = area1 + area2 - intersection_area
        
        # Calculate IoU (Intersection over Union)
        if union_area == 0:
            return False
        
        iou = intersection_area / union_area
        return iou >= threshold
    
    def _merge_field_info(self, existing: Dict[str, Any], new: Dict[str, Any]) -> None:
        """Merge information from new field into existing field"""
        
        # Take the higher confidence method as primary
        if new.get('confidence', 0) > existing.get('confidence', 0):
            existing.update({
                'id': new['id'],
                'name': new['name'],
                'type': new['type'],
                'confidence': new['confidence'],
                'analysis_method': f"{existing.get('analysis_method', '')},{new.get('analysis_method', '')}",
            })
        
        # Merge OCR information
        if 'ocr_context' in new:
            existing['ocr_context'] = new['ocr_context']
            existing['ocr_confidence'] = new['ocr_confidence']
        
        # Merge visual information
        if 'vision_type' in new:
            existing['vision_type'] = new['vision_type']
            existing['vision_confidence'] = new['vision_confidence']
    
    # Helper methods
    def _map_uia_control_type(self, control_type) -> str:
        """Map UIA control type to field type"""
        mapping = {
            uia.ControlType.EditControl: 'text',
            uia.ControlType.ComboBoxControl: 'select',
            uia.ControlType.DocumentControl: 'textarea',
        }
        return mapping.get(control_type, 'text')
    
    def _detect_semantic_type(self, text: str) -> str:
        """Detect semantic field type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['password', 'passwd', 'pwd']):
            return 'password'
        elif any(word in text_lower for word in ['email', 'mail', '@']):
            return 'email'
        elif any(word in text_lower for word in ['phone', 'tel', 'mobile']):
            return 'tel'
        elif any(word in text_lower for word in ['url', 'website', 'link', 'http']):
            return 'url'
        elif any(word in text_lower for word in ['number', 'amount', 'price', 'age']):
            return 'number'
        else:
            return 'text'
    
    def _is_required_field(self, control) -> bool:
        """Check if UIA control is required"""
        try:
            return control.IsRequiredForForm
        except:
            return False
    
    def _get_placeholder_text(self, control) -> Optional[str]:
        """Get placeholder text from UIA control"""
        try:
            return control.ValuePattern.Value if hasattr(control, 'ValuePattern') else None
        except:
            return None
    
    def _get_ocr_confidence(self, image) -> float:
        """Calculate OCR confidence score"""
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            return np.mean(confidences) / 100.0 if confidences else 0.0
        except:
            return 0.0
    
    def _is_field_context(self, ocr_text: str, context_hint: str) -> bool:
        """Check if OCR text matches field context"""
        if not ocr_text:
            return False
        
        # Look for common field labels/contexts
        field_keywords = [
            'username', 'password', 'email', 'name', 'phone', 'address',
            'search', 'input', 'enter', 'type', 'login', 'register'
        ]
        
        text_lower = ocr_text.lower()
        context_lower = context_hint.lower()
        
        # Check if OCR text contains field-related keywords
        has_field_keyword = any(keyword in text_lower for keyword in field_keywords)
        
        # Check if OCR text is related to context hint
        context_match = context_lower in text_lower or any(
            word in text_lower for word in context_lower.split('-')
        )
        
        return has_field_keyword or context_match
    
    def _detect_field_type_from_ocr(self, ocr_text: str) -> str:
        """Detect field type from OCR text"""
        return self._detect_semantic_type(ocr_text)
    
    def _calculate_visual_confidence(self, approx_poly, width: int, height: int) -> float:
        """Calculate confidence for visually detected field"""
        
        # Check if it's a good rectangle (4 corners, reasonable aspect ratio)
        if len(approx_poly) != 4:
            return 0.0
        
        # Check aspect ratio (input fields are usually wider than tall)
        aspect_ratio = width / height if height > 0 else 0
        if not (2.0 <= aspect_ratio <= 20.0):
            return 0.5
        
        # Base confidence for rectangular shape in reasonable size range
        base_confidence = 0.7
        
        # Bonus for good aspect ratio
        if 3.0 <= aspect_ratio <= 10.0:
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)


class EnhancedUIAutomationService(ui_automation_pb2_grpc.UIAutomationServiceServicer):
    """Enhanced gRPC service implementation"""
    
    def __init__(self):
        self.field_detector = FieldDetector()
        self.field_cache = {}
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        logger.info("Enhanced UI Automation Service initialized")
    
    def Ping(self, request, context):
        """Health check endpoint"""
        return ui_automation_pb2.PingResponse(
            success=True,
            message="Enhanced UI Automation Service is running",
            timestamp=int(time.time() * 1000)
        )
    
    def DetectFields(self, request, context):
        """Detect fields using standard method"""
        return self._detect_fields_impl(request, context, use_fallback=False)
    
    def DetectFieldsWithFallback(self, request, context):
        """Detect fields with OCR and vision fallback"""
        return self._detect_fields_impl(request, context, use_fallback=True)
    
    def _detect_fields_impl(self, request, context, use_fallback=True):
        """Internal field detection implementation"""
        
        try:
            logger.info(f"Field detection request: {request.context_hint} (fallback: {use_fallback})")
            
            # Detect fields
            fields_data = self.field_detector.detect_fields(
                context_hint=request.context_hint,
                window_title=request.window_title if request.HasField('window_title') else None,
                include_hidden=request.include_hidden if request.HasField('include_hidden') else False,
                confidence=request.confidence if request.HasField('confidence') else 0.8
            )
            
            # Convert to protobuf format
            fields = []
            for field_data in fields_data:
                field = ui_automation_pb2.FieldInfo(
                    id=field_data['id'],
                    name=field_data['name'],
                    type=field_data['type'],
                    description=field_data.get('description', ''),
                    placeholder=field_data.get('placeholder', ''),
                    semantic_type=field_data.get('semantic_type', ''),
                    required=field_data.get('required', False),
                    pattern=field_data.get('pattern', ''),
                    bounds=ui_automation_pb2.ElementBounds(
                        x=field_data['bounds']['x'],
                        y=field_data['bounds']['y'],
                        width=field_data['bounds']['width'],
                        height=field_data['bounds']['height']
                    ),
                    confidence=field_data.get('confidence', 0.8),
                    window_handle=field_data.get('window_handle', ''),
                    control_id=field_data.get('control_id', ''),
                    ocr_context=field_data.get('ocr_context', ''),
                    ocr_confidence=field_data.get('ocr_confidence', 0.0),
                    vision_type=field_data.get('vision_type', ''),
                    vision_confidence=field_data.get('vision_confidence', 0.0),
                    analysis_method=field_data.get('analysis_method', '')
                )
                fields.append(field)
                
                # Cache field for later operations
                self.field_cache[field_data['id']] = field_data
            
            # Get window info
            window_info = self._get_current_window_info()
            
            logger.info(f"Detected {len(fields)} fields")
            
            return ui_automation_pb2.DetectFieldsResponse(
                success=True,
                fields=fields,
                window_info=window_info,
                message=f"Successfully detected {len(fields)} fields"
            )
            
        except Exception as e:
            logger.error(f"Field detection failed: {e}")
            return ui_automation_pb2.DetectFieldsResponse(
                success=False,
                fields=[],
                message=f"Field detection failed: {str(e)}"
            )
    
    def TypeText(self, request, context):
        """Type text with enhanced field detection"""
        try:
            logger.info(f"Typing text with delay: {request.delay}")
            
            # Type the text
            if request.HasField('delay') and request.delay > 0:
                for char in request.text:
                    pyautogui.write(char)
                    time.sleep(request.delay / 1000.0)
            else:
                pyautogui.write(request.text)
            
            return ui_automation_pb2.TypeTextResponse(
                success=True,
                message=f"Successfully typed {len(request.text)} characters"
            )
            
        except Exception as e:
            logger.error(f"Typing failed: {e}")
            return ui_automation_pb2.TypeTextResponse(
                success=False,
                message=f"Typing failed: {str(e)}"
            )
    
    def GetFieldValue(self, request, context):
        """Get field value with source detection"""
        try:
            # Check if field is in cache
            field_data = self.field_cache.get(request.field_id)
            
            if not field_data:
                return ui_automation_pb2.GetFieldValueResponse(
                    success=False,
                    message="Field not found in cache"
                )
            
            # Try to get value using different methods based on analysis method
            analysis_method = field_data.get('analysis_method', '')
            value = ""
            
            if 'uia' in analysis_method:
                value = self._get_uia_field_value(field_data)
            elif 'ocr' in analysis_method:
                value = self._get_ocr_field_value(field_data)
            else:
                # Fallback to clipboard method
                value = self._get_clipboard_field_value(field_data)
            
            # Truncate if needed
            max_length = request.max_length if request.HasField('max_length') else 10000
            if len(value) > max_length:
                value = value[:max_length]
            
            # Check if field is secure
            is_secure = field_data.get('semantic_type') == 'password'
            
            return ui_automation_pb2.GetFieldValueResponse(
                success=True,
                value="" if is_secure else value,  # Don't return password values
                is_secure=is_secure,
                message="Field value retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get field value failed: {e}")
            return ui_automation_pb2.GetFieldValueResponse(
                success=False,
                message=f"Get field value failed: {str(e)}"
            )
    
    def FocusField(self, request, context):
        """Focus field with source detection"""
        try:
            # Check if field is in cache
            field_data = self.field_cache.get(request.field_id)
            
            if not field_data:
                return ui_automation_pb2.FocusFieldResponse(
                    success=False,
                    message="Field not found in cache"
                )
            
            # Get field bounds
            bounds = field_data['bounds']
            center_x = bounds['x'] + bounds['width'] // 2
            center_y = bounds['y'] + bounds['height'] // 2
            
            # Click on the field to focus it
            pyautogui.click(center_x, center_y)
            
            # Scroll into view if requested
            if request.scroll_into_view:
                # Simple scroll implementation
                pyautogui.scroll(3, x=center_x, y=center_y)
            
            return ui_automation_pb2.FocusFieldResponse(
                success=True,
                window_brought_to_front=True,
                message="Field focused successfully"
            )
            
        except Exception as e:
            logger.error(f"Focus field failed: {e}")
            return ui_automation_pb2.FocusFieldResponse(
                success=False,
                message=f"Focus field failed: {str(e)}"
            )
    
    # Helper methods
    def _get_current_window_info(self):
        """Get current window information"""
        try:
            window = uia.GetForegroundWindow()
            if window:
                rect = window.BoundingRectangle
                return ui_automation_pb2.WindowInfo(
                    title=window.Name or "Unknown",
                    class_name=window.ClassName or "Unknown",
                    pid=window.ProcessId,
                    handle=str(window.Handle),
                    bounds=ui_automation_pb2.WindowBounds(
                        x=rect.left,
                        y=rect.top,
                        width=rect.width(),
                        height=rect.height()
                    ),
                    is_active=True
                )
        except Exception as e:
            logger.warning(f"Could not get window info: {e}")
        
        return None
    
    def _get_uia_field_value(self, field_data: Dict[str, Any]) -> str:
        """Get field value using UI Automation"""
        try:
            control_id = field_data.get('control_id')
            if not control_id:
                return ""
            
            # Find the control and get its value
            window = uia.GetForegroundWindow()
            control = window.FindFirst(searchDepth=10, AutomationId=control_id)
            
            if control and hasattr(control, 'ValuePattern'):
                return control.ValuePattern.Value or ""
                
        except Exception as e:
            logger.debug(f"UIA field value retrieval failed: {e}")
        
        return ""
    
    def _get_ocr_field_value(self, field_data: Dict[str, Any]) -> str:
        """Get field value using OCR"""
        try:
            bounds = field_data['bounds']
            
            # Take screenshot of the field area
            screenshot = pyautogui.screenshot(region=(
                bounds['x'], bounds['y'], bounds['width'], bounds['height']
            ))
            
            # Convert to grayscale and enhance
            gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                enhanced, config='--psm 8 --oem 3'
            ).strip()
            
            return text
            
        except Exception as e:
            logger.debug(f"OCR field value retrieval failed: {e}")
        
        return ""
    
    def _get_clipboard_field_value(self, field_data: Dict[str, Any]) -> str:
        """Get field value using clipboard method"""
        try:
            bounds = field_data['bounds']
            center_x = bounds['x'] + bounds['width'] // 2
            center_y = bounds['y'] + bounds['height'] // 2
            
            # Click field, select all, copy
            pyautogui.click(center_x, center_y)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')
            
            # Get clipboard content (would need clipboard library)
            # For now, return empty string
            return ""
            
        except Exception as e:
            logger.debug(f"Clipboard field value retrieval failed: {e}")
        
        return ""


async def serve(port: int = 50051):
    """Start the enhanced gRPC server"""
    
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add the service
    ui_automation_pb2_grpc.add_UIAutomationServiceServicer_to_server(
        EnhancedUIAutomationService(), server
    )
    
    # Listen on all interfaces
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Enhanced UI Automation gRPC server on {listen_addr}")
    
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop(5)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced UI Automation gRPC Server')
    parser.add_argument('--port', type=int, default=50051, help='Server port')
    args = parser.parse_args()
    
    # Run the server
    asyncio.run(serve(args.port))
