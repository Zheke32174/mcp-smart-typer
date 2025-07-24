#!/usr/bin/env python3
"""
MCP Smart Typer - Low-Level Device Control Demonstration
Showcases advanced system-level device control capabilities
"""

import time
import json
import threading
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

# Import our low-level controller
from src.low_level_device_controller import LowLevelDeviceController, SystemMetrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LowLevelControlDemo:
    """Comprehensive demonstration of low-level device control"""
    
    def __init__(self):
        self.controller = LowLevelDeviceController()
        self.demo_results = []
        self.start_time = datetime.now()
        self.monitoring_active = False
        
    def log_demo(self, demo_name: str, status: str, details: str = ""):
        """Log demonstration results"""
        result = {
            'demo': demo_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'execution_time': (datetime.now() - self.start_time).total_seconds()
        }
        self.demo_results.append(result)
        logger.info(f"{demo_name}: {status} - {details}")

    def demo_1_system_metrics_monitoring(self):
        """Demo 1: Real-time system metrics monitoring"""
        print("\n🔍 DEMO 1: Real-time System Metrics Monitoring")
        print("=" * 60)
        
        try:
            print("  → Starting 10-second system monitoring...")
            
            metrics_history = []
            
            def metrics_callback(metrics: SystemMetrics):
                metrics_history.append({
                    'timestamp': metrics.timestamp.isoformat(),
                    'cpu': metrics.cpu_usage,
                    'memory': metrics.memory_usage,
                    'disk': metrics.disk_usage,
                    'power': metrics.power_status
                })
                print(f"    CPU: {metrics.cpu_usage:.1f}% | Memory: {metrics.memory_usage:.1f}% | "
                      f"Disk: {metrics.disk_usage:.1f}% | Power: {metrics.power_status.get('ac_power', 'Unknown')}")
            
            # Start monitoring
            self.controller.start_performance_monitoring(metrics_callback, interval=0.5)
            self.monitoring_active = True
            
            # Run for 10 seconds
            time.sleep(10)
            
            print(f"  → Collected {len(metrics_history)} metric samples")
            
            # Calculate averages
            if metrics_history:
                avg_cpu = sum(m['cpu'] for m in metrics_history) / len(metrics_history)
                avg_memory = sum(m['memory'] for m in metrics_history) / len(metrics_history)
                print(f"  → Average CPU: {avg_cpu:.1f}%, Average Memory: {avg_memory:.1f}%")
            
            self.log_demo("System Metrics Monitoring", "SUCCESS", 
                         f"Monitored system for 10s, collected {len(metrics_history)} samples")
            
        except Exception as e:
            self.log_demo("System Metrics Monitoring", "ERROR", str(e))

    def demo_2_device_enumeration(self):
        """Demo 2: Comprehensive device enumeration"""
        print("\n🖥️ DEMO 2: Comprehensive Device Enumeration")
        print("=" * 60)
        
        try:
            print("  → Enumerating all system devices...")
            
            devices = self.controller.enumerate_devices()
            device_summary = {}
            
            for device in devices:
                if device.device_type not in device_summary:
                    device_summary[device.device_type] = []
                device_summary[device.device_type].append({
                    'name': device.name,
                    'manufacturer': device.manufacturer,
                    'status': device.status,
                    'capabilities': device.capabilities
                })
            
            print(f"  → Found {len(devices)} total devices across {len(device_summary)} categories:")
            
            for device_type, device_list in device_summary.items():
                print(f"    {device_type.upper()}: {len(device_list)} devices")
                for device in device_list[:3]:  # Show first 3 of each type
                    print(f"      - {device['name']} ({device['manufacturer']})")
                    print(f"        Status: {device['status']}, Capabilities: {', '.join(device['capabilities'])}")
                if len(device_list) > 3:
                    print(f"      ... and {len(device_list) - 3} more")
            
            self.log_demo("Device Enumeration", "SUCCESS", 
                         f"Enumerated {len(devices)} devices in {len(device_summary)} categories")
            
        except Exception as e:
            self.log_demo("Device Enumeration", "ERROR", str(e))

    def demo_3_low_level_mouse_control(self):
        """Demo 3: Direct low-level mouse control"""
        print("\n🖱️ DEMO 3: Direct Low-Level Mouse Control")
        print("=" * 60)
        
        try:
            print("  → Testing direct Windows API mouse control...")
            
            # Get current position
            current_pos = (100, 100)  # Starting position
            
            # Test absolute movement
            test_positions = [
                (200, 200), (400, 200), (400, 400), (200, 400), (100, 100)
            ]
            
            print("    Testing absolute mouse movements...")
            for i, (x, y) in enumerate(test_positions):
                print(f"      Moving to ({x}, {y})")
                success = self.controller.low_level_mouse_control(
                    "move_absolute", x=x, y=y
                )
                if success:
                    time.sleep(0.5)
                else:
                    print(f"      Failed to move to ({x}, {y})")
            
            # Test clicking
            print("    Testing mouse clicks...")
            for button in ['left', 'right', 'middle']:
                print(f"      Testing {button} click")
                success = self.controller.low_level_mouse_control(
                    "click", button=button, duration=0.1
                )
                time.sleep(0.5)
            
            # Test scrolling
            print("    Testing mouse scroll...")
            for direction in [120, -120, 240, -240]:  # Positive = up, negative = down
                print(f"      Scrolling {'up' if direction > 0 else 'down'} (delta: {direction})")
                success = self.controller.low_level_mouse_control(
                    "scroll", delta=direction
                )
                time.sleep(0.3)
            
            self.log_demo("Low-Level Mouse Control", "SUCCESS", 
                         "Executed absolute movements, clicks, and scroll operations")
            
        except Exception as e:
            self.log_demo("Low-Level Mouse Control", "ERROR", str(e))

    def demo_4_low_level_keyboard_control(self):
        """Demo 4: Direct low-level keyboard control"""
        print("\n⌨️ DEMO 4: Direct Low-Level Keyboard Control")
        print("=" * 60)
        
        try:
            print("  → Testing direct Windows API keyboard control...")
            
            # Open Notepad for testing
            print("    Opening Notepad for keyboard testing...")
            import subprocess
            subprocess.Popen(['notepad.exe'])
            time.sleep(2)
            
            # Test key presses (Virtual Key Codes)
            print("    Testing individual key presses...")
            test_keys = [
                (0x48, "H"),  # H key
                (0x45, "E"),  # E key
                (0x4C, "L"),  # L key
                (0x4C, "L"),  # L key
                (0x4F, "O"),  # O key
                (0x20, "SPACE"),  # Space key
            ]
            
            for vk_code, key_name in test_keys:
                print(f"      Pressing {key_name} (VK: 0x{vk_code:02X})")
                success = self.controller.low_level_keyboard_control(
                    "key_press", vk_code=vk_code, duration=0.05
                )
                time.sleep(0.2)
            
            # Test Unicode input
            print("    Testing Unicode text input...")
            unicode_text = "🚀 Unicode: Åñÿ spëcîál chårs! 你好"
            print(f"      Typing: '{unicode_text}'")
            success = self.controller.low_level_keyboard_control(
                "unicode_input", text=unicode_text
            )
            time.sleep(1)
            
            # Test function keys and combinations
            print("    Testing function keys...")
            function_keys = [
                (0x0D, "ENTER"),    # Enter
                (0x08, "BACKSPACE"), # Backspace
                (0x09, "TAB"),      # Tab
                (0x1B, "ESCAPE"),   # Escape
            ]
            
            for vk_code, key_name in function_keys:
                print(f"      Pressing {key_name}")
                success = self.controller.low_level_keyboard_control(
                    "key_press", vk_code=vk_code, duration=0.05
                )
                time.sleep(0.3)
            
            self.log_demo("Low-Level Keyboard Control", "SUCCESS", 
                         "Executed key presses, Unicode input, and function keys")
            
        except Exception as e:
            self.log_demo("Low-Level Keyboard Control", "ERROR", str(e))

    def demo_5_process_control(self):
        """Demo 5: Advanced process control and monitoring"""
        print("\n⚙️ DEMO 5: Advanced Process Control and Monitoring")
        print("=" * 60)
        
        try:
            print("  → Analyzing running processes...")
            
            # List all processes
            processes = self.controller.process_control("list_processes")
            if processes:
                print(f"    Found {len(processes)} running processes")
                
                # Show top 10 by memory usage
                sorted_procs = sorted(processes, 
                                    key=lambda p: p.get('memory_info', {}).get('rss', 0) if p.get('memory_info') else 0, 
                                    reverse=True)[:10]
                
                print("    Top 10 processes by memory usage:")
                for i, proc in enumerate(sorted_procs, 1):
                    memory_mb = proc.get('memory_info', {}).get('rss', 0) / (1024 * 1024) if proc.get('memory_info') else 0
                    print(f"      {i:2d}. {proc.get('name', 'Unknown')[:30]:30} - {memory_mb:.1f} MB")
                
                # Find specific process info
                print("    Detailed info for first few processes:")
                for proc in processes[:3]:
                    if 'pid' in proc:
                        detailed_info = self.controller.process_control("get_process_info", pid=proc['pid'])
                        if detailed_info:
                            print(f"      PID {proc['pid']}: {detailed_info.get('name', 'Unknown')}")
                            print(f"        Status: {detailed_info.get('status', 'Unknown')}")
                            print(f"        Threads: {detailed_info.get('threads', 0)}")
                            print(f"        Open files: {len(detailed_info.get('open_files', []))}")
            
            self.log_demo("Process Control", "SUCCESS", 
                         f"Analyzed {len(processes) if processes else 0} processes")
            
        except Exception as e:
            self.log_demo("Process Control", "ERROR", str(e))

    def demo_6_network_analysis(self):
        """Demo 6: Network interface and connection analysis"""
        print("\n🌐 DEMO 6: Network Interface and Connection Analysis")
        print("=" * 60)
        
        try:
            print("  → Analyzing network interfaces...")
            
            # List network interfaces
            interfaces = self.controller.network_control("list_interfaces")
            if interfaces:
                print(f"    Found {len(interfaces)} network interfaces:")
                for interface in interfaces:
                    print(f"      - {interface['name']}")
                    for addr in interface['addresses']:
                        print(f"        {addr['family']}: {addr['address']}")
            
            # Get network connections
            print("  → Analyzing network connections...")
            connections = self.controller.network_control("get_connections")
            if connections:
                active_connections = [c for c in connections if c.get('status') == 'ESTABLISHED']
                print(f"    Total connections: {len(connections)}")
                print(f"    Active connections: {len(active_connections)}")
                
                # Show first few active connections
                print("    Sample active connections:")
                for conn in active_connections[:5]:
                    local_addr = conn.get('laddr', {})
                    remote_addr = conn.get('raddr', {})
                    if local_addr and remote_addr:
                        print(f"      {local_addr.get('ip', 'Unknown')}:{local_addr.get('port', 'Unknown')} → "
                              f"{remote_addr.get('ip', 'Unknown')}:{remote_addr.get('port', 'Unknown')} "
                              f"(PID: {conn.get('pid', 'Unknown')})")
            
            # Get I/O statistics
            print("  → Network I/O statistics...")
            io_stats = self.controller.network_control("get_io_stats")
            if io_stats:
                print(f"    Bytes sent: {io_stats.get('bytes_sent', 0):,}")
                print(f"    Bytes received: {io_stats.get('bytes_recv', 0):,}")
                print(f"    Packets sent: {io_stats.get('packets_sent', 0):,}")
                print(f"    Packets received: {io_stats.get('packets_recv', 0):,}")
            
            self.log_demo("Network Analysis", "SUCCESS", 
                         f"Analyzed {len(interfaces) if interfaces else 0} interfaces, "
                         f"{len(connections) if connections else 0} connections")
            
        except Exception as e:
            self.log_demo("Network Analysis", "ERROR", str(e))

    def demo_7_audio_control(self):
        """Demo 7: System audio control"""
        print("\n🔊 DEMO 7: System Audio Control")
        print("=" * 60)
        
        try:
            print("  → Testing system audio control...")
            
            # Save current volume (we'll restore it later)
            print("    Testing volume control...")
            
            volume_levels = [25, 50, 75, 100, 50]  # Test sequence
            for volume in volume_levels:
                print(f"      Setting volume to {volume}%")
                success = self.controller._set_system_volume(volume)
                if success:
                    time.sleep(1)
                else:
                    print(f"      Failed to set volume to {volume}%")
            
            print("    Testing mute/unmute...")
            
            # Test mute
            print("      Muting audio...")
            success = self.controller._mute_system_audio(True)
            if success:
                time.sleep(2)
                
                print("      Unmuting audio...")
                success = self.controller._mute_system_audio(False)
                time.sleep(1)
            
            self.log_demo("Audio Control", "SUCCESS", 
                         "Tested volume control and mute/unmute functionality")
            
        except Exception as e:
            self.log_demo("Audio Control", "ERROR", str(e))

    def demo_8_registry_operations(self):
        """Demo 8: Windows Registry operations"""
        print("\n📝 DEMO 8: Windows Registry Operations")
        print("=" * 60)
        
        try:
            print("  → Testing Windows Registry operations...")
            
            import winreg
            
            # Test registry read
            print("    Reading system information from registry...")
            
            registry_reads = [
                {
                    'hkey': winreg.HKEY_LOCAL_MACHINE,
                    'subkey': r'SOFTWARE\Microsoft\Windows NT\CurrentVersion',
                    'value_name': 'ProductName',
                    'description': 'Windows Product Name'
                },
                {
                    'hkey': winreg.HKEY_LOCAL_MACHINE,
                    'subkey': r'SOFTWARE\Microsoft\Windows NT\CurrentVersion',
                    'value_name': 'CurrentVersion',
                    'description': 'Windows Version'
                }
            ]
            
            for read_op in registry_reads:
                try:
                    result = self.controller.registry_control(
                        "read_key",
                        hkey=read_op['hkey'],
                        subkey=read_op['subkey'],
                        value_name=read_op['value_name']
                    )
                    if result:
                        print(f"      {read_op['description']}: {result['value']}")
                except Exception as e:
                    print(f"      Failed to read {read_op['description']}: {e}")
            
            # Test registry write (safe location)
            print("    Testing registry write in user area...")
            test_key = r"SOFTWARE\MCPSmartTyper\Test"
            test_value = f"Demo run at {datetime.now().isoformat()}"
            
            # Create key
            success = self.controller.registry_control(
                "create_key",
                hkey=winreg.HKEY_CURRENT_USER,
                subkey=test_key
            )
            
            if success:
                # Write value
                success = self.controller.registry_control(
                    "write_key",
                    hkey=winreg.HKEY_CURRENT_USER,
                    subkey=test_key,
                    value_name="DemoValue",
                    value=test_value
                )
                
                if success:
                    print(f"      Successfully wrote test value to registry")
                    
                    # Read back to verify
                    result = self.controller.registry_control(
                        "read_key",
                        hkey=winreg.HKEY_CURRENT_USER,
                        subkey=test_key,
                        value_name="DemoValue"
                    )
                    
                    if result and result['value'] == test_value:
                        print(f"      Successfully verified written value")
            
            self.log_demo("Registry Operations", "SUCCESS", 
                         "Performed registry read and write operations")
            
        except Exception as e:
            self.log_demo("Registry Operations", "ERROR", str(e))

    def demo_9_device_control_integration(self):
        """Demo 9: Integrated device control"""
        print("\n🎛️ DEMO 9: Integrated Device Control")
        print("=" * 60)
        
        try:
            print("  → Testing integrated device control...")
            
            # Get all devices
            devices = self.controller.enumerate_devices()
            
            # Try to control each device type
            device_controls = {}
            
            for device in devices:
                device_type = device.device_type
                device_id = device.device_id
                
                if device_type not in device_controls:
                    device_controls[device_type] = []
                
                print(f"    Testing control for {device.name} ({device_type})")
                
                if device_type == "mouse":
                    # Test mouse control
                    success = self.controller.control_device(
                        device_id, "move_absolute", x=300, y=300
                    )
                    device_controls[device_type].append(("move", success))
                    
                elif device_type == "keyboard":
                    # Test keyboard control
                    success = self.controller.control_device(
                        device_id, "key_press", vk_code=0x20  # Space key
                    )
                    device_controls[device_type].append(("key_press", success))
                    
                elif device_type == "audio":
                    # Test audio control
                    success = self.controller.control_device(
                        device_id, "set_volume", volume=50
                    )
                    device_controls[device_type].append(("volume", success))
                
                time.sleep(0.5)
            
            # Summary
            print("    Device control summary:")
            for device_type, controls in device_controls.items():
                successful = sum(1 for _, success in controls if success)
                total = len(controls)
                print(f"      {device_type}: {successful}/{total} controls successful")
            
            total_successful = sum(sum(1 for _, success in controls if success) 
                                 for controls in device_controls.values())
            total_attempts = sum(len(controls) for controls in device_controls.values())
            
            self.log_demo("Device Control Integration", "SUCCESS", 
                         f"Executed {total_successful}/{total_attempts} device controls")
            
        except Exception as e:
            self.log_demo("Device Control Integration", "ERROR", str(e))

    def demo_10_comprehensive_report_generation(self):
        """Demo 10: Comprehensive system report generation"""
        print("\n📊 DEMO 10: Comprehensive System Report Generation")
        print("=" * 60)
        
        try:
            print("  → Generating comprehensive system report...")
            
            report = self.controller.generate_device_report()
            
            if report:
                print("    Report sections generated:")
                for section, data in report.items():
                    if isinstance(data, list):
                        print(f"      - {section}: {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"      - {section}: {len(data)} properties")
                    else:
                        print(f"      - {section}: {type(data).__name__}")
                
                # Calculate report size
                report_json = json.dumps(report, default=str)
                report_size = len(report_json.encode('utf-8'))
                print(f"    Report size: {report_size:,} bytes ({report_size/1024:.1f} KB)")
                
                # Save demonstration-specific report
                demo_report_path = Path.home() / "Documents" / "mcp_low_level_demo_report.json"
                demo_report = {
                    'demonstration_results': self.demo_results,
                    'system_report': report,
                    'demo_summary': {
                        'total_demos': len(self.demo_results),
                        'successful_demos': sum(1 for r in self.demo_results if r['status'] == 'SUCCESS'),
                        'total_execution_time': (datetime.now() - self.start_time).total_seconds(),
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
                with open(demo_report_path, 'w') as f:
                    json.dump(demo_report, f, indent=2, default=str)
                
                print(f"    Demonstration report saved to: {demo_report_path}")
                
                self.log_demo("Report Generation", "SUCCESS", 
                             f"Generated comprehensive report ({report_size:,} bytes)")
            else:
                self.log_demo("Report Generation", "ERROR", "Failed to generate report")
            
        except Exception as e:
            self.log_demo("Report Generation", "ERROR", str(e))

    def generate_final_summary(self):
        """Generate final demonstration summary"""
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for r in self.demo_results if r['status'] == 'SUCCESS')
        failed_demos = total_demos - successful_demos
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("🎯 LOW-LEVEL DEVICE CONTROL DEMONSTRATION SUMMARY")
        print("=" * 80)
        print(f"Total Demonstrations: {total_demos}")
        print(f"Successful: {successful_demos}")
        print(f"Failed: {failed_demos}")
        print(f"Success Rate: {(successful_demos/total_demos)*100:.1f}%")
        print(f"Total Execution Time: {total_time:.2f} seconds")
        print(f"Average Time per Demo: {total_time/total_demos:.2f} seconds")
        print("\nDemonstration Results:")
        
        for result in self.demo_results:
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"{status_icon} {result['demo']}: {result['details']}")
        
        print("=" * 80)

    def run_all_demos(self):
        """Execute all low-level control demonstrations"""
        print("🚀 MCP SMART TYPER - LOW-LEVEL DEVICE CONTROL DEMONSTRATION")
        print("=" * 80)
        print(f"Starting advanced system control demo at {datetime.now()}")
        print("⚠️  WARNING: This demonstration will control system devices!")
        print("⚠️  Press Ctrl+C at any time to stop!")
        print("=" * 80)
        
        try:
            # Run all demonstrations
            self.demo_1_system_metrics_monitoring()
            time.sleep(1)
            
            self.demo_2_device_enumeration()
            time.sleep(1)
            
            self.demo_3_low_level_mouse_control()
            time.sleep(1)
            
            self.demo_4_low_level_keyboard_control()
            time.sleep(1)
            
            self.demo_5_process_control()
            time.sleep(1)
            
            self.demo_6_network_analysis()
            time.sleep(1)
            
            self.demo_7_audio_control()
            time.sleep(1)
            
            self.demo_8_registry_operations()
            time.sleep(1)
            
            self.demo_9_device_control_integration()
            time.sleep(1)
            
            self.demo_10_comprehensive_report_generation()
            
            # Generate final summary
            self.generate_final_summary()
            
        except KeyboardInterrupt:
            print("\n🛑 Demonstration interrupted by user!")
            self.generate_final_summary()
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            self.generate_final_summary()

if __name__ == "__main__":
    print("🔥 Initializing Low-Level Device Control Demonstration...")
    print("⚠️  WARNING: This will perform system-level operations!")
    print("⚠️  Ensure you have appropriate permissions!")
    print("⚠️  Press Ctrl+C at any time to stop!")
    
    response = input("\nProceed with low-level device control demonstration? (y/N): ")
    if response.lower() == 'y':
        demo = LowLevelControlDemo()
        demo.run_all_demos()
        print("\n✅ Low-level device control demonstration completed.")
    else:
        print("Demonstration cancelled.")
