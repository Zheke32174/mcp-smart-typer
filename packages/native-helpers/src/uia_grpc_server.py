"""
gRPC Server for Windows UIA Automation

Implements the UIAutomationService gRPC interface with Windows UIA capabilities.
Provides comprehensive element enumeration and interaction via gRPC.
"""

import asyncio
import logging
import threading
import time
from concurrent import futures
from typing import Dict, List, Any

import grpc
from grpc import aio

# Import generated protobuf classes
from generated import ui_automation_pb2
from generated import ui_automation_pb2_grpc

# Import our UIA automation module
from windows_uia_automation import WindowsUIAAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UIAutomationServiceImpl(ui_automation_pb2_grpc.UIAutomationServiceServicer):
    """
    gRPC service implementation for Windows UIA automation.
    """

    def __init__(self):
        """Initialize the service with UIA automation handler."""
        self.uia = WindowsUIAAutomation()
        logger.info("UIAutomationService initialized")

    def TypeText(self, request, context):
        """Type text into the currently focused element."""
        try:
            logger.info(f"TypeText request: '{request.text}' with delay {request.delay}")
            
            # Use pyautogui for simple text typing
            import pyautogui
            
            delay = request.delay if request.delay else 0.05
            
            for char in request.text:
                pyautogui.write(char)
                if delay > 0:
                    time.sleep(delay / 1000.0)  # Convert milliseconds to seconds
            
            return ui_automation_pb2.TypeTextResponse(
                success=True,
                message="Text typed successfully"
            )
            
        except Exception as e:
            logger.error(f"TypeText failed: {e}")
            return ui_automation_pb2.TypeTextResponse(
                success=False,
                message=f"Failed to type text: {str(e)}"
            )

    def SendKeys(self, request, context):
        """Send key combinations."""
        try:
            logger.info(f"SendKeys request: '{request.keys}' with modifiers {list(request.modifiers)}")
            
            import pyautogui
            
            # Handle modifiers and keys
            modifiers = list(request.modifiers)
            keys = request.keys
            
            if modifiers:
                # Build hotkey combination
                hotkey_combo = modifiers + [keys]
                pyautogui.hotkey(*hotkey_combo)
            else:
                # Just press the key
                pyautogui.press(keys)
            
            return ui_automation_pb2.SendKeysResponse(
                success=True,
                message="Keys sent successfully"
            )
            
        except Exception as e:
            logger.error(f"SendKeys failed: {e}")
            return ui_automation_pb2.SendKeysResponse(
                success=False,
                message=f"Failed to send keys: {str(e)}"
            )

    def GetActiveWindow(self, request, context):
        """Get information about the active window."""
        try:
            logger.info("GetActiveWindow request")
            
            import pygetwindow as gw
            
            active_window = gw.getActiveWindow()
            if not active_window:
                return ui_automation_pb2.GetActiveWindowResponse(
                    success=False,
                    message="No active window found"
                )
            
            window_info = ui_automation_pb2.WindowInfo(
                title=active_window.title,
                class_name=str(getattr(active_window, '_hWnd', 'unknown')),
                pid=getattr(active_window, 'processId', 0),
                handle=str(getattr(active_window, '_hWnd', 'unknown')),
                bounds=ui_automation_pb2.WindowBounds(
                    x=active_window.left,
                    y=active_window.top,
                    width=active_window.width,
                    height=active_window.height
                ),
                is_active=True
            )
            
            return ui_automation_pb2.GetActiveWindowResponse(
                success=True,
                window=window_info,
                message="Active window retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"GetActiveWindow failed: {e}")
            return ui_automation_pb2.GetActiveWindowResponse(
                success=False,
                message=f"Failed to get active window: {str(e)}"
            )

    def FindElement(self, request, context):
        """Find an element on the screen (legacy method)."""
        try:
            logger.info(f"FindElement request: selector='{request.selector}', method='{request.method}'")
            
            # This is a simplified implementation
            # In practice, you might want to integrate with the UIA enumeration
            
            return ui_automation_pb2.FindElementResponse(
                success=False,
                message="Use EnumerateUIAElements for more reliable element discovery"
            )
            
        except Exception as e:
            logger.error(f"FindElement failed: {e}")
            return ui_automation_pb2.FindElementResponse(
                success=False,
                message=f"FindElement failed: {str(e)}"
            )

    def ClickElement(self, request, context):
        """Click at specific coordinates."""
        try:
            logger.info(f"ClickElement request: ({request.x}, {request.y}), button='{request.button}'")
            
            import pyautogui
            
            button = request.button or 'left'
            
            if request.double_click:
                pyautogui.doubleClick(request.x, request.y, button=button)
            else:
                pyautogui.click(request.x, request.y, button=button)
            
            return ui_automation_pb2.ClickElementResponse(
                success=True,
                message=f"Clicked at ({request.x}, {request.y}) with {button} button"
            )
            
        except Exception as e:
            logger.error(f"ClickElement failed: {e}")
            return ui_automation_pb2.ClickElementResponse(
                success=False,
                message=f"Click failed: {str(e)}"
            )

    def EnumerateUIAElements(self, request, context):
        """Enumerate UIA elements (Edit, Document, RichEdit)."""
        try:
            logger.info(f"EnumerateUIAElements request: window_title='{request.window_title}', types={list(request.element_types)}")
            
            # Extract parameters
            window_title = request.window_title if request.window_title else None
            element_types = list(request.element_types) if request.element_types else None
            include_invisible = request.include_invisible
            
            # Enumerate elements
            elements_data = self.uia.enumerate_uia_elements(
                window_title=window_title,
                element_types=element_types,
                include_invisible=include_invisible
            )
            
            # Convert to protobuf format
            uia_elements = []
            for element_data in elements_data:
                uia_element = ui_automation_pb2.UIAElementInfo(
                    element_id=element_data.get('element_id', ''),
                    name=element_data.get('name', ''),
                    automation_id=element_data.get('automation_id', ''),
                    class_name=element_data.get('class_name', ''),
                    control_type=element_data.get('control_type', ''),
                    bounds=ui_automation_pb2.ElementBounds(
                        x=element_data.get('bounds', {}).get('x', 0),
                        y=element_data.get('bounds', {}).get('y', 0),
                        width=element_data.get('bounds', {}).get('width', 0),
                        height=element_data.get('bounds', {}).get('height', 0)
                    ),
                    is_visible=element_data.get('is_visible', False),
                    is_enabled=element_data.get('is_enabled', False),
                    is_focusable=element_data.get('is_focusable', False),
                    value=element_data.get('value', '') or '',  # Handle None values
                    help_text=element_data.get('help_text', ''),
                    labeled_by=element_data.get('labeled_by', ''),
                    control_patterns=element_data.get('control_patterns', []),
                    window_title=element_data.get('window_title', ''),
                    process_id=element_data.get('process_id', 0)
                )
                uia_elements.append(uia_element)
            
            return ui_automation_pb2.EnumerateUIAElementsResponse(
                success=True,
                elements=uia_elements,
                message=f"Found {len(uia_elements)} UIA elements"
            )
            
        except Exception as e:
            logger.error(f"EnumerateUIAElements failed: {e}")
            return ui_automation_pb2.EnumerateUIAElementsResponse(
                success=False,
                elements=[],
                message=f"Failed to enumerate UIA elements: {str(e)}"
            )

    def TypeIntoUIAElement(self, request, context):
        """Type text into a specific UIA element."""
        try:
            logger.info(f"TypeIntoUIAElement request: element_id='{request.element_id}', text='{request.text}'")
            
            # Type into the element using our UIA automation
            result = self.uia.type_into_uia_element(
                element_id=request.element_id,
                text=request.text,
                clear_first=request.clear_first,
                use_fallback=request.use_fallback
            )
            
            return ui_automation_pb2.TypeIntoUIAElementResponse(
                success=result.get('success', False),
                method_used=result.get('method_used', 'unknown'),
                message=result.get('message', 'No message')
            )
            
        except Exception as e:
            logger.error(f"TypeIntoUIAElement failed: {e}")
            return ui_automation_pb2.TypeIntoUIAElementResponse(
                success=False,
                method_used='error',
                message=f"Failed to type into UIA element: {str(e)}"
            )

    def GetElementDetails(self, request, context):
        """Get detailed information about a specific element."""
        try:
            logger.info(f"GetElementDetails request: element_id='{request.element_id}'")
            
            # Get element details
            element_data = self.uia.get_element_details(request.element_id)
            
            if not element_data:
                return ui_automation_pb2.GetElementDetailsResponse(
                    success=False,
                    message=f"Element with ID '{request.element_id}' not found"
                )
            
            # Convert to protobuf format
            uia_element = ui_automation_pb2.UIAElementInfo(
                element_id=element_data.get('element_id', ''),
                name=element_data.get('name', ''),
                automation_id=element_data.get('automation_id', ''),
                class_name=element_data.get('class_name', ''),
                control_type=element_data.get('control_type', ''),
                bounds=ui_automation_pb2.ElementBounds(
                    x=element_data.get('bounds', {}).get('x', 0),
                    y=element_data.get('bounds', {}).get('y', 0),
                    width=element_data.get('bounds', {}).get('width', 0),
                    height=element_data.get('bounds', {}).get('height', 0)
                ),
                is_visible=element_data.get('is_visible', False),
                is_enabled=element_data.get('is_enabled', False),
                is_focusable=element_data.get('is_focusable', False),
                value=element_data.get('value', '') or '',
                help_text=element_data.get('help_text', ''),
                labeled_by=element_data.get('labeled_by', ''),
                control_patterns=element_data.get('control_patterns', []),
                window_title=element_data.get('window_title', ''),
                process_id=element_data.get('process_id', 0)
            )
            
            return ui_automation_pb2.GetElementDetailsResponse(
                success=True,
                element=uia_element,
                message="Element details retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"GetElementDetails failed: {e}")
            return ui_automation_pb2.GetElementDetailsResponse(
                success=False,
                message=f"Failed to get element details: {str(e)}"
            )


class UIAGrpcServer:
    """
    gRPC server for Windows UIA automation.
    """
    
    def __init__(self, port: int = 50051):
        """Initialize the gRPC server."""
        self.port = port
        self.server = None
        self._stop_event = threading.Event()
        
    def start(self):
        """Start the gRPC server."""
        try:
            # Create server with thread pool
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Add the service
            ui_automation_pb2_grpc.add_UIAutomationServiceServicer_to_server(
                UIAutomationServiceImpl(), self.server
            )
            
            # Add insecure port
            listen_addr = f'[::]:{self.port}'
            self.server.add_insecure_port(listen_addr)
            
            # Start server
            self.server.start()
            logger.info(f"UIAutomation gRPC server started on port {self.port}")
            
            # Wait for stop signal
            try:
                while not self._stop_event.is_set():
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the gRPC server."""
        if self.server:
            logger.info("Stopping gRPC server...")
            self.server.stop(0)
            self.server = None
        self._stop_event.set()


def main():
    """Main entry point for the gRPC server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Windows UIA gRPC Server")
    parser.add_argument(
        '--port', 
        type=int, 
        default=50051, 
        help='Port to listen on (default: 50051)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start server
    server = UIAGrpcServer(port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
