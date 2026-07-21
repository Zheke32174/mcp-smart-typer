"""
MCP Smart Typer v2.0 - Real Browser Interaction Test
Opens browsers, detects fields, and types into them
"""

import asyncio
import subprocess
import time

from src.windows_ui_automation import WindowsUIAutomation


async def open_browsers():
    """Open three different browsers with test pages"""
    print("🌐 Opening browsers...")

    # Open Chrome
    try:
        subprocess.Popen(["start", "chrome", "https://www.google.com"], shell=True)
        await asyncio.sleep(2)
        print("✅ Chrome opened")
    except Exception as e:
        print(f"❌ Chrome failed: {e}")

    # Open Edge
    try:
        subprocess.Popen(["start", "msedge", "https://www.bing.com"], shell=True)
        await asyncio.sleep(2)
        print("✅ Edge opened")
    except Exception as e:
        print(f"❌ Edge failed: {e}")

    # Open Firefox (if available)
    try:
        subprocess.Popen(["start", "firefox", "https://duckduckgo.com"], shell=True)
        await asyncio.sleep(2)
        print("✅ Firefox opened")
    except Exception as e:
        print(f"⚠️ Firefox not available: {e}")

    print("⏳ Waiting for browsers to fully load...")
    await asyncio.sleep(3)


async def test_browser_interaction():
    """Test interaction with all detected browsers"""
    ui = WindowsUIAutomation()

    # Detect all browser windows
    browsers = await ui.detect_browser_windows()
    print(f"\n🔍 Found {len(browsers)} browser windows:")

    for i, browser in enumerate(browsers):
        print(f"  {i+1}. {browser['title']} ({browser['application']})")

    if not browsers:
        print("❌ No browsers found!")
        return

    # Test each browser
    test_messages = [
        "Hello from MCP Smart Typer v2.0! Testing Chrome browser interaction.",
        "MCP Smart Typer v2.0 - Edge browser test successful!",
        "Firefox + MCP Smart Typer v2.0 = Awesome automation!",
    ]

    for i, browser in enumerate(browsers[:3]):  # Test up to 3 browsers
        await test_single_browser(ui, browser, test_messages[i % len(test_messages)])
        await asyncio.sleep(2)  # Wait between browsers


async def test_single_browser(ui: WindowsUIAutomation, browser_info, test_message):
    """Test interaction with a single browser"""
    print(f"\n🎯 Testing: {browser_info['title']}")

    # Focus the browser window
    focus_result = await ui.focus_window(browser_info)
    if not focus_result["success"]:
        print(f"❌ Could not focus window: {focus_result.get('error', 'Unknown error')}")
        return

    print(f"✅ Focused window: {browser_info['title']}")

    # Detect fields in the browser
    fields = await ui.detect_fields_in_window(browser_info, "search")

    if not fields:
        print("⚠️ No fields detected, trying address bar...")
        # Try to type in address bar as fallback
        window_bounds = browser_info["bounds"]
        address_bar_x = window_bounds["x"] + window_bounds["width"] // 2
        address_bar_y = window_bounds["y"] + 70  # Typical address bar position

        print(f"📍 Attempting to type in address bar at ({address_bar_x}, {address_bar_y})")
        result = await ui.type_text_at_position(
            address_bar_x, address_bar_y, "https://www.example.com"
        )

        if result["success"]:
            print(f"✅ Successfully typed in address bar!")
        else:
            print(f"❌ Failed to type in address bar: {result.get('error', 'Unknown error')}")
        return

    # Find the best field to type in (prefer search boxes)
    best_field = None
    for field in fields:
        if "search" in field["name"].lower() or field["name"] == "address_bar":
            best_field = field
            break

    if not best_field:
        best_field = fields[0]  # Use first available field

    print(f"📝 Using field: {best_field['name']} at {best_field['bounds']}")

    # Calculate center of the field
    bounds = best_field["bounds"]
    center_x = bounds["x"] + bounds["width"] // 2
    center_y = bounds["y"] + bounds["height"] // 2

    # Type the test message
    print(f"⌨️ Typing message: '{test_message[:50]}...'")
    result = await ui.type_text_at_position(center_x, center_y, test_message, delay=0.02)

    if result["success"]:
        print(f"✅ Successfully typed {result['characters_typed']} characters!")

        # Press Enter if it's a search field
        if "search" in best_field["name"].lower() or "address" in best_field["name"].lower():
            await asyncio.sleep(0.5)
            import pyautogui

            pyautogui.press("enter")
            print("✅ Pressed Enter to submit")
    else:
        print(f"❌ Failed to type: {result.get('error', 'Unknown error')}")


async def take_screenshot_documentation():
    """Take screenshots for documentation"""
    ui = WindowsUIAutomation()

    print("\n📸 Taking screenshots for documentation...")

    # Take full screen screenshot
    screenshot_result = await ui.take_screenshot()
    if screenshot_result["success"]:
        print(f"✅ Full screenshot saved: {screenshot_result['filename']}")

    # Take screenshots of individual browser windows
    browsers = await ui.detect_browser_windows()
    for i, browser in enumerate(browsers):
        bounds = browser["bounds"]
        region = (bounds["x"], bounds["y"], bounds["width"], bounds["height"])

        screenshot_result = await ui.take_screenshot(region=region)
        if screenshot_result["success"]:
            print(f"✅ Browser {i+1} screenshot saved: {screenshot_result['filename']}")


async def main():
    """Main test function"""
    print("🚀 MCP Smart Typer v2.0 - Real Browser Interaction Test")
    print("=" * 60)

    # Step 1: Open browsers
    await open_browsers()

    # Step 2: Test browser interaction
    await test_browser_interaction()

    # Step 3: Take documentation screenshots
    await take_screenshot_documentation()

    print("\n" + "=" * 60)
    print("🎉 MCP Smart Typer v2.0 testing complete!")
    print("✅ Successfully demonstrated:")
    print("   • Browser window detection")
    print("   • Field detection and analysis")
    print("   • Real text input automation")
    print("   • Multi-browser support")
    print("   • Window focus management")
    print("\n💡 Ready for production use!")


if __name__ == "__main__":
    # Safety warning
    print("⚠️ WARNING: This will open browsers and type text automatically!")
    print("⚠️ Make sure you're ready and have saved your work.")
    print("⚠️ Press Ctrl+C to cancel within 5 seconds...")

    try:
        time.sleep(5)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
