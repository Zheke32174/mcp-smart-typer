"""
Windows UIA Automation Module
Implements Windows desktop automation using pywinauto and uiautomation libraries.
Provides comprehensive UIA element enumeration and interaction capabilities.
"""

import hashlib
import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import pyautogui
import pywinauto
import uiautomation as auto
from pywinauto import Application, Desktop
from pywinauto.controls.common_controls import EditWrapper, RichEditWrapper
from uiautomation import Control

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global element cache to maintain references
_element_cache: Dict[str, Control] = {}
_cache_lock = threading.Lock()


class WindowsUIAAutomation:
    """
    Windows UIA Automation using pywinauto and uiautomation libraries.
    Supports enumeration of UIA elements and advanced text input methods.
    """

    def __init__(self):
        """Initialize the UIA automation handler."""
        self.desktop = Desktop(backend="uia")
        self.auto_desktop = auto.GetRootControl()
        logger.info("Windows UIA Automation initialized")

    def _generate_element_id(self, element: Control) -> str:
        """Generate a unique ID for a UIA element based on its properties."""
        try:
            # Create a hash based on element properties
            props = []
            props.append(str(element.AutomationId))
            props.append(str(element.Name))
            props.append(str(element.ClassName))
            props.append(str(element.ControlTypeName))
            props.append(str(element.ProcessId))

            # Add bounds if available
            try:
                rect = element.BoundingRectangle
                props.append(f"{rect.left},{rect.top},{rect.right},{rect.bottom}")
            except:
                props.append("no_bounds")

            # Create hash
            content = "|".join(props)
            element_hash = hashlib.md5(content.encode()).hexdigest()[:16]
            element_id = f"uia_{element_hash}_{int(time.time())}"

            # Cache the element
            with _cache_lock:
                _element_cache[element_id] = element

            return element_id
        except Exception as e:
            logger.error(f"Failed to generate element ID: {e}")
            return f"uia_unknown_{int(time.time())}"

    def _get_cached_element(self, element_id: str) -> Optional[Control]:
        """Retrieve a cached element by ID."""
        with _cache_lock:
            return _element_cache.get(element_id)

    def enumerate_uia_elements(
        self,
        window_title: Optional[str] = None,
        element_types: Optional[List[str]] = None,
        include_invisible: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Enumerate UIA elements of specified types.

        Args:
            window_title: Filter by window title (optional)
            element_types: List of element types to find (Edit, Document, RichEdit, etc.)
            include_invisible: Whether to include invisible elements

        Returns:
            List of element information dictionaries
        """
        if element_types is None:
            element_types = ["Edit", "Document", "RichEdit"]

        elements = []

        try:
            # Get all windows or filter by title
            if window_title:
                windows = auto.GetRootControl().GetChildren()
                windows = [w for w in windows if window_title.lower() in w.Name.lower()]
            else:
                windows = auto.GetRootControl().GetChildren()

            for window in windows:
                try:
                    if not window.IsEnabled:
                        continue

                    # Skip minimized windows unless explicitly requested
                    if not include_invisible and not window.IsVisible:
                        continue

                    # Search for elements of specified types
                    for element_type in element_types:
                        found_elements = self._find_elements_by_type(
                            window, element_type, include_invisible
                        )
                        elements.extend(found_elements)

                except Exception as e:
                    logger.warning(f"Error processing window {window.Name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error enumerating UIA elements: {e}")

        logger.info(f"Found {len(elements)} UIA elements")
        return elements

    def _find_elements_by_type(
        self, parent: Control, element_type: str, include_invisible: bool
    ) -> List[Dict[str, Any]]:
        """Find all elements of a specific type within a parent control."""
        elements = []

        try:
            # Map element types to UIA control types
            type_mapping = {
                "Edit": auto.ControlType.EditControl,
                "Document": auto.ControlType.DocumentControl,
                "RichEdit": auto.ControlType.EditControl,  # RichEdit is typically an EditControl
                "Text": auto.ControlType.TextControl,
                "ComboBox": auto.ControlType.ComboBoxControl,
                "ListBox": auto.ControlType.ListControl,
                "Button": auto.ControlType.ButtonControl,
            }

            control_type = type_mapping.get(element_type, auto.ControlType.EditControl)

            # Find all matching elements
            found_controls = parent.GetChildren()

            for control in found_controls:
                try:
                    # Check if it matches our target type
                    if control.ControlType == control_type:
                        if not include_invisible and not control.IsVisible:
                            continue

                        element_info = self._extract_element_info(control, element_type)
                        if element_info:
                            elements.append(element_info)

                    # Recursively search children
                    child_elements = self._find_elements_by_type(
                        control, element_type, include_invisible
                    )
                    elements.extend(child_elements)

                except Exception as e:
                    # Skip problematic elements
                    continue

        except Exception as e:
            logger.warning(f"Error finding elements of type {element_type}: {e}")

        return elements

    def _extract_element_info(
        self, element: Control, element_type: str
    ) -> Optional[Dict[str, Any]]:
        """Extract comprehensive information from a UIA element."""
        try:
            # Generate unique ID
            element_id = self._generate_element_id(element)

            # Get basic properties
            info = {
                "element_id": element_id,
                "name": getattr(element, "Name", "") or "",
                "automation_id": getattr(element, "AutomationId", "") or "",
                "class_name": getattr(element, "ClassName", "") or "",
                "control_type": element_type,
                "is_visible": getattr(element, "IsVisible", False),
                "is_enabled": getattr(element, "IsEnabled", False),
                "is_focusable": getattr(element, "IsKeyboardFocusable", False),
            }

            # Get bounds
            try:
                rect = element.BoundingRectangle
                info["bounds"] = {
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                }
            except:
                info["bounds"] = {"x": 0, "y": 0, "width": 0, "height": 0}

            # Get value if available
            try:
                if hasattr(element, "GetValuePattern"):
                    value_pattern = element.GetValuePattern()
                    if value_pattern:
                        info["value"] = value_pattern.Value
            except:
                info["value"] = None

            # Get help text
            try:
                info["help_text"] = getattr(element, "HelpText", "") or ""
            except:
                info["help_text"] = ""

            # Get labeled by information
            try:
                labeled_by = getattr(element, "LabeledBy", None)
                if labeled_by:
                    info["labeled_by"] = labeled_by.Name
                else:
                    info["labeled_by"] = ""
            except:
                info["labeled_by"] = ""

            # Get available control patterns
            info["control_patterns"] = self._get_control_patterns(element)

            # Get window information
            try:
                window = element.GetTopLevelWindow()
                if window:
                    info["window_title"] = window.Name
                    info["process_id"] = window.ProcessId
                else:
                    info["window_title"] = ""
                    info["process_id"] = 0
            except:
                info["window_title"] = ""
                info["process_id"] = 0

            return info

        except Exception as e:
            logger.error(f"Error extracting element info: {e}")
            return None

    def _get_control_patterns(self, element: Control) -> List[str]:
        """Get list of available control patterns for an element."""
        patterns = []

        try:
            # Check for common patterns
            pattern_checks = [
                ("ValuePattern", "GetValuePattern"),
                ("TextPattern", "GetTextPattern"),
                ("InvokePattern", "GetInvokePattern"),
                ("SelectionItemPattern", "GetSelectionItemPattern"),
                ("ExpandCollapsePattern", "GetExpandCollapsePattern"),
                ("TogglePattern", "GetTogglePattern"),
                ("RangeValuePattern", "GetRangeValuePattern"),
                ("ScrollPattern", "GetScrollPattern"),
            ]

            for pattern_name, method_name in pattern_checks:
                try:
                    if hasattr(element, method_name):
                        method = getattr(element, method_name)
                        if method and method():
                            patterns.append(pattern_name)
                except:
                    continue

        except Exception as e:
            logger.warning(f"Error getting control patterns: {e}")

        return patterns

    def get_element_details(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific element."""
        element = self._get_cached_element(element_id)
        if not element:
            return None

        return self._extract_element_info(element, "Unknown")

    def type_into_uia_element(
        self, element_id: str, text: str, clear_first: bool = False, use_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Type text into a UIA element using various methods.

        Args:
            element_id: ID of the element to type into
            text: Text to type
            clear_first: Whether to clear existing text first
            use_fallback: Whether to use pyautogui fallback if UIA fails

        Returns:
            Dictionary with success status and method used
        """
        element = self._get_cached_element(element_id)
        if not element:
            return {
                "success": False,
                "method_used": "none",
                "message": f"Element with ID {element_id} not found in cache",
            }

        try:
            # Method 1: Try ValuePattern.SetValue()
            try:
                value_pattern = element.GetValuePattern()
                if value_pattern and not value_pattern.IsReadOnly:
                    if clear_first:
                        value_pattern.SetValue("")
                    value_pattern.SetValue(text)
                    logger.info(f"Successfully typed using ValuePattern.SetValue")
                    return {
                        "success": True,
                        "method_used": "uia_set_value",
                        "message": "Text set using UIA ValuePattern",
                    }
            except Exception as e:
                logger.warning(f"ValuePattern failed: {e}")

            # Method 2: Try focus + SendKeys
            try:
                element.SetFocus()
                time.sleep(0.1)  # Brief pause for focus

                if clear_first:
                    element.SendKeys("{Ctrl}a{Delete}")
                    time.sleep(0.05)

                element.SendKeys(text)
                logger.info(f"Successfully typed using UIA SendKeys")
                return {
                    "success": True,
                    "method_used": "uia_send_keys",
                    "message": "Text sent using UIA SendKeys",
                }
            except Exception as e:
                logger.warning(f"UIA SendKeys failed: {e}")

            # Method 3: Fallback to pyautogui if enabled
            if use_fallback:
                try:
                    # Click on the element first
                    rect = element.BoundingRectangle
                    center_x = (rect.left + rect.right) // 2
                    center_y = (rect.top + rect.bottom) // 2

                    pyautogui.click(center_x, center_y)
                    time.sleep(0.1)

                    if clear_first:
                        pyautogui.hotkey("ctrl", "a")
                        time.sleep(0.05)
                        pyautogui.press("delete")
                        time.sleep(0.05)

                    # Type text with small delays for reliability
                    for char in text:
                        pyautogui.write(char)
                        time.sleep(0.01)  # Small delay between characters

                    logger.info(f"Successfully typed using pyautogui fallback")
                    return {
                        "success": True,
                        "method_used": "pyautogui",
                        "message": "Text typed using pyautogui fallback",
                    }
                except Exception as e:
                    logger.error(f"Pyautogui fallback failed: {e}")

            return {"success": False, "method_used": "none", "message": "All typing methods failed"}

        except Exception as e:
            logger.error(f"Error typing into element: {e}")
            return {"success": False, "method_used": "none", "message": f"Error: {str(e)}"}

    def click_element(self, element_id: str) -> Dict[str, Any]:
        """Click on a UIA element."""
        element = self._get_cached_element(element_id)
        if not element:
            return {"success": False, "message": f"Element with ID {element_id} not found in cache"}

        try:
            # Try UIA click first
            try:
                if hasattr(element, "Click"):
                    element.Click()
                    return {
                        "success": True,
                        "method_used": "uia_click",
                        "message": "Clicked using UIA",
                    }
            except Exception as e:
                logger.warning(f"UIA click failed: {e}")

            # Fallback to coordinate click
            try:
                rect = element.BoundingRectangle
                center_x = (rect.left + rect.right) // 2
                center_y = (rect.top + rect.bottom) // 2

                pyautogui.click(center_x, center_y)
                return {
                    "success": True,
                    "method_used": "coordinate_click",
                    "message": f"Clicked at coordinates ({center_x}, {center_y})",
                }
            except Exception as e:
                logger.error(f"Coordinate click failed: {e}")
                return {"success": False, "message": f"Click failed: {str(e)}"}

        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def focus_element(self, element_id: str) -> Dict[str, Any]:
        """Focus a UIA element."""
        element = self._get_cached_element(element_id)
        if not element:
            return {"success": False, "message": f"Element with ID {element_id} not found in cache"}

        try:
            element.SetFocus()
            return {"success": True, "message": "Element focused successfully"}
        except Exception as e:
            logger.error(f"Error focusing element: {e}")
            return {"success": False, "message": f"Focus failed: {str(e)}"}

    def get_element_text(self, element_id: str) -> Dict[str, Any]:
        """Get text content from a UIA element."""
        element = self._get_cached_element(element_id)
        if not element:
            return {
                "success": False,
                "message": f"Element with ID {element_id} not found in cache",
                "text": "",
            }

        try:
            # Try different methods to get text
            text = ""

            # Method 1: ValuePattern
            try:
                value_pattern = element.GetValuePattern()
                if value_pattern:
                    text = value_pattern.Value
                    if text:
                        return {"success": True, "text": text, "method_used": "value_pattern"}
            except:
                pass

            # Method 2: Direct Name property
            try:
                if element.Name:
                    text = element.Name
                    return {"success": True, "text": text, "method_used": "name_property"}
            except:
                pass

            # Method 3: TextPattern
            try:
                text_pattern = element.GetTextPattern()
                if text_pattern:
                    text = text_pattern.DocumentRange.GetText(-1)
                    return {"success": True, "text": text, "method_used": "text_pattern"}
            except:
                pass

            return {"success": False, "text": "", "message": "Could not retrieve text from element"}

        except Exception as e:
            logger.error(f"Error getting element text: {e}")
            return {"success": False, "text": "", "message": f"Error: {str(e)}"}

    def cleanup_cache(self, max_age_seconds: int = 3600):
        """Clean up old elements from cache."""
        try:
            current_time = int(time.time())
            with _cache_lock:
                keys_to_remove = []
                for key in _element_cache.keys():
                    # Extract timestamp from key
                    try:
                        timestamp = int(key.split("_")[-1])
                        if current_time - timestamp > max_age_seconds:
                            keys_to_remove.append(key)
                    except:
                        # Remove malformed keys
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    del _element_cache[key]

                logger.info(f"Cleaned up {len(keys_to_remove)} cached elements")
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")


# Test functions
def test_enumerate_elements():
    """Test element enumeration."""
    uia = WindowsUIAAutomation()

    print("Enumerating UIA elements...")
    elements = uia.enumerate_uia_elements(
        element_types=["Edit", "Document", "RichEdit"], include_invisible=False
    )

    print(f"Found {len(elements)} elements:")
    for i, element in enumerate(elements[:5]):  # Show first 5
        print(f"{i+1}. {element['name']} ({element['control_type']})")
        print(f"   Window: {element['window_title']}")
        print(f"   Bounds: {element['bounds']}")
        print(f"   Patterns: {element['control_patterns']}")
        print()


def test_typing():
    """Test typing into elements."""
    uia = WindowsUIAAutomation()

    # Find elements first
    elements = uia.enumerate_uia_elements(element_types=["Edit"])

    if not elements:
        print("No edit elements found for testing")
        return

    # Try typing into the first element
    element = elements[0]
    print(f"Testing typing into: {element['name']} in {element['window_title']}")

    result = uia.type_into_uia_element(
        element["element_id"], "Hello from UIA automation!", clear_first=True, use_fallback=True
    )

    print(f"Typing result: {result}")


if __name__ == "__main__":
    print("Windows UIA Automation Test")
    print("=" * 40)

    # Test enumeration
    test_enumerate_elements()

    # Uncomment to test typing (be careful!)
    # print("\n" + "=" * 40)
    # test_typing()
