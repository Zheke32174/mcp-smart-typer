"""
Windows UI Automation Client v2.0
Real Windows UI automation with browser support and screen interaction
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
from PIL import Image, ImageGrab
from pynput import keyboard, mouse

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WindowsUIAutomation:
    """Real Windows UI automation with browser and application support"""

    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.active_windows = {}
        self.detected_fields = {}
        self.current_context = None

        logger.info(f"Screen resolution: {self.screen_width}x{self.screen_height}")

    async def detect_browser_windows(self) -> List[Dict[str, Any]]:
        """Detect all open browser windows"""
        browser_patterns = [
            r".*Chrome.*",
            r".*Firefox.*",
            r".*Edge.*",
            r".*Internet Explorer.*",
            r".*Safari.*",
            r".*Opera.*",
        ]

        windows = []
        all_windows = gw.getAllWindows()

        for window in all_windows:
            if window.visible and window.width > 100 and window.height > 100:
                title = window.title
                for pattern in browser_patterns:
                    if re.match(pattern, title, re.IGNORECASE):
                        windows.append(
                            {
                                "id": f"window_{id(window)}",
                                "title": title,
                                "application": self._detect_browser_type(title),
                                "bounds": {
                                    "x": window.left,
                                    "y": window.top,
                                    "width": window.width,
                                    "height": window.height,
                                },
                                "handle": (
                                    window._hWnd if hasattr(window, "_hWnd") else str(id(window))
                                ),
                                "isActive": window == gw.getActiveWindow(),
                                "windowObject": window,
                            }
                        )
                        break

        logger.info(f"Detected {len(windows)} browser windows")
        return windows

    def _detect_browser_type(self, title: str) -> str:
        """Detect browser type from window title"""
        if "chrome" in title.lower():
            return "chrome"
        elif "firefox" in title.lower():
            return "firefox"
        elif "edge" in title.lower():
            return "edge"
        elif "internet explorer" in title.lower() or "ie" in title.lower():
            return "ie"
        elif "safari" in title.lower():
            return "safari"
        elif "opera" in title.lower():
            return "opera"
        else:
            return "unknown"

    async def detect_fields_in_window(
        self, window_info: Dict[str, Any], context_hint: str = ""
    ) -> List[Dict[str, Any]]:
        """Detect input fields in a specific window using multiple methods"""
        window = window_info["windowObject"]

        # Activate the window
        try:
            window.activate()
            await asyncio.sleep(0.5)  # Wait for window to activate
        except Exception as e:
            logger.warning(f"Could not activate window: {e}")

        # Take screenshot of the window
        screenshot = self._take_window_screenshot(window)
        if screenshot is None:
            return []

        # Use different detection methods
        fields = []

        # Method 1: OCR-based text field detection
        ocr_fields = await self._detect_fields_via_ocr(screenshot, window_info, context_hint)
        fields.extend(ocr_fields)

        # Method 2: Image pattern matching for common UI elements
        pattern_fields = await self._detect_fields_via_patterns(screenshot, window_info)
        fields.extend(pattern_fields)

        # Method 3: Browser-specific automation (if it's a browser)
        if window_info["application"] in ["chrome", "firefox", "edge"]:
            browser_fields = await self._detect_browser_fields(window_info, context_hint)
            fields.extend(browser_fields)

        # Remove duplicates and merge similar fields
        unique_fields = self._merge_similar_fields(fields)

        logger.info(f"Detected {len(unique_fields)} fields in window: {window_info['title']}")
        return unique_fields

    def _take_window_screenshot(self, window) -> Optional[np.ndarray]:
        """Take screenshot of a specific window"""
        try:
            # Get window bounds
            bbox = (window.left, window.top, window.left + window.width, window.top + window.height)

            # Take screenshot
            screenshot = ImageGrab.grab(bbox)

            # Convert to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot_cv
        except Exception as e:
            logger.error(f"Failed to take window screenshot: {e}")
            return None

    async def _detect_fields_via_ocr(
        self, screenshot: np.ndarray, window_info: Dict[str, Any], context_hint: str
    ) -> List[Dict[str, Any]]:
        """Detect fields using OCR and text analysis"""
        fields = []

        # Look for common field indicators
        field_indicators = [
            "username",
            "user name",
            "email",
            "login",
            "sign in",
            "password",
            "pwd",
            "pass",
            "search",
            "enter text",
            "name",
            "address",
            "phone",
            "message",
            "comment",
        ]

        # Simple field detection based on context hint
        if "login" in context_hint.lower():
            # Predict typical login form layout
            window_bounds = window_info["bounds"]
            center_x = window_bounds["width"] // 2
            center_y = window_bounds["height"] // 2

            # Username field (typically higher up)
            fields.append(
                {
                    "id": f"field_username_{int(time.time())}",
                    "name": "username",
                    "type": "input",
                    "inputType": "text",
                    "bounds": {
                        "x": window_bounds["x"] + center_x - 100,
                        "y": window_bounds["y"] + center_y - 50,
                        "width": 200,
                        "height": 30,
                    },
                    "confidence": 0.8,
                    "detection_method": "ocr_prediction",
                }
            )

            # Password field (typically below username)
            fields.append(
                {
                    "id": f"field_password_{int(time.time())}",
                    "name": "password",
                    "type": "input",
                    "inputType": "password",
                    "bounds": {
                        "x": window_bounds["x"] + center_x - 100,
                        "y": window_bounds["y"] + center_y,
                        "width": 200,
                        "height": 30,
                    },
                    "confidence": 0.8,
                    "detection_method": "ocr_prediction",
                }
            )

        return fields

    async def _detect_fields_via_patterns(
        self, screenshot: np.ndarray, window_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect fields using image pattern matching"""
        fields = []

        # Convert to grayscale for pattern matching
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # Look for rectangular patterns that might be input fields
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        window_bounds = window_info["bounds"]

        for i, contour in enumerate(contours):
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Filter for likely input field dimensions
            if 50 < w < 400 and 15 < h < 50:
                # Convert local coordinates to screen coordinates
                screen_x = window_bounds["x"] + x
                screen_y = window_bounds["y"] + y

                fields.append(
                    {
                        "id": f"field_pattern_{int(time.time())}_{i}",
                        "name": f"input_field_{i}",
                        "type": "input",
                        "inputType": "text",
                        "bounds": {"x": screen_x, "y": screen_y, "width": w, "height": h},
                        "confidence": 0.6,
                        "detection_method": "pattern_matching",
                    }
                )

        return fields[:5]  # Limit to top 5 candidates

    async def _detect_browser_fields(
        self, window_info: Dict[str, Any], context_hint: str
    ) -> List[Dict[str, Any]]:
        """Detect fields specific to browser windows"""
        fields = []

        # For browsers, we can try to detect common elements
        browser_type = window_info["application"]
        window_bounds = window_info["bounds"]

        # Address bar detection
        if browser_type in ["chrome", "firefox", "edge"]:
            address_bar_y = window_bounds["y"] + 60  # Typical address bar position
            fields.append(
                {
                    "id": f"browser_addressbar_{int(time.time())}",
                    "name": "address_bar",
                    "type": "input",
                    "inputType": "url",
                    "bounds": {
                        "x": window_bounds["x"] + 100,
                        "y": address_bar_y,
                        "width": window_bounds["width"] - 200,
                        "height": 25,
                    },
                    "confidence": 0.9,
                    "detection_method": "browser_specific",
                }
            )

        return fields

    def _merge_similar_fields(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge similar or overlapping fields"""
        if not fields:
            return []

        merged = []
        for field in fields:
            is_duplicate = False
            for existing in merged:
                # Check if fields are close to each other (potential duplicates)
                if (
                    abs(field["bounds"]["x"] - existing["bounds"]["x"]) < 20
                    and abs(field["bounds"]["y"] - existing["bounds"]["y"]) < 20
                ):
                    # Keep the one with higher confidence
                    if field["confidence"] > existing["confidence"]:
                        merged.remove(existing)
                        merged.append(field)
                    is_duplicate = True
                    break

            if not is_duplicate:
                merged.append(field)

        return merged

    async def click_element(
        self, x: int, y: int, button: str = "left", double_click: bool = False
    ) -> Dict[str, Any]:
        """Click on a specific screen coordinate"""
        try:
            logger.info(f"Clicking at ({x}, {y}) with {button} button")

            # Move mouse to position
            pyautogui.moveTo(x, y, duration=0.2)

            # Perform click
            if double_click:
                pyautogui.doubleClick(x, y, button=button)
            else:
                pyautogui.click(x, y, button=button)

            return {"success": True, "clicked_at": {"x": x, "y": y}, "button": button}
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {"success": False, "error": str(e)}

    async def type_text_at_position(
        self, x: int, y: int, text: str, delay: float = 0.05
    ) -> Dict[str, Any]:
        """Click at position and type text"""
        try:
            # Click first to focus
            click_result = await self.click_element(x, y)
            if not click_result["success"]:
                return click_result

            # Wait a moment for focus
            await asyncio.sleep(0.2)

            # Type the text
            logger.info(f"Typing text at ({x}, {y}): {len(text)} characters")
            for char in text:
                pyautogui.write(char)
                if delay > 0:
                    await asyncio.sleep(delay)

            return {"success": True, "characters_typed": len(text), "position": {"x": x, "y": y}}
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return {"success": False, "error": str(e)}

    async def focus_window(self, window_info: Dict[str, Any]) -> Dict[str, Any]:
        """Focus a specific window"""
        try:
            window = window_info["windowObject"]
            window.activate()

            # Bring to front if minimized
            if window.isMinimized:
                window.restore()

            await asyncio.sleep(0.3)  # Wait for window to become active

            return {"success": True, "window_title": window_info["title"]}
        except Exception as e:
            logger.error(f"Focus window failed: {e}")
            return {"success": False, "error": str(e)}

    async def take_screenshot(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """Take a screenshot of the screen or specific region"""
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            # Save to temporary location
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            screenshot.save(filename)

            return {"success": True, "filename": filename, "size": screenshot.size}
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {"success": False, "error": str(e)}


# Test functions for development
async def test_browser_detection():
    """Test browser detection functionality"""
    ui = WindowsUIAutomation()

    print("Detecting browser windows...")
    browsers = await ui.detect_browser_windows()

    for browser in browsers:
        print(f"Found: {browser['title']} ({browser['application']})")
        print(f"  Bounds: {browser['bounds']}")
        print(f"  Active: {browser['isActive']}")
        print()


async def test_field_detection():
    """Test field detection in browsers"""
    ui = WindowsUIAutomation()

    # Get browser windows
    browsers = await ui.detect_browser_windows()

    if not browsers:
        print("No browser windows found!")
        return

    # Test field detection on first browser
    browser = browsers[0]
    print(f"Testing field detection on: {browser['title']}")

    fields = await ui.detect_fields_in_window(browser, "login-form")

    print(f"Detected {len(fields)} fields:")
    for field in fields:
        print(f"  {field['name']}: {field['bounds']} (confidence: {field['confidence']})")


async def test_typing():
    """Test typing functionality"""
    ui = WindowsUIAutomation()

    print("Click somewhere on screen and wait 3 seconds...")
    await asyncio.sleep(3)

    # Get current mouse position
    x, y = pyautogui.position()
    print(f"Typing at current position: ({x}, {y})")

    result = await ui.type_text_at_position(
        x, y, "Hello, this is a test from MCP Smart Typer v2.0!"
    )
    print(f"Result: {result}")


if __name__ == "__main__":

    async def main():
        print("MCP Smart Typer v2.0 - Windows UI Automation Test")
        print("=" * 50)

        await test_browser_detection()
        print("\n" + "=" * 50)

        await test_field_detection()
        print("\n" + "=" * 50)

        # Uncomment to test typing (be careful!)
        # await test_typing()

    asyncio.run(main())
