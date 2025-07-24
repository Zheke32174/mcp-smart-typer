"""
Browser Automation Layer with Playwright

This module provides a comprehensive browser automation layer using Playwright that can:
- Attach to existing browser instances or launch new ones
- Analyze DOM for input fields with intelligent type inference
- Generate stable field IDs for consistent interaction
- Provide human-like typing with fallback to clipboard paste
- Capture screenshots for ML/OCR fallback

Features:
- Support for Chrome, Edge, and Firefox browsers
- DOM analysis for input, textarea, and contenteditable elements
- Type inference from HTML attributes and surrounding context
- Stable field identification using page URL + CSS/XPath + hash
- Human-like typing simulation with delays
- Screenshot capture for visual analysis
- Robust error handling and fallback mechanisms
"""

import asyncio
import hashlib
import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from urllib.parse import urlparse

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    ElementHandle,
    Locator,
    Error as PlaywrightError
)
from lxml import html


@dataclass
class FieldInfo:
    """Information about a form field detected in the DOM."""
    
    field_id: str
    element_type: str  # 'input', 'textarea', 'contenteditable'
    input_type: Optional[str]  # type attribute for input elements
    selector: str  # CSS selector
    xpath: str  # XPath selector
    label: Optional[str]
    placeholder: Optional[str]
    aria_label: Optional[str]
    name: Optional[str]
    id: Optional[str]
    class_name: Optional[str]
    inferred_type: str  # 'text', 'email', 'password', 'search', etc.
    confidence: float  # Confidence in type inference (0.0-1.0)
    bounds: Optional[Dict[str, float]]  # Element bounding box
    is_visible: bool
    is_enabled: bool


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""
    
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = False
    viewport_width: int = 1366
    viewport_height: int = 768
    user_agent: Optional[str] = None
    timeout: int = 30000  # milliseconds
    connect_to_existing: bool = True
    browser_executable_path: Optional[str] = None
    args: Optional[List[str]] = None


