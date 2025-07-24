#!/usr/bin/env python3
"""
MCP Smart Typer - Advanced Low-Level Device Controller
Direct hardware and system-level control capabilities
"""

import ctypes
import ctypes.wintypes
import time
import threading
import struct
import psutil
import winreg
import subprocess
import json
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging

# Windows API Constants
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040

# Input types
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

# Mouse events
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

# Keyboard events
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Registry access rights
KEY_READ = 0x20019
KEY_WRITE = 0x20006
KEY_ALL_ACCESS = 0xF003F

# System metrics
SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# Window messages
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

# Device types
DEVICE_MOUSE = "mouse"
DEVICE_KEYBOARD = "keyboard"
DEVICE_DISPLAY = "display"
DEVICE_AUDIO = "audio"
DEVICE_STORAGE = "storage"
DEVICE_NETWORK = "network"
DEVICE_USB = "usb"
DEVICE_BLUETOOTH = "bluetooth"

logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    """Information about a system device"""
    device_id: str
    device_type: str
    name: str
    manufacturer: str
    status: str
    properties: Dict[str, Any]
    capabilities: List[str]

@dataclass
class SystemMetrics:
    """System performance and hardware metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    temperature: Optional[float]
    power_status: Dict[str, Any]
    timestamp: datetime

class LowLevelDeviceController:
    """Advanced low-level device and system controller"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.gdi32 = ctypes.windll.gdi32
        self.ntdll = ctypes.windll.ntdll
        self.setupapi = ctypes.windll.setupapi
        
        self.device_cache = {}
        self.monitoring_threads = {}
        self.performance_callbacks = []
        
        # Initialize low-level input structures
        self._init_input_structures()
        
        logger.info("Low-level device controller initialized")

    def _init_input_structures(self):
        """Initialize Windows input structures"""
        
        # Define input structures
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.wintypes.LONG),
                ("dy", ctypes.wintypes.LONG),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
            ]
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", ctypes.wintypes.WORD),
                ("wScan", ctypes.wintypes.WORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
            ]
        
        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", ctypes.wintypes.DWORD),
                ("wParamL", ctypes.wintypes.WORD),
                ("wParamH", ctypes.wintypes.WORD)
            ]
        
        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)
            ]
        
        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.wintypes.DWORD),
                ("input", INPUT_UNION)
            ]
        
        # Store structures for later use
        self.POINT = POINT
        self.MOUSEINPUT = MOUSEINPUT
        self.KEYBDINPUT = KEYBDINPUT
        self.HARDWAREINPUT = HARDWAREINPUT
        self.INPUT = INPUT

    def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system performance metrics"""
        try:
            # CPU and memory
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('C:\\')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            net_io = psutil.net_io_counters()
            network_io = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
            # Power status (Windows-specific)
            power_status = self._get_power_status()
            
            # Temperature (if available)
            temperature = self._get_cpu_temperature()
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk_usage,
                network_io=network_io,
                temperature=temperature,
                power_status=power_status,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            raise

    def _get_power_status(self) -> Dict[str, Any]:
        """Get system power status"""
        try:
            class SYSTEM_POWER_STATUS(ctypes.Structure):
                _fields_ = [
                    ('ACLineStatus', ctypes.c_ubyte),
                    ('BatteryFlag', ctypes.c_ubyte),
                    ('BatteryLifePercent', ctypes.c_ubyte),
                    ('Reserved1', ctypes.c_ubyte),
                    ('BatteryLifeTime', ctypes.wintypes.DWORD),
                    ('BatteryFullLifeTime', ctypes.wintypes.DWORD),
                ]
            
            power_status = SYSTEM_POWER_STATUS()
            ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power_status))
            
            return {
                'ac_power': bool(power_status.ACLineStatus),
                'battery_present': power_status.BatteryFlag != 128,
                'battery_percent': power_status.BatteryLifePercent if power_status.BatteryLifePercent <= 100 else None,
                'battery_life_time': power_status.BatteryLifeTime if power_status.BatteryLifeTime != 0xFFFFFFFF else None
            }
            
        except Exception as e:
            logger.warning(f"Could not get power status: {e}")
            return {}

    def _get_cpu_temperature(self) -> Optional[float]:
        """Attempt to get CPU temperature (requires specific hardware/drivers)"""
        try:
            # This is a simplified approach - real implementation would need
            # specific hardware monitoring libraries like OpenHardwareMonitor
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_infos = w.Sensor()
            
            for sensor in temperature_infos:
                if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                    return float(sensor.Value)
                    
        except ImportError:
            logger.debug("WMI not available for temperature monitoring")
        except Exception as e:
            logger.debug(f"Temperature monitoring failed: {e}")
            
        return None

    def low_level_mouse_control(self, action: str, **kwargs) -> bool:
        """Direct low-level mouse control via Windows API"""
        try:
            if action == "move_absolute":
                x, y = kwargs.get('x', 0), kwargs.get('y', 0)
                # Convert to absolute coordinates (0-65535 range)
                abs_x = int((x * 65535) / self.user32.GetSystemMetrics(SM_CXSCREEN))
                abs_y = int((y * 65535) / self.user32.GetSystemMetrics(SM_CYSCREEN))
                
                input_struct = self.INPUT()
                input_struct.type = INPUT_MOUSE
                input_struct.input.mi.dx = abs_x
                input_struct.input.mi.dy = abs_y
                input_struct.input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
                
                result = self.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
                return result == 1
                
            elif action == "click":
                button = kwargs.get('button', 'left')
                duration = kwargs.get('duration', 0.05)
                
                # Mouse down
                down_flags = {
                    'left': MOUSEEVENTF_LEFTDOWN,
                    'right': MOUSEEVENTF_RIGHTDOWN,
                    'middle': MOUSEEVENTF_MIDDLEDOWN
                }
                
                # Mouse up
                up_flags = {
                    'left': MOUSEEVENTF_LEFTUP,
                    'right': MOUSEEVENTF_RIGHTUP,
                    'middle': MOUSEEVENTF_MIDDLEUP
                }
                
                # Send mouse down
                input_down = self.INPUT()
                input_down.type = INPUT_MOUSE
                input_down.input.mi.dwFlags = down_flags.get(button, MOUSEEVENTF_LEFTDOWN)
                self.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(input_down))
                
                time.sleep(duration)
                
                # Send mouse up
                input_up = self.INPUT()
                input_up.type = INPUT_MOUSE
                input_up.input.mi.dwFlags = up_flags.get(button, MOUSEEVENTF_LEFTUP)
                self.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(input_up))
                
                return True
                
            elif action == "scroll":
                delta = kwargs.get('delta', 120)  # Standard scroll delta
                
                input_struct = self.INPUT()
                input_struct.type = INPUT_MOUSE
                input_struct.input.mi.mouseData = delta
                input_struct.input.mi.dwFlags = MOUSEEVENTF_WHEEL
                
                result = self.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
                return result == 1
                
        except Exception as e:
            logger.error(f"Low-level mouse control failed: {e}")
            return False

    def low_level_keyboard_control(self, action: str, **kwargs) -> bool:
        """Direct low-level keyboard control via Windows API"""
        try:
            if action == "key_press":
                vk_code = kwargs.get('vk_code')
                scan_code = kwargs.get('scan_code', 0)
                duration = kwargs.get('duration', 0.05)
                
                if not vk_code:
                    return False
                
                # Key down
                input_down = self.INPUT()
                input_down.type = INPUT_KEYBOARD
                input_down.input.ki.wVk = vk_code
                input_down.input.ki.wScan = scan_code
                input_down.input.ki.dwFlags = 0
                
                # Key up
                input_up = self.INPUT()
                input_up.type = INPUT_KEYBOARD
                input_up.input.ki.wVk = vk_code
                input_up.input.ki.wScan = scan_code
                input_up.input.ki.dwFlags = KEYEVENTF_KEYUP
                
                # Send key down
                result1 = self.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(input_down))
                time.sleep(duration)
                
                # Send key up
                result2 = self.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(input_up))
                
                return result1 == 1 and result2 == 1
                
            elif action == "unicode_input":
                text = kwargs.get('text', '')
                
                for char in text:
                    unicode_value = ord(char)
                    
                    # Unicode key down
                    input_down = self.INPUT()
                    input_down.type = INPUT_KEYBOARD
                    input_down.input.ki.wVk = 0
                    input_down.input.ki.wScan = unicode_value
                    input_down.input.ki.dwFlags = KEYEVENTF_UNICODE
                    
                    # Unicode key up
                    input_up = self.INPUT()
                    input_up.type = INPUT_KEYBOARD
                    input_up.input.ki.wVk = 0
                    input_up.input.ki.wScan = unicode_value
                    input_up.input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
                    
                    self.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(input_down))
                    self.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(input_up))
                    
                    time.sleep(0.01)  # Small delay between characters
                
                return True
                
        except Exception as e:
            logger.error(f"Low-level keyboard control failed: {e}")
            return False

    def enumerate_devices(self, device_type: Optional[str] = None) -> List[DeviceInfo]:
        """Enumerate system devices using Windows Device Manager APIs"""
        devices = []
        
        try:
            # Use WMI to enumerate devices
            import wmi
            c = wmi.WMI()
            
            # Get different device types
            device_queries = {
                DEVICE_MOUSE: "SELECT * FROM Win32_PointingDevice",
                DEVICE_KEYBOARD: "SELECT * FROM Win32_Keyboard", 
                DEVICE_DISPLAY: "SELECT * FROM Win32_VideoController",
                DEVICE_AUDIO: "SELECT * FROM Win32_SoundDevice",
                DEVICE_STORAGE: "SELECT * FROM Win32_DiskDrive",
                DEVICE_NETWORK: "SELECT * FROM Win32_NetworkAdapter",
                DEVICE_USB: "SELECT * FROM Win32_USBControllerDevice"
            }
            
            target_types = [device_type] if device_type else device_queries.keys()
            
            for dev_type in target_types:
                if dev_type not in device_queries:
                    continue
                    
                try:
                    for device in c.query(device_queries[dev_type]):
                        device_info = DeviceInfo(
                            device_id=getattr(device, 'DeviceID', 'Unknown'),
                            device_type=dev_type,
                            name=getattr(device, 'Name', 'Unknown Device'),
                            manufacturer=getattr(device, 'Manufacturer', 'Unknown'),
                            status=getattr(device, 'Status', 'Unknown'),
                            properties=self._extract_device_properties(device),
                            capabilities=self._get_device_capabilities(device, dev_type)
                        )
                        devices.append(device_info)
                        
                except Exception as e:
                    logger.warning(f"Failed to enumerate {dev_type} devices: {e}")
                    
        except ImportError:
            logger.warning("WMI not available, using fallback device enumeration")
            devices = self._enumerate_devices_fallback(device_type)
            
        return devices

    def _extract_device_properties(self, device) -> Dict[str, Any]:
        """Extract relevant properties from WMI device object"""
        properties = {}
        
        # Common properties to extract
        prop_names = [
            'Description', 'HardwareID', 'CompatibleID', 'Service', 
            'ClassGuid', 'DriverVersion', 'DriverDate', 'Location'
        ]
        
        for prop_name in prop_names:
            try:
                value = getattr(device, prop_name, None)
                if value is not None:
                    properties[prop_name.lower()] = value
            except:
                pass
                
        return properties

    def _get_device_capabilities(self, device, device_type: str) -> List[str]:
        """Determine device capabilities based on type and properties"""
        capabilities = []
        
        if device_type == DEVICE_MOUSE:
            capabilities.extend(['click', 'move', 'scroll'])
            if hasattr(device, 'NumberOfButtons') and device.NumberOfButtons > 2:
                capabilities.append('multi_button')
                
        elif device_type == DEVICE_KEYBOARD:
            capabilities.extend(['type', 'shortcuts', 'function_keys'])
            
        elif device_type == DEVICE_DISPLAY:
            capabilities.extend(['render', 'resolution_change'])
            if hasattr(device, 'AcceleratorCapabilities'):
                capabilities.append('hardware_acceleration')
                
        elif device_type == DEVICE_AUDIO:
            capabilities.extend(['playback', 'volume_control'])
            
        elif device_type == DEVICE_STORAGE:
            capabilities.extend(['read', 'write', 'format'])
            
        elif device_type == DEVICE_NETWORK:
            capabilities.extend(['connect', 'transmit', 'receive'])
            
        return capabilities

    def _enumerate_devices_fallback(self, device_type: Optional[str]) -> List[DeviceInfo]:
        """Fallback device enumeration without WMI"""
        devices = []
        
        # Basic system info fallback
        basic_devices = [
            DeviceInfo(
                device_id="system_mouse",
                device_type=DEVICE_MOUSE,
                name="System Mouse",
                manufacturer="Unknown",
                status="OK",
                properties={},
                capabilities=['click', 'move', 'scroll']
            ),
            DeviceInfo(
                device_id="system_keyboard", 
                device_type=DEVICE_KEYBOARD,
                name="System Keyboard",
                manufacturer="Unknown",
                status="OK",
                properties={},
                capabilities=['type', 'shortcuts']
            )
        ]
        
        if device_type:
            devices = [d for d in basic_devices if d.device_type == device_type]
        else:
            devices = basic_devices
            
        return devices

    def control_device(self, device_id: str, action: str, **kwargs) -> bool:
        """Control a specific device"""
        try:
            # Find device
            device = None
            for dev in self.enumerate_devices():
                if dev.device_id == device_id:
                    device = dev
                    break
                    
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
                
            # Route to appropriate control method
            if device.device_type == DEVICE_MOUSE:
                return self.low_level_mouse_control(action, **kwargs)
            elif device.device_type == DEVICE_KEYBOARD:
                return self.low_level_keyboard_control(action, **kwargs)
            elif device.device_type == DEVICE_DISPLAY:
                return self._control_display(action, **kwargs)
            elif device.device_type == DEVICE_AUDIO:
                return self._control_audio(action, **kwargs)
            else:
                logger.warning(f"Device type {device.device_type} control not implemented")
                return False
                
        except Exception as e:
            logger.error(f"Device control failed: {e}")
            return False

    def _control_display(self, action: str, **kwargs) -> bool:
        """Control display settings"""
        try:
            if action == "change_resolution":
                width = kwargs.get('width', 1920)
                height = kwargs.get('height', 1080)
                return self._change_display_resolution(width, height)
            elif action == "change_brightness":
                brightness = kwargs.get('brightness', 50)
                return self._change_display_brightness(brightness)
                
        except Exception as e:
            logger.error(f"Display control failed: {e}")
            return False

    def _control_audio(self, action: str, **kwargs) -> bool:
        """Control audio settings"""
        try:
            if action == "set_volume":
                volume = kwargs.get('volume', 50)
                return self._set_system_volume(volume)
            elif action == "mute":
                return self._mute_system_audio(kwargs.get('mute', True))
                
        except Exception as e:
            logger.error(f"Audio control failed: {e}")
            return False

    def _change_display_resolution(self, width: int, height: int) -> bool:
        """Change display resolution"""
        try:
            # This would require more complex Windows API calls
            # For now, return a placeholder
            logger.info(f"Would change resolution to {width}x{height}")
            return True
        except Exception as e:
            logger.error(f"Resolution change failed: {e}")
            return False

    def _change_display_brightness(self, brightness: int) -> bool:
        """Change display brightness (0-100)"""
        try:
            # This requires WMI and specific hardware support
            import wmi
            c = wmi.WMI(namespace='root\\WMI')
            methods = c.query('SELECT * FROM WmiMonitorBrightnessMethods')
            
            for method in methods:
                method.WmiSetBrightness(brightness, 0)
                return True
                
        except Exception as e:
            logger.debug(f"Brightness control not available: {e}")
            return False

    def _set_system_volume(self, volume: int) -> bool:
        """Set system volume (0-100)"""
        try:
            # Use Windows volume control API
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_control = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Convert percentage to scalar (0.0 to 1.0)
            scalar_volume = volume / 100.0
            volume_control.SetMasterScalarVolume(scalar_volume, None)
            
            return True
            
        except ImportError:
            logger.debug("pycaw not available for volume control")
            return False
        except Exception as e:
            logger.error(f"Volume control failed: {e}")
            return False

    def _mute_system_audio(self, mute: bool) -> bool:
        """Mute or unmute system audio"""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_control = cast(interface, POINTER(IAudioEndpointVolume))
            
            volume_control.SetMute(mute, None)
            return True
            
        except ImportError:
            logger.debug("pycaw not available for mute control")
            return False
        except Exception as e:
            logger.error(f"Mute control failed: {e}")
            return False

    def start_performance_monitoring(self, callback: Callable[[SystemMetrics], None], interval: float = 1.0):
        """Start continuous performance monitoring"""
        def monitor():
            while True:
                try:
                    metrics = self.get_system_metrics()
                    callback(metrics)
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Performance monitoring error: {e}")
                    break
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.monitoring_threads['performance'] = monitor_thread
        
        logger.info(f"Started performance monitoring with {interval}s interval")

    def registry_control(self, action: str, **kwargs) -> Any:
        """Direct Windows registry manipulation"""
        try:
            if action == "read_key":
                hkey = kwargs.get('hkey', winreg.HKEY_CURRENT_USER)
                subkey = kwargs.get('subkey', '')
                value_name = kwargs.get('value_name', '')
                
                with winreg.OpenKey(hkey, subkey, 0, KEY_READ) as key:
                    value, value_type = winreg.QueryValueEx(key, value_name)
                    return {'value': value, 'type': value_type}
                    
            elif action == "write_key":
                hkey = kwargs.get('hkey', winreg.HKEY_CURRENT_USER)
                subkey = kwargs.get('subkey', '')
                value_name = kwargs.get('value_name', '')
                value = kwargs.get('value')
                value_type = kwargs.get('value_type', winreg.REG_SZ)
                
                with winreg.OpenKey(hkey, subkey, 0, KEY_WRITE) as key:
                    winreg.SetValueEx(key, value_name, 0, value_type, value)
                    return True
                    
            elif action == "create_key":
                hkey = kwargs.get('hkey', winreg.HKEY_CURRENT_USER)
                subkey = kwargs.get('subkey', '')
                
                with winreg.CreateKey(hkey, subkey) as key:
                    return True
                    
        except Exception as e:
            logger.error(f"Registry operation failed: {e}")
            return None

    def process_control(self, action: str, **kwargs) -> Any:
        """Advanced process control and monitoring"""
        try:
            if action == "list_processes":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                return processes
                
            elif action == "kill_process":
                pid = kwargs.get('pid')
                name = kwargs.get('name')
                
                if pid:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    return True
                elif name:
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == name:
                            proc.terminate()
                            return True
                            
            elif action == "get_process_info":
                pid = kwargs.get('pid')
                if pid:
                    proc = psutil.Process(pid)
                    return {
                        'pid': proc.pid,
                        'name': proc.name(),
                        'status': proc.status(),
                        'cpu_percent': proc.cpu_percent(),
                        'memory_info': proc.memory_info()._asdict(),
                        'connections': [conn._asdict() for conn in proc.connections()],
                        'open_files': [f.path for f in proc.open_files()],
                        'threads': len(proc.threads())
                    }
                    
        except Exception as e:
            logger.error(f"Process control failed: {e}")
            return None

    def network_control(self, action: str, **kwargs) -> Any:
        """Network interface and connection control"""
        try:
            if action == "list_interfaces":
                interfaces = []
                for interface, addrs in psutil.net_if_addrs().items():
                    interface_info = {
                        'name': interface,
                        'addresses': [{'family': addr.family.name, 'address': addr.address} for addr in addrs]
                    }
                    interfaces.append(interface_info)
                return interfaces
                
            elif action == "get_connections":
                connections = []
                for conn in psutil.net_connections():
                    connections.append({
                        'fd': conn.fd,
                        'family': conn.family.name if conn.family else None,
                        'type': conn.type.name if conn.type else None,
                        'laddr': conn.laddr._asdict() if conn.laddr else None,
                        'raddr': conn.raddr._asdict() if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid
                    })
                return connections
                
            elif action == "get_io_stats":
                return psutil.net_io_counters()._asdict()
                
        except Exception as e:
            logger.error(f"Network control failed: {e}")
            return None

    def generate_device_report(self) -> Dict[str, Any]:
        """Generate comprehensive device and system report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': self.get_system_metrics().__dict__,
                'devices': [device.__dict__ for device in self.enumerate_devices()],
                'processes': self.process_control('list_processes'),
                'network_interfaces': self.network_control('list_interfaces'),
                'network_connections': self.network_control('get_connections'),
                'network_io': self.network_control('get_io_stats')
            }
            
            # Save report
            report_path = Path.home() / "Documents" / "mcp_device_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
                
            logger.info(f"Device report saved to {report_path}")
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {}

    def emergency_system_control(self, action: str) -> bool:
        """Emergency system control functions"""
        try:
            if action == "force_shutdown":
                subprocess.run(['shutdown', '-s', '-f', '-t', '0'], check=True)
                return True
            elif action == "force_restart":
                subprocess.run(['shutdown', '-r', '-f', '-t', '0'], check=True)
                return True
            elif action == "lock_workstation":
                self.user32.LockWorkStation()
                return True
            elif action == "log_off":
                subprocess.run(['shutdown', '-l'], check=True)
                return True
                
        except Exception as e:
            logger.error(f"Emergency system control failed: {e}")
            return False

if __name__ == "__main__":
    # Demo usage
    controller = LowLevelDeviceController()
    
    print("🔧 Low-Level Device Controller Demo")
    print("=" * 50)
    
    # Get system metrics
    metrics = controller.get_system_metrics()
    print(f"CPU Usage: {metrics.cpu_usage}%")
    print(f"Memory Usage: {metrics.memory_usage}%")
    print(f"Power Status: {metrics.power_status}")
    
    # Enumerate devices
    devices = controller.enumerate_devices()
    print(f"\nFound {len(devices)} devices:")
    for device in devices:
        print(f"  - {device.name} ({device.device_type})")
    
    # Generate comprehensive report
    report = controller.generate_device_report()
    print(f"\nGenerated device report with {len(report)} sections")
