"""
gRPC server implementation for UI automation operations.
"""

import logging
import time
from typing import Optional, Tuple

import grpc
import pyautogui
import pygetwindow as gw
from pynput import keyboard, mouse
from pynput.keyboard import Key

from .generated import ui_automation_pb2, ui_automation_pb2_grpc
from .ui_automation import UIAutomationHandler

logger = logging.getLogger(__name__)


class UIAutomationServicer(ui_automation_pb2_grpc.UIAutomationServiceServicer):
    """gRPC servicer for UI automation operations."""

    def __init__(self) -> None:
        """Initialize the servicer."""
        self.ui_handler = UIAutomationHandler()
        logger.info("UIAutomationServicer initialized")

    async def TypeText(
        self, request: ui_automation_pb2.TypeTextRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.TypeTextResponse:
        """Type text into the active window."""
        try:
            logger.info(f"TypeText request: text='{request.text}', delay={request.delay}")

            # Use default delay if not specified
            delay = request.delay if request.delay > 0 else 10

            # Type the text with specified delay
            await self.ui_handler.type_text(request.text, delay / 1000.0)  # Convert to seconds

            return ui_automation_pb2.TypeTextResponse(
                success=True, message=f"Successfully typed text: '{request.text}'"
            )

        except Exception as e:
            logger.error(f"Error in TypeText: {e}")
            return ui_automation_pb2.TypeTextResponse(
                success=False, message=f"Failed to type text: {str(e)}"
            )

    async def SendKeys(
        self, request: ui_automation_pb2.SendKeysRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.SendKeysResponse:
        """Send key combinations."""
        try:
            logger.info(
                f"SendKeys request: keys='{request.keys}', modifiers={list(request.modifiers)}"
            )

            await self.ui_handler.send_keys(request.keys, list(request.modifiers))

            return ui_automation_pb2.SendKeysResponse(
                success=True, message=f"Successfully sent keys: '{request.keys}'"
            )

        except Exception as e:
            logger.error(f"Error in SendKeys: {e}")
            return ui_automation_pb2.SendKeysResponse(
                success=False, message=f"Failed to send keys: {str(e)}"
            )

    async def GetActiveWindow(
        self, request: ui_automation_pb2.GetActiveWindowRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.GetActiveWindowResponse:
        """Get information about the active window."""
        try:
            logger.info("GetActiveWindow request")

            window_info = await self.ui_handler.get_active_window()

            if window_info:
                # Convert to protobuf message
                pb_window = ui_automation_pb2.WindowInfo(
                    title=window_info["title"],
                    class_name=window_info["class_name"],
                    pid=window_info["pid"],
                    handle=window_info["handle"],
                    bounds=ui_automation_pb2.WindowBounds(
                        x=window_info["bounds"]["x"],
                        y=window_info["bounds"]["y"],
                        width=window_info["bounds"]["width"],
                        height=window_info["bounds"]["height"],
                    ),
                    is_active=window_info["is_active"],
                )

                return ui_automation_pb2.GetActiveWindowResponse(
                    success=True, window=pb_window, message="Active window information retrieved"
                )
            else:
                return ui_automation_pb2.GetActiveWindowResponse(
                    success=False, message="No active window found"
                )

        except Exception as e:
            logger.error(f"Error in GetActiveWindow: {e}")
            return ui_automation_pb2.GetActiveWindowResponse(
                success=False, message=f"Failed to get active window: {str(e)}"
            )

    async def FindElement(
        self, request: ui_automation_pb2.FindElementRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.FindElementResponse:
        """Find an element on the screen."""
        try:
            logger.info(
                f"FindElement request: selector='{request.selector}', method='{request.method}', timeout={request.timeout}"
            )

            timeout = request.timeout if request.timeout > 0 else 5000

            element_info = await self.ui_handler.find_element(
                request.selector, request.method, timeout / 1000.0  # Convert to seconds
            )

            if element_info:
                # Convert to protobuf message
                pb_element = ui_automation_pb2.ElementInfo(
                    id=element_info.get("id", ""),
                    name=element_info.get("name", ""),
                    class_name=element_info.get("class_name", ""),
                    bounds=ui_automation_pb2.ElementBounds(
                        x=element_info["bounds"]["x"],
                        y=element_info["bounds"]["y"],
                        width=element_info["bounds"]["width"],
                        height=element_info["bounds"]["height"],
                    ),
                    is_visible=element_info["is_visible"],
                    is_enabled=element_info["is_enabled"],
                    text=element_info.get("text", ""),
                    element_type=element_info["element_type"],
                )

                return ui_automation_pb2.FindElementResponse(
                    success=True, element=pb_element, message="Element found"
                )
            else:
                return ui_automation_pb2.FindElementResponse(
                    success=False, message="Element not found"
                )

        except Exception as e:
            logger.error(f"Error in FindElement: {e}")
            return ui_automation_pb2.FindElementResponse(
                success=False, message=f"Failed to find element: {str(e)}"
            )

    async def ClickElement(
        self, request: ui_automation_pb2.ClickElementRequest, context: grpc.aio.ServicerContext
    ) -> ui_automation_pb2.ClickElementResponse:
        """Click at specific coordinates."""
        try:
            logger.info(
                f"ClickElement request: x={request.x}, y={request.y}, button='{request.button}', double_click={request.double_click}"
            )

            button = request.button if request.button else "left"
            double_click = request.double_click if hasattr(request, "double_click") else False

            await self.ui_handler.click_element(request.x, request.y, button, double_click)

            click_type = "double-clicked" if double_click else "clicked"
            return ui_automation_pb2.ClickElementResponse(
                success=True,
                message=f"Successfully {click_type} at ({request.x}, {request.y}) with {button} button",
            )

        except Exception as e:
            logger.error(f"Error in ClickElement: {e}")
            return ui_automation_pb2.ClickElementResponse(
                success=False, message=f"Failed to click element: {str(e)}"
            )
