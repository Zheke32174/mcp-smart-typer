#!/usr/bin/env python3
"""
Basic Functionality Test for MCP Smart Typer Native Helpers
Tests core UI automation capabilities with working dependencies only.
"""

import sys
import time
import subprocess
from pathlib import Path

def test_basic_imports():
    """Test that all basic dependencies import correctly."""
    print("=== Testing Basic Imports ===")
    
    try:
        import pyautogui
        print("✅ PyAutoGUI imported successfully")
        print(f"   Screen size: {pyautogui.size()}")
    except Exception as e:
        print(f"❌ PyAutoGUI import failed: {e}")
        return False
    
    try:
        import pygetwindow as gw
        print("✅ PyGetWindow imported successfully")
        windows = gw.getWindowsWithTitle('')
        print(f"   Found {len(windows)} windows")
    except Exception as e:
        print(f"❌ PyGetWindow import failed: {e}")
        return False
    
    try:
        import pynput
        print("✅ PyInput imported successfully")
    except Exception as e:
        print(f"❌ PyInput import failed: {e}")
        return False
    
    try:
        import PIL
        print("✅ Pillow (PIL) imported successfully")
    except Exception as e:
        print(f"❌ Pillow import failed: {e}")
        return False
    
    return True

def test_window_detection():
    """Test window detection capabilities."""
    print("\n=== Testing Window Detection ===")
    
    try:
        import pygetwindow as gw
        
        # Get all windows
        all_windows = gw.getAllWindows()
        print(f"✅ Found {len(all_windows)} total windows")
        
        # Find specific windows
        notepad_windows = gw.getWindowsWithTitle('Notepad')
        print(f"   Notepad windows: {len(notepad_windows)}")
        
        # Find Windows Terminal or PowerShell windows
        terminal_windows = gw.getWindowsWithTitle('Windows PowerShell')
        if not terminal_windows:
            terminal_windows = gw.getWindowsWithTitle('PowerShell')
        if not terminal_windows:
            terminal_windows = gw.getWindowsWithTitle('Windows Terminal')
        
        print(f"   Terminal/PowerShell windows: {len(terminal_windows)}")
        
        # Show some window titles (first 5)
        print("   Sample window titles:")
        for i, window in enumerate(all_windows[:5]):
            if window.title.strip():
                print(f"     {i+1}. '{window.title}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Window detection failed: {e}")
        return False

def test_screenshot_capability():
    """Test screenshot functionality."""
    print("\n=== Testing Screenshot Capability ===")
    
    try:
        import pyautogui
        
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        print(f"✅ Screenshot taken successfully")
        print(f"   Screenshot size: {screenshot.size}")
        
        # Save screenshot to temp location
        temp_path = Path(__file__).parent / "test_screenshot.png"
        screenshot.save(temp_path)
        print(f"   Screenshot saved to: {temp_path}")
        
        # Clean up
        if temp_path.exists():
            temp_path.unlink()
            print("   Temporary screenshot cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Screenshot test failed: {e}")
        return False

def test_notepad_automation():
    """Test basic automation with Notepad."""
    print("\n=== Testing Notepad Automation ===")
    
    try:
        import pyautogui
        import pygetwindow as gw
        import subprocess
        
        # Start Notepad
        print("   Starting Notepad...")
        notepad_process = subprocess.Popen(['notepad.exe'])
        time.sleep(2)  # Wait for Notepad to start
        
        # Find Notepad window
        notepad_windows = gw.getWindowsWithTitle('Untitled - Notepad')
        if not notepad_windows:
            notepad_windows = gw.getWindowsWithTitle('Notepad')
        
        if notepad_windows:
            notepad_window = notepad_windows[0]
            print(f"✅ Found Notepad window: '{notepad_window.title}'")
            
            # Activate the window
            try:
                notepad_window.activate()
                time.sleep(1)
                print("   Notepad window activated")
                
                # Type some text
                test_text = "MCP Smart Typer Test - Basic functionality working!"
                pyautogui.typewrite(test_text, interval=0.1)
                print(f"   Typed text: '{test_text}'")
                
                # Try to close Notepad without saving
                pyautogui.hotkey('alt', 'f4')
                time.sleep(1)
                
                # If save dialog appears, press 'n' for don't save
                pyautogui.press('n')
                time.sleep(0.5)
                
                print("✅ Notepad automation test completed successfully")
                return True
                
            except Exception as e:
                print(f"⚠️ Notepad interaction failed: {e}")
                # Try to close anyway
                try:
                    notepad_process.terminate()
                except:
                    pass
                return False
        else:
            print("❌ Could not find Notepad window")
            # Try to close process
            try:
                notepad_process.terminate()
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Notepad automation test failed: {e}")
        return False

def test_grpc_imports():
    """Test gRPC related imports."""
    print("\n=== Testing gRPC Imports ===")
    
    try:
        import grpc
        print("✅ gRPC imported successfully")
        print(f"   gRPC version: {grpc.__version__}")
    except Exception as e:
        print(f"❌ gRPC import failed: {e}")
        return False
    
    try:
        import google.protobuf
        print("✅ Protobuf imported successfully")
        print(f"   Protobuf version: {google.protobuf.__version__}")
    except Exception as e:
        print(f"❌ Protobuf import failed: {e}")
        return False
    
    return True

def main():
    """Run all basic functionality tests."""
    print("🚀 MCP Smart Typer - Basic Functionality Test")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(("Basic Imports", test_basic_imports()))
    test_results.append(("Window Detection", test_window_detection()))
    test_results.append(("Screenshot Capability", test_screenshot_capability()))
    test_results.append(("gRPC Imports", test_grpc_imports()))
    test_results.append(("Notepad Automation", test_notepad_automation()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All basic functionality tests PASSED!")
        return 0
    elif passed >= total * 0.8:  # 80% pass rate
        print("⚠️ Most tests passed - system is functional with some limitations")
        return 0
    else:
        print("❌ Too many tests failed - system may not be functional")
        return 1

if __name__ == "__main__":
    sys.exit(main())
