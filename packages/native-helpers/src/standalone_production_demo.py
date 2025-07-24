"""
Standalone Production Demo for MCP Smart Typer
==============================================

This script demonstrates the core optimized capabilities of MCP Smart Typer
without requiring heavy machine learning dependencies.

Features Demonstrated:
- Optimized device controller with caching
- High-performance mouse and keyboard control
- System resource monitoring
- Performance benchmarking
- Error handling and recovery
- Real-time optimization

Author: MCP Smart Typer Team
Version: 2.0 (Standalone Production Demo)
"""

import asyncio
import json
import logging
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
import uuid
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque

# Core imports that are available
import psutil
import win32api
import win32con
import win32gui

# Setup logging
def setup_demo_logging():
    """Setup logging for the demo"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "standalone_demo.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

@dataclass
class DemoMetrics:
    """Track demo performance metrics"""
    operation_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    operation_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    success_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_operation(self, name: str, duration: float, success: bool = True):
        """Record an operation result"""
        self.operation_times[name].append(duration)
        self.operation_counts[name] += 1
        if success:
            self.success_counts[name] += 1
        else:
            self.error_counts[name] += 1
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        summary = {}
        for op_name in self.operation_counts:
            times = self.operation_times[op_name]
            summary[op_name] = {
                'total_operations': self.operation_counts[op_name],
                'successful_operations': self.success_counts[op_name],
                'success_rate': self.success_counts[op_name] / self.operation_counts[op_name] if self.operation_counts[op_name] > 0 else 0,
                'avg_time_ms': round(sum(times) / len(times) * 1000, 3) if times else 0,
                'min_time_ms': round(min(times) * 1000, 3) if times else 0,
                'max_time_ms': round(max(times) * 1000, 3) if times else 0
            }
        return summary

class OptimizedMouseController:
    """Optimized mouse controller with caching and performance tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MouseController")
        self.position_cache = (0, 0)
        self.cache_timestamp = 0
        self.cache_ttl = 0.01  # 10ms cache TTL
        self.metrics = DemoMetrics()
    
    def get_position(self) -> tuple:
        """Get mouse position with caching"""
        current_time = time.perf_counter()
        
        # Use cache if fresh
        if current_time - self.cache_timestamp < self.cache_ttl:
            return self.position_cache
        
        # Get fresh position
        try:
            from ctypes import wintypes
            point = wintypes.POINT()
            win32gui.GetCursorPos()
            cursor_pos = win32gui.GetCursorPos()
            self.position_cache = cursor_pos
            self.cache_timestamp = current_time
            return cursor_pos
        except Exception as e:
            self.logger.error(f"Failed to get cursor position: {e}")
            return self.position_cache
    
    def move_to(self, x: int, y: int) -> bool:
        """Move mouse to position with optimization"""
        start_time = time.perf_counter()
        
        try:
            # Check if already at position
            current_pos = self.get_position()
            if abs(current_pos[0] - x) < 2 and abs(current_pos[1] - y) < 2:
                duration = time.perf_counter() - start_time
                self.metrics.record_operation('move_cached', duration, True)
                return True
            
            # Move to new position
            win32api.SetCursorPos((x, y))
            
            # Update cache
            self.position_cache = (x, y)
            self.cache_timestamp = time.perf_counter()
            
            duration = time.perf_counter() - start_time
            self.metrics.record_operation('move_actual', duration, True)
            return True
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation('move_failed', duration, False)
            self.logger.error(f"Mouse move failed: {e}")
            return False
    
    def click(self, x: int, y: int, button: str = 'left') -> bool:
        """Click at position with optimization"""
        start_time = time.perf_counter()
        
        try:
            # Move to position first
            if not self.move_to(x, y):
                return False
            
            # Map button to events
            button_events = {
                'left': (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
                'right': (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
                'middle': (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP)
            }
            
            if button not in button_events:
                return False
            
            down_event, up_event = button_events[button]
            
            # Perform click
            win32api.mouse_event(down_event, x, y, 0, 0)
            time.sleep(0.001)  # Brief delay
            win32api.mouse_event(up_event, x, y, 0, 0)
            
            duration = time.perf_counter() - start_time
            self.metrics.record_operation(f'click_{button}', duration, True)
            return True
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation(f'click_{button}_failed', duration, False)
            self.logger.error(f"Mouse click failed: {e}")
            return False

class OptimizedKeyboardController:
    """Optimized keyboard controller with performance tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.KeyboardController")
        self.metrics = DemoMetrics()
    
    def type_text(self, text: str, delay_ms: float = 10) -> bool:
        """Type text with optimized performance"""
        start_time = time.perf_counter()
        
        try:
            delay_seconds = delay_ms / 1000.0
            
            for char in text:
                if ord(char) < 128:  # ASCII characters
                    self._type_ascii_char(char, delay_seconds)
                else:  # Unicode characters
                    self._type_unicode_char(char, delay_seconds)
            
            duration = time.perf_counter() - start_time
            chars_per_second = len(text) / duration if duration > 0 else 0
            self.metrics.record_operation('type_text', duration, True)
            self.logger.debug(f"Typed {len(text)} chars in {duration:.3f}s ({chars_per_second:.1f} chars/sec)")
            return True
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation('type_text_failed', duration, False)
            self.logger.error(f"Typing failed: {e}")
            return False
    
    def _type_ascii_char(self, char: str, delay: float):
        """Type ASCII character efficiently"""
        if char == ' ':
            vk_code = win32con.VK_SPACE
        elif char.isalpha():
            vk_code = ord(char.upper())
        elif char.isdigit():
            vk_code = ord(char)
        else:
            # Handle special characters
            vk_code = ord(char.upper()) if char.upper().isalpha() else win32con.VK_SPACE
        
        # Press and release
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(delay * 0.5)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(delay * 0.5)
    
    def _type_unicode_char(self, char: str, delay: float):
        """Type Unicode character (simplified approach)"""
        # For demo purposes, replace non-ASCII with spaces
        self._type_ascii_char(' ', delay)
    
    def press_key(self, key_code: int) -> bool:
        """Press a specific key"""
        start_time = time.perf_counter()
        
        try:
            win32api.keybd_event(key_code, 0, 0, 0)
            time.sleep(0.01)
            win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            duration = time.perf_counter() - start_time
            self.metrics.record_operation('press_key', duration, True)
            return True
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation('press_key_failed', duration, False)
            self.logger.error(f"Key press failed: {e}")
            return False

class SystemMonitor:
    """Real-time system monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SystemMonitor")
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 1.0):
        """Start system monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("System monitoring started")
    
    def _monitor_loop(self, interval: float):
        """Monitoring loop"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                metric = {
                    'timestamp': time.perf_counter(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_mb': memory.available / 1024 / 1024
                }
                
                self.metrics.append(metric)
                
                # Keep only last 100 samples
                if len(self.metrics) > 100:
                    self.metrics.pop(0)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(interval * 2)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("System monitoring stopped")
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        if not self.metrics:
            return {}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        
        return {
            'samples': len(self.metrics),
            'cpu': {
                'avg': round(sum(cpu_values) / len(cpu_values), 2),
                'min': round(min(cpu_values), 2),
                'max': round(max(cpu_values), 2)
            },
            'memory': {
                'avg': round(sum(memory_values) / len(memory_values), 2),
                'min': round(min(memory_values), 2),
                'max': round(max(memory_values), 2)
            },
            'duration_seconds': round(self.metrics[-1]['timestamp'] - self.metrics[0]['timestamp'], 2) if len(self.metrics) > 1 else 0
        }

class StandaloneProductionDemo:
    """Standalone production demonstration"""
    
    def __init__(self):
        self.logger = setup_demo_logging()
        self.mouse = OptimizedMouseController()
        self.keyboard = OptimizedKeyboardController()
        self.monitor = SystemMonitor()
        self.demo_results = {}
        self.start_time = time.perf_counter()
        
        self.logger.info("🚀 Standalone Production Demo initialized")
    
    async def run_full_demo(self):
        """Run the complete standalone demo"""
        try:
            self.logger.info("=" * 80)
            self.logger.info("🔥 MCP SMART TYPER STANDALONE PRODUCTION DEMO")
            self.logger.info("=" * 80)
            
            # Start system monitoring
            self.monitor.start_monitoring()
            
            # Phase 1: Basic Performance Testing
            await self._phase_1_basic_performance()
            
            # Phase 2: Optimized Mouse Control
            await self._phase_2_mouse_control()
            
            # Phase 3: Optimized Keyboard Control
            await self._phase_3_keyboard_control()
            
            # Phase 4: Bulk Operations
            await self._phase_4_bulk_operations()
            
            # Phase 5: Stress Testing
            await self._phase_5_stress_testing()
            
            # Phase 6: Final Analysis
            await self._phase_6_final_analysis()
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            self.logger.error(traceback.format_exc())
        
        finally:
            self.monitor.stop_monitoring()
    
    async def _phase_1_basic_performance(self):
        """Phase 1: Basic performance testing"""
        self.logger.info("📊 PHASE 1: Basic Performance Testing")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Test 1: System Information
            self.logger.info("🖥️ Test 1: System Information")
            
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\\\')\
            
            self.logger.info(f"  CPU Cores: {cpu_count}")
            self.logger.info(f"  Memory: {memory.total / 1024**3:.1f}GB total, {memory.percent:.1f}% used")
            self.logger.info(f"  Disk: {disk.total / 1024**3:.1f}GB total, {disk.percent:.1f}% used")
            
            # Test 2: Performance Baselines
            self.logger.info("⚡ Test 2: Performance Baselines")
            
            # Mouse position retrieval speed
            mouse_times = []
            for i in range(100):
                start = time.perf_counter()
                pos = self.mouse.get_position()
                duration = time.perf_counter() - start
                mouse_times.append(duration)
            
            avg_mouse_time = sum(mouse_times) / len(mouse_times)
            self.logger.info(f"  Mouse position retrieval: {avg_mouse_time*1000:.3f}ms avg")
            
            # Simple calculation speed
            calc_start = time.perf_counter()
            result = sum(i * i for i in range(10000))
            calc_duration = time.perf_counter() - calc_start
            self.logger.info(f"  Calculation speed: {calc_duration*1000:.3f}ms for 10k operations")
            
            phase_duration = time.perf_counter() - phase_start
            self.demo_results['phase_1_basic_performance'] = {
                'duration_seconds': round(phase_duration, 3),
                'cpu_cores': cpu_count,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'mouse_avg_time_ms': round(avg_mouse_time * 1000, 3),
                'calculation_time_ms': round(calc_duration * 1000, 3),
                'status': 'SUCCESS'
            }
            
            self.logger.info(f"✅ Phase 1 completed in {phase_duration:.3f}s")
            
        except Exception as e:
            self.demo_results['phase_1_basic_performance'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            raise
    
    async def _phase_2_mouse_control(self):
        """Phase 2: Optimized mouse control testing"""
        self.logger.info("🖱️ PHASE 2: Optimized Mouse Control")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Test 1: Mouse Movement Optimization
            self.logger.info("🎯 Test 1: Mouse Movement Optimization")
            
            # Test movement patterns
            test_positions = [
                (100, 100), (200, 100), (200, 200), (100, 200), (150, 150),
                (300, 300), (400, 300), (400, 400), (300, 400), (350, 350)
            ]
            
            movement_times = []
            for i, (x, y) in enumerate(test_positions):
                start = time.perf_counter()
                success = self.mouse.move_to(x, y)
                duration = time.perf_counter() - start
                movement_times.append(duration)
                
                if i % 3 == 0:  # Log every 3rd movement
                    self.logger.info(f"  Move {i+1}: ({x}, {y}) in {duration*1000:.3f}ms - {'✅' if success else '❌'}")
                
                await asyncio.sleep(0.01)  # Brief pause
            
            avg_movement_time = sum(movement_times) / len(movement_times)
            successful_moves = sum(1 for i, _ in enumerate(test_positions) if movement_times[i] < 0.1)  # Under 100ms
            
            self.logger.info(f"  📊 Movement Results:")
            self.logger.info(f"    Average time: {avg_movement_time*1000:.3f}ms")
            self.logger.info(f"    Fast movements: {successful_moves}/{len(test_positions)} (under 100ms)")
            
            # Test 2: Click Performance
            self.logger.info("👆 Test 2: Click Performance")
            
            click_positions = [(150, 150), (250, 250), (350, 350)]
            click_types = ['left', 'right', 'middle']
            
            for pos in click_positions:
                for click_type in click_types:
                    start = time.perf_counter()
                    success = self.mouse.click(pos[0], pos[1], click_type)
                    duration = time.perf_counter() - start
                    
                    self.logger.info(f"  {click_type.capitalize()} click at {pos}: {duration*1000:.3f}ms - {'✅' if success else '❌'}")
                    await asyncio.sleep(0.1)
            
            # Get mouse metrics
            mouse_metrics = self.mouse.metrics.get_summary()
            
            phase_duration = time.perf_counter() - phase_start
            self.demo_results['phase_2_mouse_control'] = {
                'duration_seconds': round(phase_duration, 3),
                'movements_tested': len(test_positions),
                'avg_movement_time_ms': round(avg_movement_time * 1000, 3),
                'fast_movements': successful_moves,
                'clicks_tested': len(click_positions) * len(click_types),
                'mouse_metrics': mouse_metrics,
                'status': 'SUCCESS'
            }
            
            self.logger.info(f"✅ Phase 2 completed in {phase_duration:.3f}s")
            
        except Exception as e:
            self.demo_results['phase_2_mouse_control'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            raise
    
    async def _phase_3_keyboard_control(self):
        """Phase 3: Optimized keyboard control testing"""
        self.logger.info("⌨️ PHASE 3: Optimized Keyboard Control")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Test 1: Text Typing Performance
            self.logger.info("📝 Test 1: Text Typing Performance")
            
            test_texts = [
                "Hello World",
                "Quick brown fox jumps over lazy dog",
                "Testing 123 with numbers!",
                "UPPERCASE and lowercase MiXeD",
                "Special chars: !@#$%^&*()",
                "A" * 50  # Long repetitive text
            ]
            
            typing_results = []
            for i, text in enumerate(test_texts):
                start = time.perf_counter()
                success = self.keyboard.type_text(text, delay_ms=5)  # 5ms delay for speed
                duration = time.perf_counter() - start
                
                chars_per_second = len(text) / duration if duration > 0 else 0
                typing_results.append({
                    'text_length': len(text),
                    'duration_ms': round(duration * 1000, 3),
                    'chars_per_second': round(chars_per_second, 1),
                    'success': success
                })\n                \n                self.logger.info(f\"  Text {i+1}: {len(text)} chars → {chars_per_second:.1f} chars/sec - {'✅' if success else '❌'}\")\n                await asyncio.sleep(0.2)\n            \n            # Calculate averages\n            avg_chars_per_sec = sum(r['chars_per_second'] for r in typing_results) / len(typing_results)\n            success_rate = sum(1 for r in typing_results if r['success']) / len(typing_results)\n            \n            self.logger.info(f\"  📊 Typing Results:\")\n            self.logger.info(f\"    Average speed: {avg_chars_per_sec:.1f} chars/sec\")\n            self.logger.info(f\"    Success rate: {success_rate:.1%}\")\n            \n            # Test 2: Special Key Presses\n            self.logger.info(\"🔑 Test 2: Special Key Presses\")\n            \n            special_keys = [\n                ('ENTER', win32con.VK_RETURN),\n                ('BACKSPACE', win32con.VK_BACK),\n                ('TAB', win32con.VK_TAB),\n                ('ESCAPE', win32con.VK_ESCAPE),\n                ('SPACE', win32con.VK_SPACE)\n            ]\n            \n            key_results = []\n            for key_name, key_code in special_keys:\n                start = time.perf_counter()\n                success = self.keyboard.press_key(key_code)\n                duration = time.perf_counter() - start\n                \n                key_results.append({\n                    'key': key_name,\n                    'duration_ms': round(duration * 1000, 3),\n                    'success': success\n                })\n                \n                self.logger.info(f\"  {key_name}: {duration*1000:.3f}ms - {'✅' if success else '❌'}\")\n                await asyncio.sleep(0.1)\n            \n            # Get keyboard metrics\n            keyboard_metrics = self.keyboard.metrics.get_summary()\n            \n            phase_duration = time.perf_counter() - phase_start\n            self.demo_results['phase_3_keyboard_control'] = {\n                'duration_seconds': round(phase_duration, 3),\n                'texts_tested': len(test_texts),\n                'avg_chars_per_second': round(avg_chars_per_sec, 1),\n                'typing_success_rate': round(success_rate, 3),\n                'special_keys_tested': len(special_keys),\n                'typing_results': typing_results,\n                'key_results': key_results,\n                'keyboard_metrics': keyboard_metrics,\n                'status': 'SUCCESS'\n            }\n            \n            self.logger.info(f\"✅ Phase 3 completed in {phase_duration:.3f}s\")\n            \n        except Exception as e:\n            self.demo_results['phase_3_keyboard_control'] = {\n                'status': 'FAILED',\n                'error': str(e)\n            }\n            raise\n    \n    async def _phase_4_bulk_operations(self):\n        \"\"\"Phase 4: Bulk operations testing\"\"\"\n        self.logger.info(\"📦 PHASE 4: Bulk Operations\")\n        self.logger.info(\"-\" * 50)\n        \n        phase_start = time.perf_counter()\n        \n        try:\n            # Test 1: Bulk Mouse Movements\n            self.logger.info(\"🖱️ Test 1: Bulk Mouse Movements\")\n            \n            # Generate bulk movement operations\n            bulk_positions = [(100 + i*20, 100 + i*10) for i in range(25)]  # 25 positions\n            \n            bulk_start = time.perf_counter()\n            successful_moves = 0\n            \n            for i, (x, y) in enumerate(bulk_positions):\n                success = self.mouse.move_to(x, y)\n                if success:\n                    successful_moves += 1\n                \n                # Brief async pause every 5 operations\n                if i % 5 == 0:\n                    await asyncio.sleep(0.001)\n            \n            bulk_duration = time.perf_counter() - bulk_start\n            moves_per_second = len(bulk_positions) / bulk_duration if bulk_duration > 0 else 0\n            \n            self.logger.info(f\"  ✅ Bulk movements: {successful_moves}/{len(bulk_positions)} successful\")\n            self.logger.info(f\"  ⚡ Performance: {moves_per_second:.1f} moves/second\")\n            \n            # Test 2: Bulk Typing Operations\n            self.logger.info(\"⌨️ Test 2: Bulk Typing Operations\")\n            \n            # Generate bulk typing operations\n            bulk_texts = [f\"Text {i+1}\" for i in range(10)]\n            \n            typing_start = time.perf_counter()\n            successful_types = 0\n            total_chars = 0\n            \n            for text in bulk_texts:\n                success = self.keyboard.type_text(text, delay_ms=1)  # Very fast typing\n                if success:\n                    successful_types += 1\n                    total_chars += len(text)\n                await asyncio.sleep(0.01)  # Brief pause\n            \n            typing_duration = time.perf_counter() - typing_start\n            chars_per_second = total_chars / typing_duration if typing_duration > 0 else 0\n            \n            self.logger.info(f\"  ✅ Bulk typing: {successful_types}/{len(bulk_texts)} successful\")\n            self.logger.info(f\"  ⚡ Performance: {chars_per_second:.1f} chars/second\")\n            \n            # Test 3: Mixed Operations\n            self.logger.info(\"🔄 Test 3: Mixed Operations\")\n            \n            mixed_start = time.perf_counter()\n            mixed_operations = 20\n            successful_mixed = 0\n            \n            for i in range(mixed_operations):\n                if i % 2 == 0:  # Even: mouse movement\n                    success = self.mouse.move_to(200 + i*5, 200 + i*3)\n                else:  # Odd: key press\n                    success = self.keyboard.press_key(win32con.VK_SPACE)\n                \n                if success:\n                    successful_mixed += 1\n                \n                await asyncio.sleep(0.005)  # 5ms pause\n            \n            mixed_duration = time.perf_counter() - mixed_start\n            mixed_per_second = mixed_operations / mixed_duration if mixed_duration > 0 else 0\n            \n            self.logger.info(f\"  ✅ Mixed operations: {successful_mixed}/{mixed_operations} successful\")\n            self.logger.info(f\"  ⚡ Performance: {mixed_per_second:.1f} operations/second\")\n            \n            phase_duration = time.perf_counter() - phase_start\n            self.demo_results['phase_4_bulk_operations'] = {\n                'duration_seconds': round(phase_duration, 3),\n                'bulk_movements': {\n                    'total': len(bulk_positions),\n                    'successful': successful_moves,\n                    'moves_per_second': round(moves_per_second, 1)\n                },\n                'bulk_typing': {\n                    'total': len(bulk_texts),\n                    'successful': successful_types,\n                    'chars_per_second': round(chars_per_second, 1)\n                },\n                'mixed_operations': {\n                    'total': mixed_operations,\n                    'successful': successful_mixed,\n                    'operations_per_second': round(mixed_per_second, 1)\n                },\n                'status': 'SUCCESS'\n            }\n            \n            self.logger.info(f\"✅ Phase 4 completed in {phase_duration:.3f}s\")\n            \n        except Exception as e:\n            self.demo_results['phase_4_bulk_operations'] = {\n                'status': 'FAILED',\n                'error': str(e)\n            }\n            raise\n    \n    async def _phase_5_stress_testing(self):\n        \"\"\"Phase 5: Stress testing under load\"\"\"\n        self.logger.info(\"🔥 PHASE 5: Stress Testing\")\n        self.logger.info(\"-\" * 50)\n        \n        phase_start = time.perf_counter()\n        \n        try:\n            # Test 1: Rapid Mouse Operations\n            self.logger.info(\"🚀 Test 1: Rapid Mouse Operations\")\n            \n            rapid_operations = 100\n            rapid_start = time.perf_counter()\n            rapid_successes = 0\n            \n            for i in range(rapid_operations):\n                x = 100 + (i % 20) * 10\n                y = 100 + (i % 15) * 8\n                \n                success = self.mouse.move_to(x, y)\n                if success:\n                    rapid_successes += 1\n                \n                # No delay for maximum speed\n                if i % 25 == 0:  # Brief async yield every 25 operations\n                    await asyncio.sleep(0.001)\n            \n            rapid_duration = time.perf_counter() - rapid_start\n            rapid_ops_per_sec = rapid_operations / rapid_duration if rapid_duration > 0 else 0\n            \n            self.logger.info(f\"  ✅ Rapid mouse: {rapid_successes}/{rapid_operations} successful\")\n            self.logger.info(f\"  ⚡ Performance: {rapid_ops_per_sec:.1f} operations/second\")\n            \n            # Test 2: Memory Usage Under Load\n            self.logger.info(\"💾 Test 2: Memory Usage Under Load\")\n            \n            import psutil\n            process = psutil.Process()\n            \n            initial_memory = process.memory_info().rss / 1024 / 1024  # MB\n            \n            # Perform memory-intensive operations\n            memory_test_operations = 200\n            memory_data = []\n            \n            for i in range(memory_test_operations):\n                # Create some data structures\n                data = {\n                    'operation_id': i,\n                    'timestamp': time.perf_counter(),\n                    'data': list(range(100))  # Small data structure\n                }\n                memory_data.append(data)\n                \n                # Perform mouse operation\n                self.mouse.move_to(150 + i % 50, 150 + i % 30)\n                \n                # Check memory every 50 operations\n                if i % 50 == 0:\n                    current_memory = process.memory_info().rss / 1024 / 1024\n                    self.logger.info(f\"  Memory at {i} ops: {current_memory:.1f}MB\")\n                \n                await asyncio.sleep(0.001)  # 1ms pause\n            \n            final_memory = process.memory_info().rss / 1024 / 1024  # MB\n            memory_increase = final_memory - initial_memory\n            \n            self.logger.info(f\"  📊 Memory Analysis:\")\n            self.logger.info(f\"    Initial: {initial_memory:.1f}MB\")\n            self.logger.info(f\"    Final: {final_memory:.1f}MB\")\n            self.logger.info(f\"    Increase: {memory_increase:.1f}MB\")\n            \n            # Cleanup\n            del memory_data\n            \n            # Test 3: Concurrent Operations Simulation\n            self.logger.info(\"🔄 Test 3: Concurrent Operations Simulation\")\n            \n            # Simulate concurrent operations using async\n            concurrent_tasks = []\n            concurrent_count = 10\n            \n            async def simulate_user_action(user_id: int):\n                actions = 0\n                for i in range(10):  # 10 actions per \"user\"\n                    # Alternate between mouse and keyboard\n                    if i % 2 == 0:\n                        success = self.mouse.move_to(200 + user_id*20, 200 + i*10)\n                    else:\n                        success = self.keyboard.type_text(f\"User{user_id}Action{i}\")\n                    \n                    if success:\n                        actions += 1\n                    \n                    await asyncio.sleep(0.01)  # 10ms delay\n                \n                return actions\n            \n            # Create concurrent tasks\n            concurrent_start = time.perf_counter()\n            for user_id in range(concurrent_count):\n                task = asyncio.create_task(simulate_user_action(user_id))\n                concurrent_tasks.append(task)\n            \n            # Wait for all tasks to complete\n            results = await asyncio.gather(*concurrent_tasks)\n            concurrent_duration = time.perf_counter() - concurrent_start\n            \n            total_actions = sum(results)\n            max_actions = concurrent_count * 10\n            concurrent_success_rate = total_actions / max_actions if max_actions > 0 else 0\n            \n            self.logger.info(f\"  ✅ Concurrent simulation: {total_actions}/{max_actions} actions successful\")\n            self.logger.info(f\"  📊 Success rate: {concurrent_success_rate:.1%}\")\n            self.logger.info(f\"  ⚡ Throughput: {total_actions/concurrent_duration:.1f} actions/second\")\n            \n            phase_duration = time.perf_counter() - phase_start\n            self.demo_results['phase_5_stress_testing'] = {\n                'duration_seconds': round(phase_duration, 3),\n                'rapid_mouse': {\n                    'operations': rapid_operations,\n                    'successful': rapid_successes,\n                    'ops_per_second': round(rapid_ops_per_sec, 1),\n                    'success_rate': rapid_successes / rapid_operations\n                },\n                'memory_test': {\n                    'operations': memory_test_operations,\n                    'initial_memory_mb': round(initial_memory, 1),\n                    'final_memory_mb': round(final_memory, 1),\n                    'memory_increase_mb': round(memory_increase, 1)\n                },\n                'concurrent_simulation': {\n                    'simulated_users': concurrent_count,\n                    'total_actions': total_actions,\n                    'max_actions': max_actions,\n                    'success_rate': round(concurrent_success_rate, 3),\n                    'actions_per_second': round(total_actions/concurrent_duration, 1)\n                },\n                'status': 'SUCCESS'\n            }\n            \n            self.logger.info(f\"✅ Phase 5 completed in {phase_duration:.3f}s\")\n            \n        except Exception as e:\n            self.demo_results['phase_5_stress_testing'] = {\n                'status': 'FAILED',\n                'error': str(e)\n            }\n            raise\n    \n    async def _phase_6_final_analysis(self):\n        \"\"\"Phase 6: Final analysis and reporting\"\"\"\n        self.logger.info(\"📈 PHASE 6: Final Analysis & Reporting\")\n        self.logger.info(\"-\" * 50)\n        \n        phase_start = time.perf_counter()\n        \n        try:\n            # Calculate overall statistics\n            total_demo_duration = time.perf_counter() - self.start_time\n            successful_phases = sum(1 for phase in self.demo_results.values() if phase.get('status') == 'SUCCESS')\n            total_phases = len(self.demo_results)\n            \n            # Get system monitoring stats\n            system_stats = self.monitor.get_stats()\n            \n            # Collect all metrics\n            all_mouse_metrics = self.mouse.metrics.get_summary()\n            all_keyboard_metrics = self.keyboard.metrics.get_summary()\n            \n            # Generate comprehensive summary\n            summary = {\n                'demo_overview': {\n                    'total_duration_seconds': round(total_demo_duration, 3),\n                    'total_duration_minutes': round(total_demo_duration / 60, 2),\n                    'phases_total': total_phases,\n                    'phases_successful': successful_phases,\n                    'overall_success_rate': successful_phases / total_phases if total_phases > 0 else 0,\n                    'demo_timestamp': time.time()\n                },\n                'performance_highlights': {\n                    'avg_mouse_move_time_ms': self._extract_metric('phase_2_mouse_control.avg_movement_time_ms', 0),\n                    'avg_typing_speed_chars_per_sec': self._extract_metric('phase_3_keyboard_control.avg_chars_per_second', 0),\n                    'bulk_moves_per_second': self._extract_metric('phase_4_bulk_operations.bulk_movements.moves_per_second', 0),\n                    'stress_ops_per_second': self._extract_metric('phase_5_stress_testing.rapid_mouse.ops_per_second', 0)\n                },\n                'reliability_metrics': {\n                    'mouse_control_success_rate': self._extract_metric('phase_2_mouse_control.mouse_metrics.move_actual.success_rate', 0),\n                    'keyboard_control_success_rate': self._extract_metric('phase_3_keyboard_control.typing_success_rate', 0),\n                    'bulk_operations_success_rate': (\n                        self._extract_metric('phase_4_bulk_operations.bulk_movements.successful', 0) + \n                        self._extract_metric('phase_4_bulk_operations.bulk_typing.successful', 0)\n                    ) / (\n                        self._extract_metric('phase_4_bulk_operations.bulk_movements.total', 1) + \n                        self._extract_metric('phase_4_bulk_operations.bulk_typing.total', 1)\n                    ),\n                    'stress_test_success_rate': self._extract_metric('phase_5_stress_testing.concurrent_simulation.success_rate', 0)\n                },\n                'system_performance': system_stats,\n                'component_metrics': {\n                    'mouse_controller': all_mouse_metrics,\n                    'keyboard_controller': all_keyboard_metrics\n                },\n                'detailed_results': self.demo_results\n            }\n            \n            # Save comprehensive report\n            report_dir = Path(\"reports\")\n            report_dir.mkdir(exist_ok=True)\n            \n            report_file = report_dir / f\"standalone_demo_report_{int(time.time())}.json\"\n            with open(report_file, 'w', encoding='utf-8') as f:\n                json.dump(summary, f, indent=2)\n            \n            # Log final summary\n            self.logger.info(\"🎯 STANDALONE PRODUCTION DEMO COMPLETE!\")\n            self.logger.info(\"=\" * 80)\n            self.logger.info(f\"📊 Overall Success Rate: {summary['demo_overview']['overall_success_rate']:.1%}\")\n            self.logger.info(f\"⏱️ Total Duration: {summary['demo_overview']['total_duration_minutes']:.2f} minutes\")\n            self.logger.info(f\"🎯 Phases Completed: {successful_phases}/{total_phases}\")\n            \n            self.logger.info(\"\\n🏆 Performance Highlights:\")\n            highlights = summary['performance_highlights']\n            self.logger.info(f\"  🖱️ Mouse Move Avg: {highlights['avg_mouse_move_time_ms']:.3f}ms\")\n            self.logger.info(f\"  ⌨️ Typing Speed: {highlights['avg_typing_speed_chars_per_sec']:.1f} chars/sec\")\n            self.logger.info(f\"  📦 Bulk Moves: {highlights['bulk_moves_per_second']:.1f} moves/sec\")\n            self.logger.info(f\"  🚀 Stress Ops: {highlights['stress_ops_per_second']:.1f} ops/sec\")\n            \n            self.logger.info(\"\\n🛡️ Reliability Metrics:\")\n            reliability = summary['reliability_metrics']\n            self.logger.info(f\"  🖱️ Mouse Success: {reliability['mouse_control_success_rate']:.1%}\")\n            self.logger.info(f\"  ⌨️ Keyboard Success: {reliability['keyboard_control_success_rate']:.1%}\")\n            self.logger.info(f\"  📦 Bulk Success: {reliability['bulk_operations_success_rate']:.1%}\")\n            self.logger.info(f\"  🔥 Stress Success: {reliability['stress_test_success_rate']:.1%}\")\n            \n            if system_stats:\n                self.logger.info(\"\\n💻 System Performance:\")\n                self.logger.info(f\"  📊 Monitoring Duration: {system_stats['duration_seconds']:.1f}s\")\n                self.logger.info(f\"  🖥️ CPU Usage: {system_stats['cpu']['avg']:.1f}% avg ({system_stats['cpu']['min']:.1f}%-{system_stats['cpu']['max']:.1f}%)\")\n                self.logger.info(f\"  💾 Memory Usage: {system_stats['memory']['avg']:.1f}% avg ({system_stats['memory']['min']:.1f}%-{system_stats['memory']['max']:.1f}%)\")\n            \n            self.logger.info(f\"\\n📄 Detailed report saved: {report_file}\")\n            self.logger.info(\"=\" * 80)\n            \n            phase_duration = time.perf_counter() - phase_start\n            self.demo_results['phase_6_final_analysis'] = {\n                'duration_seconds': round(phase_duration, 3),\n                'status': 'SUCCESS',\n                'report_file': str(report_file),\n                'summary': summary\n            }\n            \n        except Exception as e:\n            self.demo_results['phase_6_final_analysis'] = {\n                'status': 'FAILED',\n                'error': str(e)\n            }\n            raise\n    \n    def _extract_metric(self, path: str, default: Any = 0) -> Any:\n        \"\"\"Extract a nested metric from demo results\"\"\"\n        try:\n            keys = path.split('.')\n            value = self.demo_results\n            for key in keys:\n                value = value[key]\n            return value if value is not None else default\n        except (KeyError, TypeError):\n            return default\n\nasync def main():\n    \"\"\"Main entry point for the standalone demo\"\"\"\n    try:\n        demo = StandaloneProductionDemo()\n        await demo.run_full_demo()\n        \n    except KeyboardInterrupt:\n        print(\"\\n🛑 Demo interrupted by user\")\n    except Exception as e:\n        print(f\"\\n❌ Demo failed: {e}\")\n        traceback.print_exc()\n\nif __name__ == \"__main__\":\n    asyncio.run(main())"
