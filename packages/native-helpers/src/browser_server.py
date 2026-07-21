"""
Extended gRPC server implementation with browser automation capabilities.

This module extends the existing UI automation server to include Playwright-based
browser automation for web page interaction, DOM analysis, and form field typing.
"""

import asyncio
import json
import logging
from concurrent import futures
from typing import Any, Dict, List, Optional

import grpc

from .browser_automation import BrowserConfig, FieldInfo, PlaywrightBrowserAutomation
from .generated import ui_automation_pb2, ui_automation_pb2_grpc
from .server import UIAutomationServicer

logger = logging.getLogger(__name__)


class ExtendedUIAutomationServicer(UIAutomationServicer):
    """
    Extended gRPC servicer that includes browser automation capabilities.

    This class extends the base UIAutomationServicer with Playwright-based
    browser automation for web page interaction and form analysis.
    """

    def __init__(self):
        """Initialize the extended servicer with browser automation."""
        super().__init__()

        # Browser automation instances (one per browser type)
        self._browser_instances: Dict[str, PlaywrightBrowserAutomation] = {}
        self._browser_configs: Dict[str, BrowserConfig] = {}

        # Default browser config
        self._default_config = BrowserConfig(
            browser_type="chromium",
            headless=False,
            connect_to_existing=True,
            viewport_width=1366,
            viewport_height=768,
            timeout=30000,
        )

        logger.info("ExtendedUIAutomationServicer initialized with browser automation")

    async def _get_browser_instance(
        self, browser_type: str = "chromium"
    ) -> Optional[PlaywrightBrowserAutomation]:
        """Get or create a browser automation instance."""
        try:
            if browser_type not in self._browser_instances:
                config = self._browser_configs.get(browser_type, self._default_config)
                config.browser_type = browser_type

                browser = PlaywrightBrowserAutomation(config)
                await browser.start()

                self._browser_instances[browser_type] = browser
                logger.info(f"Created browser instance for {browser_type}")

            return self._browser_instances[browser_type]

        except Exception as e:
            logger.error(f"Failed to get browser instance for {browser_type}: {e}")
            return None

    async def NavigateToBrowser(
        self, request: ui_automation_pb2.NavigateBrowserRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.NavigateBrowserResponse:
        """Navigate browser to a specific URL."""
        try:
            logger.info(
                f"NavigateToBrowser request: url='{request.url}', browser='{request.browser_type}'"
            )

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.NavigateBrowserResponse(
                    success=False, message=f"Failed to initialize {browser_type} browser"
                )

            await browser.navigate(request.url)
            page_info = await browser.get_page_info()

            return ui_automation_pb2.NavigateBrowserResponse(
                success=True,
                message=f"Successfully navigated to {request.url}",
                page_title=page_info.get("title", ""),
                actual_url=page_info.get("url", request.url),
            )

        except Exception as e:
            logger.error(f"Error in NavigateToBrowser: {e}")
            return ui_automation_pb2.NavigateBrowserResponse(
                success=False, message=f"Failed to navigate: {str(e)}"
            )

    async def AnalyzeBrowserDOM(
        self, request: ui_automation_pb2.AnalyzeDOMRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.AnalyzeDOMResponse:
        """Analyze the DOM of the current browser page for input fields."""
        try:
            logger.info(f"AnalyzeBrowserDOM request: browser='{request.browser_type}'")

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.AnalyzeDOMResponse(
                    success=False, message=f"No active {browser_type} browser instance"
                )

            # Analyze DOM for input fields
            fields = await browser.analyze_dom()

            # Convert FieldInfo objects to protobuf messages
            pb_fields = []
            for field in fields:
                pb_field = ui_automation_pb2.BrowserFieldInfo(
                    field_id=field.field_id,
                    element_type=field.element_type,
                    input_type=field.input_type or "",
                    selector=field.selector,
                    xpath=field.xpath,
                    label=field.label or "",
                    placeholder=field.placeholder or "",
                    aria_label=field.aria_label or "",
                    name=field.name or "",
                    id=field.id or "",
                    class_name=field.class_name or "",
                    inferred_type=field.inferred_type,
                    confidence=field.confidence,
                    is_visible=field.is_visible,
                    is_enabled=field.is_enabled,
                )

                # Add bounds if available
                if field.bounds:
                    pb_field.bounds.x = field.bounds["x"]
                    pb_field.bounds.y = field.bounds["y"]
                    pb_field.bounds.width = field.bounds["width"]
                    pb_field.bounds.height = field.bounds["height"]

                pb_fields.append(pb_field)

            current_url = await browser.get_current_url()

            return ui_automation_pb2.AnalyzeDOMResponse(
                success=True,
                message=f"Found {len(fields)} input fields",
                current_url=current_url,
                fields=pb_fields,
            )

        except Exception as e:
            logger.error(f"Error in AnalyzeBrowserDOM: {e}")
            return ui_automation_pb2.AnalyzeDOMResponse(
                success=False, message=f"Failed to analyze DOM: {str(e)}"
            )

    async def TypeInBrowserField(
        self, request: ui_automation_pb2.TypeBrowserFieldRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.TypeBrowserFieldResponse:
        """Type text into a browser field with human-like delays."""
        try:
            logger.info(
                f"TypeInBrowserField request: field_selector='{request.field_selector}', "
                f"text='{request.text}', human_like={request.human_like}"
            )

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.TypeBrowserFieldResponse(
                    success=False, message=f"No active {browser_type} browser instance"
                )

            # Type text into the field
            success = await browser.type_text(
                field_selector=request.field_selector,
                text=request.text,
                human_like=request.human_like,
                clear_first=request.clear_first,
            )

            if success:
                return ui_automation_pb2.TypeBrowserFieldResponse(
                    success=True, message=f"Successfully typed text into field"
                )
            else:
                return ui_automation_pb2.TypeBrowserFieldResponse(
                    success=False, message="Failed to type text into field"
                )

        except Exception as e:
            logger.error(f"Error in TypeInBrowserField: {e}")
            return ui_automation_pb2.TypeBrowserFieldResponse(
                success=False, message=f"Failed to type in browser field: {str(e)}"
            )

    async def CaptureScreenshot(
        self, request: ui_automation_pb2.ScreenshotRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.ScreenshotResponse:
        """Capture a screenshot of the browser page or specific element."""
        try:
            logger.info(
                f"CaptureScreenshot request: browser='{request.browser_type}', "
                f"element_selector='{request.element_selector}', full_page={request.full_page}"
            )

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.ScreenshotResponse(
                    success=False, message=f"No active {browser_type} browser instance"
                )

            # Capture screenshot
            screenshot_bytes = await browser.capture_screenshot(
                path=request.save_path if request.save_path else None,
                element_selector=request.element_selector if request.element_selector else None,
                full_page=request.full_page,
            )

            return ui_automation_pb2.ScreenshotResponse(
                success=True,
                message="Screenshot captured successfully",
                screenshot_data=screenshot_bytes,
            )

        except Exception as e:
            logger.error(f"Error in CaptureScreenshot: {e}")
            return ui_automation_pb2.ScreenshotResponse(
                success=False, message=f"Failed to capture screenshot: {str(e)}"
            )

    async def GetBrowserPageInfo(
        self, request: ui_automation_pb2.GetPageInfoRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.GetPageInfoResponse:
        """Get information about the current browser page."""
        try:
            logger.info(f"GetBrowserPageInfo request: browser='{request.browser_type}'")

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.GetPageInfoResponse(
                    success=False, message=f"No active {browser_type} browser instance"
                )

            page_info = await browser.get_page_info()

            return ui_automation_pb2.GetPageInfoResponse(
                success=True,
                message="Page information retrieved",
                url=page_info.get("url", ""),
                title=page_info.get("title", ""),
                viewport_width=page_info.get("viewport", {}).get("width", 0),
                viewport_height=page_info.get("viewport", {}).get("height", 0),
                user_agent=page_info.get("user_agent", ""),
                fields_count=page_info.get("fields_count", 0),
            )

        except Exception as e:
            logger.error(f"Error in GetBrowserPageInfo: {e}")
            return ui_automation_pb2.GetPageInfoResponse(
                success=False, message=f"Failed to get page info: {str(e)}"
            )

    async def ClickBrowserElement(
        self,
        request: ui_automation_pb2.ClickBrowserElementRequest,
        context: grpc.aio.ServicerContext,
    ) -> ui_automation_pb2.ClickBrowserElementResponse:
        """Click an element in the browser."""
        try:
            logger.info(
                f"ClickBrowserElement request: selector='{request.selector}', "
                f"browser='{request.browser_type}'"
            )

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.ClickBrowserElementResponse(
                    success=False, message=f"No active {browser_type} browser instance"
                )

            # Click the element
            success = await browser.click_element(request.selector)

            if success:
                return ui_automation_pb2.ClickBrowserElementResponse(
                    success=True, message=f"Successfully clicked element: {request.selector}"
                )
            else:
                return ui_automation_pb2.ClickBrowserElementResponse(
                    success=False, message=f"Failed to click element: {request.selector}"
                )

        except Exception as e:
            logger.error(f"Error in ClickBrowserElement: {e}")
            return ui_automation_pb2.ClickBrowserElementResponse(
                success=False, message=f"Failed to click browser element: {str(e)}"
            )

    async def WaitForBrowserElement(
        self, request: ui_automation_pb2.WaitForElementRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.WaitForElementResponse:
        """Wait for an element to appear in the browser."""
        try:
            logger.info(
                f"WaitForBrowserElement request: selector='{request.selector}', "
                f"timeout={request.timeout}, browser='{request.browser_type}'"
            )

            browser_type = request.browser_type or "chromium"
            browser = await self._get_browser_instance(browser_type)

            if not browser:
                return ui_automation_pb2.WaitForElementResponse(
                    success=False, message=f"No active {browser_type} browser instance"
                )

            # Wait for element
            timeout = request.timeout if request.timeout > 0 else 5000
            success = await browser.wait_for_element(request.selector, timeout)

            if success:
                return ui_automation_pb2.WaitForElementResponse(
                    success=True, message=f"Element appeared: {request.selector}"
                )
            else:
                return ui_automation_pb2.WaitForElementResponse(
                    success=False,
                    message=f"Element did not appear within {timeout}ms: {request.selector}",
                )

        except Exception as e:
            logger.error(f"Error in WaitForBrowserElement: {e}")
            return ui_automation_pb2.WaitForElementResponse(
                success=False, message=f"Failed to wait for browser element: {str(e)}"
            )

    async def ConfigureBrowser(
        self, request: ui_automation_pb2.ConfigureBrowserRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.ConfigureBrowserResponse:
        """Configure browser settings."""
        try:
            logger.info(
                f"ConfigureBrowser request: browser='{request.browser_type}', "
                f"headless={request.headless}"
            )

            browser_type = request.browser_type or "chromium"

            # Create new configuration
            config = BrowserConfig(
                browser_type=browser_type,
                headless=request.headless,
                viewport_width=request.viewport_width if request.viewport_width > 0 else 1366,
                viewport_height=request.viewport_height if request.viewport_height > 0 else 768,
                timeout=request.timeout if request.timeout > 0 else 30000,
                connect_to_existing=request.connect_to_existing,
                user_agent=request.user_agent if request.user_agent else None,
            )

            # Store configuration
            self._browser_configs[browser_type] = config

            # If browser instance exists, close it so new config takes effect
            if browser_type in self._browser_instances:
                await self._browser_instances[browser_type].close()
                del self._browser_instances[browser_type]

            return ui_automation_pb2.ConfigureBrowserResponse(
                success=True, message=f"Browser configuration updated for {browser_type}"
            )

        except Exception as e:
            logger.error(f"Error in ConfigureBrowser: {e}")
            return ui_automation_pb2.ConfigureBrowserResponse(
                success=False, message=f"Failed to configure browser: {str(e)}"
            )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup browser instances."""
        for browser_type, browser in self._browser_instances.items():
            try:
                await browser.close()
                logger.info(f"Closed browser instance: {browser_type}")
            except Exception as e:
                logger.error(f"Error closing browser {browser_type}: {e}")

        self._browser_instances.clear()


# Additional helper functions for browser automation
async def create_extended_server(host: str = "localhost", port: int = 50051, max_workers: int = 10):
    """Create an extended gRPC server with browser automation capabilities."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    # Add the extended UI automation service
    servicer = ExtendedUIAutomationServicer()
    ui_automation_pb2_grpc.add_UIAutomationServiceServicer_to_server(servicer, server)

    # Configure server address
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)

    logger.info(f"Created extended gRPC server with browser automation on {listen_addr}")
    return server, servicer
