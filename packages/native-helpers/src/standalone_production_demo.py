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
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        handlers=[logging.FileHandler(log_dir / "standalone_demo.log"), logging.StreamHandler()],
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
                "total_operations": self.operation_counts[op_name],
                "successful_operations": self.success_counts[op_name],
                "success_rate": (
                    self.success_counts[op_name] / self.operation_counts[op_name]
                    if self.operation_counts[op_name] > 0
                    else 0
                ),
                "avg_time_ms": round(sum(times) / len(times) * 1000, 3) if times else 0,
                "min_time_ms": round(min(times) * 1000, 3) if times else 0,
                "max_time_ms": round(max(times) * 1000, 3) if times else 0,
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
                self.metrics.record_operation("move_cached", duration, True)
                return True

            # Move to new position
            win32api.SetCursorPos((x, y))

            # Update cache
            self.position_cache = (x, y)
            self.cache_timestamp = time.perf_counter()

            duration = time.perf_counter() - start_time
            self.metrics.record_operation("move_actual", duration, True)
            return True

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation("move_failed", duration, False)
            self.logger.error(f"Mouse move failed: {e}")
            return False

    def click(self, x: int, y: int, button: str = "left") -> bool:
        """Click at position with optimization"""
        start_time = time.perf_counter()

        try:
            # Move to position first
            if not self.move_to(x, y):
                return False

            # Map button to events
            button_events = {
                "left": (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
                "right": (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
                "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
            }

            if button not in button_events:
                return False

            down_event, up_event = button_events[button]

            # Perform click
            win32api.mouse_event(down_event, x, y, 0, 0)
            time.sleep(0.001)  # Brief delay
            win32api.mouse_event(up_event, x, y, 0, 0)

            duration = time.perf_counter() - start_time
            self.metrics.record_operation(f"click_{button}", duration, True)
            return True

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation(f"click_{button}_failed", duration, False)
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
            self.metrics.record_operation("type_text", duration, True)
            self.logger.debug(
                f"Typed {len(text)} chars in {duration:.3f}s ({chars_per_second:.1f} chars/sec)"
            )
            return True

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation("type_text_failed", duration, False)
            self.logger.error(f"Typing failed: {e}")
            return False

    def _type_ascii_char(self, char: str, delay: float):
        """Type ASCII character efficiently"""
        if char == " ":
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
        self._type_ascii_char(" ", delay)

    def press_key(self, key_code: int) -> bool:
        """Press a specific key"""
        start_time = time.perf_counter()

        try:
            win32api.keybd_event(key_code, 0, 0, 0)
            time.sleep(0.01)
            win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)

            duration = time.perf_counter() - start_time
            self.metrics.record_operation("press_key", duration, True)
            return True

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.metrics.record_operation("press_key_failed", duration, False)
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
            target=self._monitor_loop, args=(interval,), daemon=True
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
                    "timestamp": time.perf_counter(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / 1024 / 1024,
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

        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_percent"] for m in self.metrics]

        return {
            "samples": len(self.metrics),
            "cpu": {
                "avg": round(sum(cpu_values) / len(cpu_values), 2),
                "min": round(min(cpu_values), 2),
                "max": round(max(cpu_values), 2),
            },
            "memory": {
                "avg": round(sum(memory_values) / len(memory_values), 2),
                "min": round(min(memory_values), 2),
                "max": round(max(memory_values), 2),
            },
            "duration_seconds": (
                round(self.metrics[-1]["timestamp"] - self.metrics[0]["timestamp"], 2)
                if len(self.metrics) > 1
                else 0
            ),
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
            disk = psutil.disk_usage("C:\\\\")
            self.logger.info(f"  CPU Cores: {cpu_count}")
            self.logger.info(
                f"  Memory: {memory.total / 1024**3:.1f}GB total, {memory.percent:.1f}% used"
            )
            self.logger.info(
                f"  Disk: {disk.total / 1024**3:.1f}GB total, {disk.percent:.1f}% used"
            )

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
            self.demo_results["phase_1_basic_performance"] = {
                "duration_seconds": round(phase_duration, 3),
                "cpu_cores": cpu_count,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "mouse_avg_time_ms": round(avg_mouse_time * 1000, 3),
                "calculation_time_ms": round(calc_duration * 1000, 3),
                "status": "SUCCESS",
            }

            self.logger.info(f"✅ Phase 1 completed in {phase_duration:.3f}s")

        except Exception as e:
            self.demo_results["phase_1_basic_performance"] = {"status": "FAILED", "error": str(e)}
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
                (100, 100),
                (200, 100),
                (200, 200),
                (100, 200),
                (150, 150),
                (300, 300),
                (400, 300),
                (400, 400),
                (300, 400),
                (350, 350),
            ]

            movement_times = []
            for i, (x, y) in enumerate(test_positions):
                start = time.perf_counter()
                success = self.mouse.move_to(x, y)
                duration = time.perf_counter() - start
                movement_times.append(duration)

                if i % 3 == 0:  # Log every 3rd movement
                    self.logger.info(
                        f"  Move {i+1}: ({x}, {y}) in {duration*1000:.3f}ms - {'✅' if success else '❌'}"
                    )

                await asyncio.sleep(0.01)  # Brief pause

            avg_movement_time = sum(movement_times) / len(movement_times)
            successful_moves = sum(
                1 for i, _ in enumerate(test_positions) if movement_times[i] < 0.1
            )  # Under 100ms

            self.logger.info(f"  📊 Movement Results:")
            self.logger.info(f"    Average time: {avg_movement_time*1000:.3f}ms")
            self.logger.info(
                f"    Fast movements: {successful_moves}/{len(test_positions)} (under 100ms)"
            )

            # Test 2: Click Performance
            self.logger.info("👆 Test 2: Click Performance")

            click_positions = [(150, 150), (250, 250), (350, 350)]
            click_types = ["left", "right", "middle"]

            for pos in click_positions:
                for click_type in click_types:
                    start = time.perf_counter()
                    success = self.mouse.click(pos[0], pos[1], click_type)
                    duration = time.perf_counter() - start

                    self.logger.info(
                        f"  {click_type.capitalize()} click at {pos}: {duration*1000:.3f}ms - {'✅' if success else '❌'}"
                    )
                    await asyncio.sleep(0.1)

            # Get mouse metrics
            mouse_metrics = self.mouse.metrics.get_summary()

            phase_duration = time.perf_counter() - phase_start
            self.demo_results["phase_2_mouse_control"] = {
                "duration_seconds": round(phase_duration, 3),
                "movements_tested": len(test_positions),
                "avg_movement_time_ms": round(avg_movement_time * 1000, 3),
                "fast_movements": successful_moves,
                "clicks_tested": len(click_positions) * len(click_types),
                "mouse_metrics": mouse_metrics,
                "status": "SUCCESS",
            }

            self.logger.info(f"✅ Phase 2 completed in {phase_duration:.3f}s")

        except Exception as e:
            self.demo_results["phase_2_mouse_control"] = {"status": "FAILED", "error": str(e)}
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
                "A" * 50,  # Long repetitive text
            ]

            typing_results = []
            for i, text in enumerate(test_texts):
                start = time.perf_counter()
                success = self.keyboard.type_text(text, delay_ms=5)  # 5ms delay for speed
                duration = time.perf_counter() - start

                chars_per_second = len(text) / duration if duration > 0 else 0
                typing_results.append(
                    {
                        "text_length": len(text),
                        "duration_ms": round(duration * 1000, 3),
                        "chars_per_second": round(chars_per_second, 1),
                        "success": success,
                    }
                )

                self.logger.info(
                    f"  Text {i+1}: {len(text)} chars → {chars_per_second:.1f} chars/sec - {'✅' if success else '❌'}"
                )
                await asyncio.sleep(0.2)

            # Calculate averages
            avg_chars_per_sec = sum(r["chars_per_second"] for r in typing_results) / len(
                typing_results
            )
            success_rate = sum(1 for r in typing_results if r["success"]) / len(typing_results)

            self.logger.info(f"  📊 Typing Results:")
            self.logger.info(f"    Average speed: {avg_chars_per_sec:.1f} chars/sec")
            self.logger.info(f"    Success rate: {success_rate:.1%}")

            # Test 2: Special Key Presses
            self.logger.info("🔑 Test 2: Special Key Presses")

            special_keys = [
                ("ENTER", win32con.VK_RETURN),
                ("BACKSPACE", win32con.VK_BACK),
                ("TAB", win32con.VK_TAB),
                ("ESCAPE", win32con.VK_ESCAPE),
                ("SPACE", win32con.VK_SPACE),
            ]

            key_results = []
            for key_name, key_code in special_keys:
                start = time.perf_counter()
                success = self.keyboard.press_key(key_code)
                duration = time.perf_counter() - start

                key_results.append(
                    {"key": key_name, "duration_ms": round(duration * 1000, 3), "success": success}
                )

                self.logger.info(
                    f"  {key_name}: {duration*1000:.3f}ms - {'✅' if success else '❌'}"
                )
                await asyncio.sleep(0.1)

            # Get keyboard metrics
            keyboard_metrics = self.keyboard.metrics.get_summary()

            phase_duration = time.perf_counter() - phase_start
            self.demo_results["phase_3_keyboard_control"] = {
                "duration_seconds": round(phase_duration, 3),
                "texts_tested": len(test_texts),
                "avg_chars_per_second": round(avg_chars_per_sec, 1),
                "typing_success_rate": round(success_rate, 3),
                "special_keys_tested": len(special_keys),
                "typing_results": typing_results,
                "key_results": key_results,
                "keyboard_metrics": keyboard_metrics,
                "status": "SUCCESS",
            }

            self.logger.info(f"✅ Phase 3 completed in {phase_duration:.3f}s")

        except Exception as e:
            self.demo_results["phase_3_keyboard_control"] = {"status": "FAILED", "error": str(e)}
            raise

    async def _phase_4_bulk_operations(self):
        """Phase 4: Bulk operations testing"""
        self.logger.info("📦 PHASE 4: Bulk Operations")
        self.logger.info("-" * 50)

        phase_start = time.perf_counter()

        try:
            # Test 1: Bulk Mouse Movements
            self.logger.info("🖱️ Test 1: Bulk Mouse Movements")

            # Generate bulk movement operations
            bulk_positions = [(100 + i * 20, 100 + i * 10) for i in range(25)]  # 25 positions

            bulk_start = time.perf_counter()
            successful_moves = 0

            for i, (x, y) in enumerate(bulk_positions):
                success = self.mouse.move_to(x, y)
                if success:
                    successful_moves += 1

                # Brief async pause every 5 operations
                if i % 5 == 0:
                    await asyncio.sleep(0.001)

            bulk_duration = time.perf_counter() - bulk_start
            moves_per_second = len(bulk_positions) / bulk_duration if bulk_duration > 0 else 0

            self.logger.info(
                f"  ✅ Bulk movements: {successful_moves}/{len(bulk_positions)} successful"
            )
            self.logger.info(f"  ⚡ Performance: {moves_per_second:.1f} moves/second")

            # Test 2: Bulk Typing Operations
            self.logger.info("⌨️ Test 2: Bulk Typing Operations")

            # Generate bulk typing operations
            bulk_texts = [f"Text {i+1}" for i in range(10)]

            typing_start = time.perf_counter()
            successful_types = 0
            total_chars = 0

            for text in bulk_texts:
                success = self.keyboard.type_text(text, delay_ms=1)  # Very fast typing
                if success:
                    successful_types += 1
                    total_chars += len(text)
                await asyncio.sleep(0.01)  # Brief pause

            typing_duration = time.perf_counter() - typing_start
            chars_per_second = total_chars / typing_duration if typing_duration > 0 else 0

            self.logger.info(f"  ✅ Bulk typing: {successful_types}/{len(bulk_texts)} successful")
            self.logger.info(f"  ⚡ Performance: {chars_per_second:.1f} chars/second")

            # Test 3: Mixed Operations
            self.logger.info("🔄 Test 3: Mixed Operations")

            mixed_start = time.perf_counter()
            mixed_operations = 20
            successful_mixed = 0

            for i in range(mixed_operations):
                if i % 2 == 0:  # Even: mouse movement
                    success = self.mouse.move_to(200 + i * 5, 200 + i * 3)
                else:  # Odd: key press
                    success = self.keyboard.press_key(win32con.VK_SPACE)

                if success:
                    successful_mixed += 1

                await asyncio.sleep(0.005)  # 5ms pause

            mixed_duration = time.perf_counter() - mixed_start
            mixed_per_second = mixed_operations / mixed_duration if mixed_duration > 0 else 0

            self.logger.info(
                f"  ✅ Mixed operations: {successful_mixed}/{mixed_operations} successful"
            )
            self.logger.info(f"  ⚡ Performance: {mixed_per_second:.1f} operations/second")

            phase_duration = time.perf_counter() - phase_start
            self.demo_results["phase_4_bulk_operations"] = {
                "duration_seconds": round(phase_duration, 3),
                "bulk_movements": {
                    "total": len(bulk_positions),
                    "successful": successful_moves,
                    "moves_per_second": round(moves_per_second, 1),
                },
                "bulk_typing": {
                    "total": len(bulk_texts),
                    "successful": successful_types,
                    "chars_per_second": round(chars_per_second, 1),
                },
                "mixed_operations": {
                    "total": mixed_operations,
                    "successful": successful_mixed,
                    "operations_per_second": round(mixed_per_second, 1),
                },
                "status": "SUCCESS",
            }

            self.logger.info(f"✅ Phase 4 completed in {phase_duration:.3f}s")

        except Exception as e:
            self.demo_results["phase_4_bulk_operations"] = {"status": "FAILED", "error": str(e)}
            raise

    async def _phase_5_stress_testing(self):
        """Phase 5: Stress testing under load"""
        self.logger.info("🔥 PHASE 5: Stress Testing")
        self.logger.info("-" * 50)

        phase_start = time.perf_counter()

        try:
            # Test 1: Rapid Mouse Operations
            self.logger.info("🚀 Test 1: Rapid Mouse Operations")

            rapid_operations = 100
            rapid_start = time.perf_counter()
            rapid_successes = 0

            for i in range(rapid_operations):
                x = 100 + (i % 20) * 10
                y = 100 + (i % 15) * 8

                success = self.mouse.move_to(x, y)
                if success:
                    rapid_successes += 1

                # No delay for maximum speed
                if i % 25 == 0:  # Brief async yield every 25 operations
                    await asyncio.sleep(0.001)

            rapid_duration = time.perf_counter() - rapid_start
            rapid_ops_per_sec = rapid_operations / rapid_duration if rapid_duration > 0 else 0

            self.logger.info(f"  ✅ Rapid mouse: {rapid_successes}/{rapid_operations} successful")
            self.logger.info(f"  ⚡ Performance: {rapid_ops_per_sec:.1f} operations/second")

            # Test 2: Memory Usage Under Load
            self.logger.info("💾 Test 2: Memory Usage Under Load")

            import psutil

            process = psutil.Process()

            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform memory-intensive operations
            memory_test_operations = 200
            memory_data = []

            for i in range(memory_test_operations):
                # Create some data structures
                data = {
                    "operation_id": i,
                    "timestamp": time.perf_counter(),
                    "data": list(range(100)),  # Small data structure
                }
                memory_data.append(data)

                # Perform mouse operation
                self.mouse.move_to(150 + i % 50, 150 + i % 30)

                # Check memory every 50 operations
                if i % 50 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    self.logger.info(f"  Memory at {i} ops: {current_memory:.1f}MB")

                await asyncio.sleep(0.001)  # 1ms pause

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            self.logger.info(f"  📊 Memory Analysis:")
            self.logger.info(f"    Initial: {initial_memory:.1f}MB")
            self.logger.info(f"    Final: {final_memory:.1f}MB")
            self.logger.info(f"    Increase: {memory_increase:.1f}MB")

            # Cleanup
            del memory_data

            # Test 3: Concurrent Operations Simulation
            self.logger.info("🔄 Test 3: Concurrent Operations Simulation")

            # Simulate concurrent operations using async
            concurrent_tasks = []
            concurrent_count = 10

            async def simulate_user_action(user_id: int):
                actions = 0
                for i in range(10):  # 10 actions per "user"
                    # Alternate between mouse and keyboard
                    if i % 2 == 0:
                        success = self.mouse.move_to(200 + user_id * 20, 200 + i * 10)
                    else:
                        success = self.keyboard.type_text(f"User{user_id}Action{i}")

                    if success:
                        actions += 1

                    await asyncio.sleep(0.01)  # 10ms delay

                return actions

            # Create concurrent tasks
            concurrent_start = time.perf_counter()
            for user_id in range(concurrent_count):
                task = asyncio.create_task(simulate_user_action(user_id))
                concurrent_tasks.append(task)

            # Wait for all tasks to complete
            results = await asyncio.gather(*concurrent_tasks)
            concurrent_duration = time.perf_counter() - concurrent_start

            total_actions = sum(results)
            max_actions = concurrent_count * 10
            concurrent_success_rate = total_actions / max_actions if max_actions > 0 else 0

            self.logger.info(
                f"  ✅ Concurrent simulation: {total_actions}/{max_actions} actions successful"
            )
            self.logger.info(f"  📊 Success rate: {concurrent_success_rate:.1%}")
            self.logger.info(
                f"  ⚡ Throughput: {total_actions/concurrent_duration:.1f} actions/second"
            )

            phase_duration = time.perf_counter() - phase_start
            self.demo_results["phase_5_stress_testing"] = {
                "duration_seconds": round(phase_duration, 3),
                "rapid_mouse": {
                    "operations": rapid_operations,
                    "successful": rapid_successes,
                    "ops_per_second": round(rapid_ops_per_sec, 1),
                    "success_rate": rapid_successes / rapid_operations,
                },
                "memory_test": {
                    "operations": memory_test_operations,
                    "initial_memory_mb": round(initial_memory, 1),
                    "final_memory_mb": round(final_memory, 1),
                    "memory_increase_mb": round(memory_increase, 1),
                },
                "concurrent_simulation": {
                    "simulated_users": concurrent_count,
                    "total_actions": total_actions,
                    "max_actions": max_actions,
                    "success_rate": round(concurrent_success_rate, 3),
                    "actions_per_second": round(total_actions / concurrent_duration, 1),
                },
                "status": "SUCCESS",
            }

            self.logger.info(f"✅ Phase 5 completed in {phase_duration:.3f}s")

        except Exception as e:
            self.demo_results["phase_5_stress_testing"] = {"status": "FAILED", "error": str(e)}
            raise

    async def _phase_6_final_analysis(self):
        """Phase 6: Final analysis and reporting"""
        self.logger.info("📈 PHASE 6: Final Analysis & Reporting")
        self.logger.info("-" * 50)

        phase_start = time.perf_counter()

        try:
            # Calculate overall statistics
            total_demo_duration = time.perf_counter() - self.start_time
            successful_phases = sum(
                1 for phase in self.demo_results.values() if phase.get("status") == "SUCCESS"
            )
            total_phases = len(self.demo_results)

            # Get system monitoring stats
            system_stats = self.monitor.get_stats()

            # Collect all metrics
            all_mouse_metrics = self.mouse.metrics.get_summary()
            all_keyboard_metrics = self.keyboard.metrics.get_summary()

            # Generate comprehensive summary
            summary = {
                "demo_overview": {
                    "total_duration_seconds": round(total_demo_duration, 3),
                    "total_duration_minutes": round(total_demo_duration / 60, 2),
                    "phases_total": total_phases,
                    "phases_successful": successful_phases,
                    "overall_success_rate": (
                        successful_phases / total_phases if total_phases > 0 else 0
                    ),
                    "demo_timestamp": time.time(),
                },
                "performance_highlights": {
                    "avg_mouse_move_time_ms": self._extract_metric(
                        "phase_2_mouse_control.avg_movement_time_ms", 0
                    ),
                    "avg_typing_speed_chars_per_sec": self._extract_metric(
                        "phase_3_keyboard_control.avg_chars_per_second", 0
                    ),
                    "bulk_moves_per_second": self._extract_metric(
                        "phase_4_bulk_operations.bulk_movements.moves_per_second", 0
                    ),
                    "stress_ops_per_second": self._extract_metric(
                        "phase_5_stress_testing.rapid_mouse.ops_per_second", 0
                    ),
                },
                "reliability_metrics": {
                    "mouse_control_success_rate": self._extract_metric(
                        "phase_2_mouse_control.mouse_metrics.move_actual.success_rate", 0
                    ),
                    "keyboard_control_success_rate": self._extract_metric(
                        "phase_3_keyboard_control.typing_success_rate", 0
                    ),
                    "bulk_operations_success_rate": (
                        self._extract_metric("phase_4_bulk_operations.bulk_movements.successful", 0)
                        + self._extract_metric("phase_4_bulk_operations.bulk_typing.successful", 0)
                    )
                    / (
                        self._extract_metric("phase_4_bulk_operations.bulk_movements.total", 1)
                        + self._extract_metric("phase_4_bulk_operations.bulk_typing.total", 1)
                    ),
                    "stress_test_success_rate": self._extract_metric(
                        "phase_5_stress_testing.concurrent_simulation.success_rate", 0
                    ),
                },
                "system_performance": system_stats,
                "component_metrics": {
                    "mouse_controller": all_mouse_metrics,
                    "keyboard_controller": all_keyboard_metrics,
                },
                "detailed_results": self.demo_results,
            }

            # Save comprehensive report
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)

            report_file = report_dir / f"standalone_demo_report_{int(time.time())}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

            # Log final summary
            self.logger.info("🎯 STANDALONE PRODUCTION DEMO COMPLETE!")
            self.logger.info("=" * 80)
            self.logger.info(
                f"📊 Overall Success Rate: {summary['demo_overview']['overall_success_rate']:.1%}"
            )
            self.logger.info(
                f"⏱️ Total Duration: {summary['demo_overview']['total_duration_minutes']:.2f} minutes"
            )
            self.logger.info(f"🎯 Phases Completed: {successful_phases}/{total_phases}")

            self.logger.info("\n🏆 Performance Highlights:")
            highlights = summary["performance_highlights"]
            self.logger.info(f"  🖱️ Mouse Move Avg: {highlights['avg_mouse_move_time_ms']:.3f}ms")
            self.logger.info(
                f"  ⌨️ Typing Speed: {highlights['avg_typing_speed_chars_per_sec']:.1f} chars/sec"
            )
            self.logger.info(
                f"  📦 Bulk Moves: {highlights['bulk_moves_per_second']:.1f} moves/sec"
            )
            self.logger.info(f"  🚀 Stress Ops: {highlights['stress_ops_per_second']:.1f} ops/sec")

            self.logger.info("\n🛡️ Reliability Metrics:")
            reliability = summary["reliability_metrics"]
            self.logger.info(f"  🖱️ Mouse Success: {reliability['mouse_control_success_rate']:.1%}")
            self.logger.info(
                f"  ⌨️ Keyboard Success: {reliability['keyboard_control_success_rate']:.1%}"
            )
            self.logger.info(
                f"  📦 Bulk Success: {reliability['bulk_operations_success_rate']:.1%}"
            )
            self.logger.info(f"  🔥 Stress Success: {reliability['stress_test_success_rate']:.1%}")

            if system_stats:
                self.logger.info("\n💻 System Performance:")
                self.logger.info(
                    f"  📊 Monitoring Duration: {system_stats['duration_seconds']:.1f}s"
                )
                self.logger.info(
                    f"  🖥️ CPU Usage: {system_stats['cpu']['avg']:.1f}% avg ({system_stats['cpu']['min']:.1f}%-{system_stats['cpu']['max']:.1f}%)"
                )
                self.logger.info(
                    f"  💾 Memory Usage: {system_stats['memory']['avg']:.1f}% avg ({system_stats['memory']['min']:.1f}%-{system_stats['memory']['max']:.1f}%)"
                )

            self.logger.info(f"\n📄 Detailed report saved: {report_file}")
            self.logger.info("=" * 80)

            phase_duration = time.perf_counter() - phase_start
            self.demo_results["phase_6_final_analysis"] = {
                "duration_seconds": round(phase_duration, 3),
                "status": "SUCCESS",
                "report_file": str(report_file),
                "summary": summary,
            }

        except Exception as e:
            self.demo_results["phase_6_final_analysis"] = {"status": "FAILED", "error": str(e)}
            raise

    def _extract_metric(self, path: str, default: Any = 0) -> Any:
        """Extract a nested metric from demo results"""
        try:
            keys = path.split(".")
            value = self.demo_results
            for key in keys:
                value = value[key]
            return value if value is not None else default
        except (KeyError, TypeError):
            return default


async def main():
    """Main entry point for the standalone demo"""
    try:
        demo = StandaloneProductionDemo()
        await demo.run_full_demo()

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
