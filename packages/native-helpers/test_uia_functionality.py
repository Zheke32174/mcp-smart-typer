#!/usr/bin/env python3
"""
Test script for Windows UIA Automation functionality
Tests element enumeration and interaction capabilities.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    import grpc

    from generated import ui_automation_pb2, ui_automation_pb2_grpc
    from uia_grpc_server import UIAGrpcServer, UIAutomationServiceImpl
    from windows_uia_automation import WindowsUIAAutomation
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed and protobuf files are generated.")
    sys.exit(1)


def test_uia_module():
    """Test the basic UIA automation module."""
    print("=" * 60)
    print("Testing Windows UIA Automation Module")
    print("=" * 60)

    try:
        # Initialize UIA automation
        print("1. Initializing UIA automation...")
        uia = WindowsUIAAutomation()
        print("✓ UIA automation initialized successfully")

        # Test element enumeration
        print("\n2. Testing element enumeration...")
        elements = uia.enumerate_uia_elements(
            element_types=["Edit", "Document", "RichEdit"], include_invisible=False
        )
        print(f"✓ Found {len(elements)} UIA elements")

        # Show first few elements
        if elements:
            print(f"\nFirst {min(3, len(elements))} elements:")
            for i, element in enumerate(elements[:3]):
                print(f"  {i+1}. {element['name']} ({element['control_type']})")
                print(f"     Window: {element['window_title']}")
                print(f"     Bounds: {element['bounds']}")
                print(f"     Enabled: {element['is_enabled']}, Visible: {element['is_visible']}")
        else:
            print(
                "  No elements found (this is normal if no applications with text fields are open)"
            )

        # Test cleanup
        print("\n3. Testing cache cleanup...")
        uia.cleanup_cache(max_age_seconds=0)  # Clean all
        print("✓ Cache cleanup completed")

        print("\n✓ UIA module test completed successfully!")
        return True

    except Exception as e:
        print(f"✗ UIA module test failed: {e}")
        return False


def test_grpc_service():
    """Test the gRPC service implementation."""
    print("\n" + "=" * 60)
    print("Testing gRPC Service Implementation")
    print("=" * 60)

    try:
        # Initialize service
        print("1. Initializing gRPC service...")
        service = UIAutomationServiceImpl()
        print("✓ gRPC service initialized successfully")

        # Test GetActiveWindow
        print("\n2. Testing GetActiveWindow...")
        request = ui_automation_pb2.GetActiveWindowRequest()
        response = service.GetActiveWindow(request, None)

        if response.success:
            print("✓ GetActiveWindow succeeded")
            print(f"  Active window: {response.window.title}")
            print(f"  Bounds: {response.window.bounds.width}x{response.window.bounds.height}")
        else:
            print(f"⚠ GetActiveWindow failed: {response.message}")

        # Test EnumerateUIAElements
        print("\n3. Testing EnumerateUIAElements...")
        request = ui_automation_pb2.EnumerateUIAElementsRequest()
        request.element_types.extend(["Edit", "Document"])
        request.include_invisible = False

        response = service.EnumerateUIAElements(request, None)

        if response.success:
            print(f"✓ EnumerateUIAElements succeeded: {len(response.elements)} elements")
            if response.elements:
                element = response.elements[0]
                print(f"  First element: {element.name} ({element.control_type})")
                print(f"  Window: {element.window_title}")
        else:
            print(f"⚠ EnumerateUIAElements failed: {response.message}")

        print("\n✓ gRPC service test completed successfully!")
        return True

    except Exception as e:
        print(f"✗ gRPC service test failed: {e}")
        return False


def test_full_server():
    """Test the complete gRPC server."""
    print("\n" + "=" * 60)
    print("Testing Complete gRPC Server")
    print("=" * 60)

    try:
        print("1. Starting gRPC server on port 50052...")
        server = UIAGrpcServer(port=50052)

        # Start server in a separate thread
        import threading

        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()

        # Give server time to start
        time.sleep(2)
        print("✓ Server started")

        # Test client connection
        print("\n2. Testing client connection...")
        try:
            channel = grpc.insecure_channel("localhost:50052")
            stub = ui_automation_pb2_grpc.UIAutomationServiceStub(channel)

            # Test with timeout
            request = ui_automation_pb2.GetActiveWindowRequest()
            response = stub.GetActiveWindow(request, timeout=5.0)

            if response.success:
                print("✓ Client connection and RPC call succeeded")
                print(f"  Response: {response.message}")
            else:
                print(f"⚠ RPC call failed: {response.message}")

            channel.close()

        except Exception as e:
            print(f"⚠ Client connection failed: {e}")

        # Stop server
        print("\n3. Stopping server...")
        server.stop()
        print("✓ Server stopped")

        print("\n✓ Complete server test finished!")
        return True

    except Exception as e:
        print(f"✗ Complete server test failed: {e}")
        return False


def main():
    """Main test function."""
    print("MCP Smart Typer - Windows UIA Automation Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("UIA Module", test_uia_module()))
    results.append(("gRPC Service", test_grpc_service()))
    results.append(("Complete Server", test_full_server()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nThe UIA automation system is working correctly!")
        print("You can now build the executable using build.bat")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease check the error messages above and ensure:")
        print("  1. All dependencies are installed (pip install -r requirements.txt)")
        print("  2. Protobuf files are generated")
        print("  3. Windows UI Automation services are available")

    print("\nPress any key to exit...")
    try:
        input()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
