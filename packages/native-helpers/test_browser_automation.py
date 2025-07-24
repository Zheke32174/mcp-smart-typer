#!/usr/bin/env python3
"""
Test script for Playwright Browser Automation

This script demonstrates the browser automation capabilities including:
- Connecting to existing browsers or launching new ones
- DOM analysis and field detection
- Type inference for form fields
- Human-like typing simulation
- Screenshot capture

Usage:
    python test_browser_automation.py [--url URL] [--headless] [--browser TYPE]
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_automation import PlaywrightBrowserAutomation, BrowserConfig, FieldInfo


async def test_google_search():
    """Test basic functionality with Google search."""
    print("🚀 Testing browser automation with Google search...")
    
    config = BrowserConfig(
        browser_type="chromium",
        headless=False,
        connect_to_existing=True
    )
    
    async with PlaywrightBrowserAutomation(config) as browser:
        # Navigate to Google
        print("📍 Navigating to Google...")
        await browser.navigate("https://www.google.com")
        
        # Get page info
        page_info = await browser.get_page_info()
        print(f"📄 Page: {page_info['title']} - {page_info['url']}")
        print(f"👀 Viewport: {page_info['viewport']}")
        print(f"🔍 Fields found: {page_info['fields_count']}")
        
        # Analyze DOM
        print("\n🔍 Analyzing DOM for input fields...")
        fields = await browser.analyze_dom()
        
        print(f"Found {len(fields)} input fields:")
        for i, field in enumerate(fields[:5]):  # Show first 5 fields
            print(f"  {i+1}. {field.inferred_type} field (confidence: {field.confidence:.2f})")
            print(f"     Label: {field.label or 'N/A'}")
            print(f"     Placeholder: {field.placeholder or 'N/A'}")
            print(f"     Selector: {field.selector}")
            print()
        
        # Find the search box and type in it
        search_field = None
        for field in fields:
            if field.inferred_type == "search" or "search" in (field.name or "").lower():
                search_field = field
                break
        
        if search_field:
            print(f"🎯 Found search field: {search_field.field_id}")
            print("⌨️  Typing search query with human-like delays...")
            
            success = await browser.type_text(
                search_field.selector,
                "Playwright browser automation",
                human_like=True
            )
            
            if success:
                print("✅ Successfully typed in search field!")
                
                # Take a screenshot
                print("📸 Capturing screenshot...")
                screenshot_path = "google_search_test.png"
                await browser.capture_screenshot(path=screenshot_path)
                print(f"📸 Screenshot saved to: {screenshot_path}")
                
                # Wait a moment then search
                await asyncio.sleep(2)
                await browser.click_element("input[type='submit'], button[type='submit']")
                print("🔍 Submitted search!")
                
            else:
                print("❌ Failed to type in search field")
        else:
            print("❌ Could not find search field")


async def test_form_analysis(url: str):
    """Test DOM analysis on a specific URL."""
    print(f"🔍 Analyzing forms on: {url}")
    
    config = BrowserConfig(
        browser_type="chromium",
        headless=False,
        connect_to_existing=True
    )
    
    async with PlaywrightBrowserAutomation(config) as browser:
        try:
            await browser.navigate(url)
            
            # Get page info
            page_info = await browser.get_page_info()
            print(f"📄 Page: {page_info['title']}")
            print(f"🔗 URL: {page_info['url']}")
            
            # Analyze DOM
            fields = await browser.analyze_dom()
            
            if not fields:
                print("❌ No input fields found on this page")
                return
            
            print(f"\n📊 Found {len(fields)} input fields:")
            print("=" * 80)
            
            for i, field in enumerate(fields, 1):
                print(f"\n{i}. Field ID: {field.field_id}")
                print(f"   Type: {field.element_type} ({field.input_type or 'N/A'})")
                print(f"   Inferred: {field.inferred_type} (confidence: {field.confidence:.2f})")
                print(f"   Label: {field.label or 'N/A'}")
                print(f"   Placeholder: {field.placeholder or 'N/A'}")
                print(f"   Name: {field.name or 'N/A'}")
                print(f"   ID: {field.id or 'N/A'}")
                print(f"   Selector: {field.selector}")
                print(f"   Visible: {field.is_visible}, Enabled: {field.is_enabled}")
                
                if field.bounds:
                    print(f"   Position: ({field.bounds['x']:.0f}, {field.bounds['y']:.0f}) "
                          f"Size: {field.bounds['width']:.0f}x{field.bounds['height']:.0f}")
            
            # Take screenshot
            screenshot_path = f"form_analysis_{url.replace('://', '_').replace('/', '_')}.png"
            await browser.capture_screenshot(path=screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
            
            # Save field analysis as JSON
            fields_data = []
            for field in fields:
                fields_data.append({
                    "field_id": field.field_id,
                    "element_type": field.element_type,
                    "input_type": field.input_type,
                    "inferred_type": field.inferred_type,
                    "confidence": field.confidence,
                    "label": field.label,
                    "placeholder": field.placeholder,
                    "name": field.name,
                    "id": field.id,
                    "selector": field.selector,
                    "xpath": field.xpath,
                    "is_visible": field.is_visible,
                    "is_enabled": field.is_enabled,
                    "bounds": field.bounds
                })
            
            json_path = f"fields_analysis_{url.replace('://', '_').replace('/', '_')}.json"
            with open(json_path, 'w') as f:
                json.dump(fields_data, f, indent=2)
            
            print(f"💾 Field analysis saved to: {json_path}")
            
        except Exception as e:
            print(f"❌ Error analyzing page: {e}")


async def test_typing_demo():
    """Demonstrate different typing methods."""
    print("⌨️  Testing typing capabilities...")
    
    config = BrowserConfig(
        browser_type="chromium",
        headless=False,
        connect_to_existing=True
    )
    
    async with PlaywrightBrowserAutomation(config) as browser:
        # Navigate to a simple form page
        await browser.navigate("data:text/html,<html><body><h1>Typing Test</h1><input type='text' placeholder='Normal typing' id='normal'><br><br><input type='text' placeholder='Human-like typing' id='human'><br><br><textarea placeholder='Large text area' id='textarea'></textarea></body></html>")
        
        print("🎯 Testing normal typing...")
        await browser.type_text("#normal", "This is normal typing", human_like=False)
        await asyncio.sleep(1)
        
        print("🎯 Testing human-like typing...")
        await browser.type_text("#human", "This is human-like typing with natural delays", human_like=True)
        await asyncio.sleep(1)
        
        print("🎯 Testing textarea typing...")
        long_text = "This is a longer text to demonstrate typing in a textarea. It includes multiple sentences and should show the human-like typing behavior with natural pauses between words."
        await browser.type_text("#textarea", long_text, human_like=True)
        
        print("📸 Taking final screenshot...")
        await browser.capture_screenshot(path="typing_demo.png")
        print("✅ Typing demo completed!")


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Playwright Browser Automation")
    parser.add_argument("--url", help="URL to analyze for forms")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], 
                       default="chromium", help="Browser type to use")
    parser.add_argument("--test", choices=["google", "typing", "analyze"], 
                       default="google", help="Test to run")
    
    args = parser.parse_args()
    
    print("🎭 Playwright Browser Automation Test")
    print("=" * 50)
    
    try:
        if args.test == "google":
            await test_google_search()
        elif args.test == "typing":
            await test_typing_demo()
        elif args.test == "analyze" and args.url:
            await test_form_analysis(args.url)
        else:
            print("❌ Please specify a test to run or provide a URL for analysis")
            print("Examples:")
            print("  python test_browser_automation.py --test google")
            print("  python test_browser_automation.py --test typing")
            print("  python test_browser_automation.py --test analyze --url https://example.com")
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