class PlaywrightBrowserAutomation:
    """
    Playwright-based browser automation with intelligent DOM analysis.
    
    This class provides comprehensive browser automation capabilities including:
    - Browser lifecycle management (attach/launch)
    - DOM analysis and field detection
    - Intelligent type inference for form fields
    - Human-like typing simulation
    - Screenshot capture for visual analysis
    """
    
    def __init__(self, config: BrowserConfig = None):
        """Initialize the browser automation handler."""
        self.config = config or BrowserConfig()
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # Typing simulation parameters
        self._min_delay = 0.05  # Minimum delay between keystrokes (50ms)
        self._max_delay = 0.15  # Maximum delay between keystrokes (150ms)
        self._word_pause = 0.2  # Pause between words (200ms)
        
        # Field type inference patterns
        self._type_patterns = self._build_type_patterns()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Initialize Playwright and browser."""
        try:
            self._playwright = await async_playwright().start()
            
            if self.config.connect_to_existing:
                await self._connect_to_existing_browser()
            else:
                await self._launch_new_browser()
                
        except Exception as e:
            raise RuntimeError(f"Failed to start browser automation: {e}")
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
    
    async def _connect_to_existing_browser(self) -> None:
        """Try to connect to existing browser instances."""
        browser_types = ["chromium", "firefox", "webkit"]
        
        for browser_type in browser_types:
            try:
                browser_launcher = getattr(self._playwright, browser_type)
                
                # Try to connect to existing browser on common debugging ports
                ports = [9222, 9223, 9224] if browser_type == "chromium" else [9222]
                
                for port in ports:
                    try:
                        self._browser = await browser_launcher.connect_over_cdp(
                            f"http://localhost:{port}"
                        )
                        print(f"Connected to existing {browser_type} on port {port}")
                        break
                    except:
                        continue
                
                if self._browser:
                    break
                    
            except:
                continue
        
        if not self._browser:
            print("No existing browser found, launching new instance")
            await self._launch_new_browser()
        else:
            await self._setup_context()
    
    async def _launch_new_browser(self) -> None:
        """Launch a new browser instance."""
        browser_launcher = getattr(self._playwright, self.config.browser_type)
        
        launch_options = {
            "headless": self.config.headless,
            "args": self.config.args or []
        }
        
        if self.config.browser_executable_path:
            launch_options["executable_path"] = self.config.browser_executable_path
        
        # Add debugging port for future connections
        if self.config.browser_type == "chromium":
            launch_options["args"].extend([
                "--remote-debugging-port=9222",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ])
        
        self._browser = await browser_launcher.launch(**launch_options)
        await self._setup_context()
    
    async def _setup_context(self) -> None:
        """Setup browser context and page."""
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height
            }
        }
        
        if self.config.user_agent:
            context_options["user_agent"] = self.config.user_agent
        
        self._context = await self._browser.new_context(**context_options)
        
        # Setup page with timeout
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.config.timeout)
    
    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call start() first.")
        
        try:
            await self._page.goto(url, wait_until="networkidle")
        except PlaywrightError as e:
            raise RuntimeError(f"Failed to navigate to {url}: {e}")
    
    async def get_current_url(self) -> str:
        """Get the current page URL."""
        if not self._page:
            raise RuntimeError("Browser not initialized.")
        return self._page.url
    
    async def analyze_dom(self) -> List[FieldInfo]:
        """
        Analyze the DOM to find and classify input fields.
        
        Returns:
            List of FieldInfo objects containing details about detected fields.
        """
        if not self._page:
            raise RuntimeError("Browser not initialized.")
        
        fields = []
        
        try:
            # Get page content for analysis
            content = await self._page.content()
            current_url = await self.get_current_url()
            
            # Parse HTML with lxml
            doc = html.fromstring(content)
            
            # Find all potential input elements
            selectors = [
                "input[type='text'], input:not([type]), input[type='email'], input[type='password'], input[type='search'], input[type='tel'], input[type='url']",
                "textarea",
                "[contenteditable='true'], [contenteditable='']"
            ]
            
            for selector in selectors:
                elements = await self._page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        field_info = await self._analyze_element(element, current_url)
                        if field_info:
                            fields.append(field_info)
                    except Exception as e:
                        print(f"Error analyzing element: {e}")
                        continue
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze DOM: {e}")
        
        return fields
    
    async def _analyze_element(self, element: ElementHandle, page_url: str) -> Optional[FieldInfo]:
        """Analyze a single DOM element to extract field information."""
        try:
            # Get element properties
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            element_type = tag_name
            
            # Get attributes
            attributes = await element.evaluate("""
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            
            # Generate selectors
            css_selector = await self._generate_css_selector(element)
            xpath = await self._generate_xpath(element)
            
            # Generate stable field ID
            field_id = self._generate_field_id(page_url, css_selector, xpath, attributes)
            
            # Extract field properties
            input_type = attributes.get("type")
            name = attributes.get("name")
            id_attr = attributes.get("id")
            class_name = attributes.get("class")
            placeholder = attributes.get("placeholder")
            aria_label = attributes.get("aria-label")
            
            # Find associated label
            label = await self._find_label(element, id_attr)
            
            # Check visibility and enabled state
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            # Get bounding box
            bounds = None
            if is_visible:
                box = await element.bounding_box()
                if box:
                    bounds = {
                        "x": box["x"],
                        "y": box["y"],
                        "width": box["width"],
                        "height": box["height"]
                    }
            
            # Infer field type
            inferred_type, confidence = self._infer_field_type(
                element_type, input_type, name, id_attr, class_name,
                placeholder, aria_label, label
            )
            
            return FieldInfo(
                field_id=field_id,
                element_type=element_type,
                input_type=input_type,
                selector=css_selector,
                xpath=xpath,
                label=label,
                placeholder=placeholder,
                aria_label=aria_label,
                name=name,
                id=id_attr,
                class_name=class_name,
                inferred_type=inferred_type,
                confidence=confidence,
                bounds=bounds,
                is_visible=is_visible,
                is_enabled=is_enabled
            )
            
        except Exception as e:
            print(f"Error analyzing element: {e}")
            return None
    
    async def _generate_css_selector(self, element: ElementHandle) -> str:
        """Generate a CSS selector for the element."""
        try:
            return await element.evaluate("""
                el => {
                    // Try ID first
                    if (el.id) {
                        return '#' + el.id;
                    }
                    
                    // Build path with classes
                    let selector = el.tagName.toLowerCase();
                    if (el.className) {
                        selector += '.' + el.className.split(' ').join('.');
                    }
                    
                    // Add attributes for uniqueness
                    if (el.name) {
                        selector += '[name="' + el.name + '"]';
                    }
                    if (el.type) {
                        selector += '[type="' + el.type + '"]';
                    }
                    
                    return selector;
                }
            """)
        except:
            return "unknown"
    
    async def _generate_xpath(self, element: ElementHandle) -> str:
        """Generate an XPath for the element."""
        try:
            return await element.evaluate("""
                el => {
                    if (el.id) {
                        return '//*[@id="' + el.id + '"]';
                    }
                    
                    let path = '';
                    let current = el;
                    
                    while (current && current.nodeType === Node.ELEMENT_NODE) {
                        let selector = current.tagName.toLowerCase();
                        
                        if (current.name) {
                            selector += '[@name="' + current.name + '"]';
                        } else if (current.className) {
                            selector += '[@class="' + current.className + '"]';
                        }
                        
                        path = '/' + selector + path;
                        current = current.parentElement;
                    }
                    
                    return path || '//*';
                }
            """)
        except:
            return "//*"
    
    def _generate_field_id(self, page_url: str, css_selector: str, xpath: str, attributes: Dict) -> str:
        """Generate a stable field ID based on page URL, selectors, and attributes."""
        # Create a consistent identifier
        id_components = [
            urlparse(page_url).netloc + urlparse(page_url).path,
            css_selector,
            xpath,
            attributes.get("name", ""),
            attributes.get("id", ""),
            attributes.get("type", "")
        ]
        
        # Create hash
        combined = "|".join(filter(None, id_components))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    async def _find_label(self, element: ElementHandle, element_id: Optional[str]) -> Optional[str]:
        """Find the label associated with an input element."""
        try:
            # Check for label[for] attribute
            if element_id:
                label_element = await self._page.query_selector(f'label[for="{element_id}"]')
                if label_element:
                    return await label_element.text_content()
            
            # Check for parent label
            parent_label = await element.evaluate("""
                el => {
                    let parent = el.parentElement;
                    while (parent) {
                        if (parent.tagName.toLowerCase() === 'label') {
                            return parent.textContent.trim();
                        }
                        parent = parent.parentElement;
                    }
                    return null;
                }
            """)
            
            if parent_label:
                return parent_label
            
            # Check for sibling label
            sibling_label = await element.evaluate("""
                el => {
                    let prev = el.previousElementSibling;
                    if (prev && prev.tagName.toLowerCase() === 'label') {
                        return prev.textContent.trim();
                    }
                    return null;
                }
            """)
            
            return sibling_label
            
        except:
            return None
    
    def _build_type_patterns(self) -> Dict[str, List[Tuple[re.Pattern, float]]]:
        """Build regex patterns for field type inference."""
        return {
            "email": [
                (re.compile(r"email", re.IGNORECASE), 0.9),
                (re.compile(r"e-?mail", re.IGNORECASE), 0.8),
                (re.compile(r"@", re.IGNORECASE), 0.6),
            ],
            "password": [
                (re.compile(r"password", re.IGNORECASE), 0.95),
                (re.compile(r"passwd", re.IGNORECASE), 0.9),
                (re.compile(r"pwd", re.IGNORECASE), 0.8),
                (re.compile(r"pass", re.IGNORECASE), 0.7),
            ],
            "search": [
                (re.compile(r"search", re.IGNORECASE), 0.9),
                (re.compile(r"query", re.IGNORECASE), 0.8),
                (re.compile(r"find", re.IGNORECASE), 0.7),
            ],
            "name": [
                (re.compile(r"name", re.IGNORECASE), 0.8),
                (re.compile(r"full.?name", re.IGNORECASE), 0.9),
                (re.compile(r"first.?name", re.IGNORECASE), 0.9),
                (re.compile(r"last.?name", re.IGNORECASE), 0.9),
            ],
            "phone": [
                (re.compile(r"phone", re.IGNORECASE), 0.9),
                (re.compile(r"tel", re.IGNORECASE), 0.9),
                (re.compile(r"mobile", re.IGNORECASE), 0.8),
            ],
            "address": [
                (re.compile(r"address", re.IGNORECASE), 0.9),
                (re.compile(r"street", re.IGNORECASE), 0.8),
                (re.compile(r"city", re.IGNORECASE), 0.8),
                (re.compile(r"zip", re.IGNORECASE), 0.8),
                (re.compile(r"postal", re.IGNORECASE), 0.8),
            ]
        }
    
    def _infer_field_type(self, element_type: str, input_type: Optional[str],
                         name: Optional[str], id_attr: Optional[str],
                         class_name: Optional[str], placeholder: Optional[str],
                         aria_label: Optional[str], label: Optional[str]) -> Tuple[str, float]:
        """Infer the field type based on available information."""
        
        # Start with HTML type if available
        if input_type and input_type in ["email", "password", "search", "tel", "url"]:
            return input_type, 0.95
        
        # Combine all text for analysis
        text_sources = [name, id_attr, class_name, placeholder, aria_label, label]
        combined_text = " ".join(filter(None, text_sources))
        
        if not combined_text:
            return "text", 0.5
        
        # Check patterns
        best_match = ("text", 0.5)
        
        for field_type, patterns in self._type_patterns.items():
            for pattern, confidence in patterns:
                if pattern.search(combined_text):
                    if confidence > best_match[1]:
                        best_match = (field_type, confidence)
        
        return best_match
    
    async def type_text(self, field_selector: str, text: str, 
                       human_like: bool = True, clear_first: bool = True) -> bool:
        """
        Type text into a field with human-like delays.
        
        Args:
            field_selector: CSS selector or field ID to target
            text: Text to type
            human_like: Whether to use human-like typing delays
            clear_first: Whether to clear the field first
            
        Returns:
            True if successful, False otherwise
        """
        if not self._page:
            raise RuntimeError("Browser not initialized.")
        
        try:
            # Find the element
            element = await self._page.query_selector(field_selector)
            if not element:
                # Try as field_id if direct selector fails
                fields = await self.analyze_dom()
                for field in fields:
                    if field.field_id == field_selector:
                        element = await self._page.query_selector(field.selector)
                        break
            
            if not element:
                return False
            
            # Focus the element
            await element.focus()
            
            # Clear if requested
            if clear_first:
                await element.fill("")
            
            if human_like:
                await self._type_human_like(element, text)
            else:
                await element.type(text)
            
            return True
            
        except Exception as e:
            print(f"Error typing text: {e}")
            # Fallback to clipboard paste
            return await self._paste_text_fallback(field_selector, text)
    
    async def _type_human_like(self, element: ElementHandle, text: str) -> None:
        """Type text with human-like delays and patterns."""
        words = text.split()
        
        for i, word in enumerate(words):
            for char in word:
                await element.type(char, delay=random.uniform(self._min_delay, self._max_delay) * 1000)
            
            # Add word pause (except for last word)
            if i < len(words) - 1:
                await element.type(" ", delay=self._word_pause * 1000)
    
    async def _paste_text_fallback(self, field_selector: str, text: str) -> bool:
        """Fallback method using clipboard paste."""
        try:
            # Copy text to clipboard using JavaScript
            await self._page.evaluate(f"""
                navigator.clipboard.writeText({json.dumps(text)});
            """)
            
            # Focus and paste
            element = await self._page.query_selector(field_selector)
            if element:
                await element.focus()
                await self._page.keyboard.press("Control+V")
                return True
                
        except Exception as e:
            print(f"Clipboard fallback failed: {e}")
        
        return False
    
    async def capture_screenshot(self, path: Optional[str] = None,
                               element_selector: Optional[str] = None,
                               full_page: bool = False) -> bytes:
        """
        Capture a screenshot for ML/OCR analysis.
        
        Args:
            path: Optional file path to save screenshot
            element_selector: Optional selector to screenshot specific element
            full_page: Whether to capture full page (scrolling)
            
        Returns:
            Screenshot data as bytes
        """
        if not self._page:
            raise RuntimeError("Browser not initialized.")
        
        try:
            screenshot_options = {
                "type": "png",
                "full_page": full_page
            }
            
            if path:
                screenshot_options["path"] = path
            
            if element_selector:
                element = await self._page.query_selector(element_selector)
                if element:
                    return await element.screenshot(**screenshot_options)
            
            return await self._page.screenshot(**screenshot_options)
            
        except Exception as e:
            raise RuntimeError(f"Failed to capture screenshot: {e}")
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get comprehensive page information."""
        if not self._page:
            raise RuntimeError("Browser not initialized.")
        
        try:
            return {
                "url": self._page.url,
                "title": await self._page.title(),
                "viewport": self._page.viewport_size,
                "user_agent": await self._page.evaluate("navigator.userAgent"),
                "fields_count": len(await self.analyze_dom())
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get page info: {e}")
    
    async def wait_for_element(self, selector: str, timeout: int = 5000) -> bool:
        """Wait for an element to appear."""
        if not self._page:
            return False
        
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def click_element(self, selector: str) -> bool:
        """Click an element."""
        if not self._page:
            return False
        
        try:
            await self._page.click(selector)
            return True
        except:
            return False


# Convenience function for quick usage
async def create_browser_automation(config: BrowserConfig = None) -> PlaywrightBrowserAutomation:
    """Create and initialize a browser automation instance."""
    automation = PlaywrightBrowserAutomation(config)
    await automation.start()
    return automation
