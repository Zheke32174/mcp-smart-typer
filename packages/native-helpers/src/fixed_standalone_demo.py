"""
Fixed Standalone Production Demo for MCP Smart Typer
===================================================

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
Version: 2.0 (Fixed Standalone Production Demo)
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
            # Handle special characters - simplified approach
            vk_code = win32con.VK_SPACE  # Default to space for unknown chars
        
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

class FixedStandaloneDemo:
    """Fixed standalone production demonstration"""
    
    def __init__(self):
        self.logger = setup_demo_logging()
        self.mouse = OptimizedMouseController()
        self.keyboard = OptimizedKeyboardController()
        self.demo_results = {}
        self.start_time = time.perf_counter()
        
        self.logger.info("🚀 Fixed Standalone Production Demo initialized")
    
    async def run_demo(self):
        """Run the complete demo"""
        try:
            self.logger.info("=" * 80)
            self.logger.info("🔥 MCP SMART TYPER OPTIMIZED PRODUCTION DEMO")
            self.logger.info("=" * 80)
            
            # Phase 1: System Information
            await self._test_system_info()
            
            # Phase 2: Mouse Performance
            await self._test_mouse_performance()
            
            # Phase 3: Keyboard Performance
            await self._test_keyboard_performance()
            
            # Phase 4: Bulk Operations
            await self._test_bulk_operations()
            
            # Phase 5: Final Report
            await self._generate_final_report()
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            self.logger.error(traceback.format_exc())
    
    async def _test_system_info(self):
        """Test system information gathering"""
        self.logger.info("📊 PHASE 1: System Information")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Get system specs
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            
            self.logger.info(f"  🖥️ CPU Cores: {cpu_count}")
            self.logger.info(f"  💾 Memory: {memory.total / 1024**3:.1f}GB total, {memory.percent:.1f}% used")
            
            # Test mouse position retrieval speed
            position_times = []
            for i in range(50):
                start = time.perf_counter()
                pos = self.mouse.get_position()
                duration = time.perf_counter() - start
                position_times.append(duration)
            
            avg_pos_time = sum(position_times) / len(position_times)
            self.logger.info(f"  🖱️ Mouse position retrieval: {avg_pos_time*1000:.3f}ms avg")
            
            phase_duration = time.perf_counter() - phase_start
            self.demo_results['system_info'] = {
                'duration_seconds': round(phase_duration, 3),
                'cpu_cores': cpu_count,
                'memory_percent': memory.percent,
                'mouse_pos_time_ms': round(avg_pos_time * 1000, 3),
                'status': 'SUCCESS'
            }
            
            self.logger.info(f"✅ Phase 1 completed in {phase_duration:.3f}s")
            
        except Exception as e:
            self.demo_results['system_info'] = {'status': 'FAILED', 'error': str(e)}
            raise
    
    async def _test_mouse_performance(self):
        """Test optimized mouse performance"""
        self.logger.info("🖱️ PHASE 2: Mouse Performance Testing")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Test mouse movements
            test_positions = [
                (100, 100), (200, 200), (300, 300), (400, 400), (150, 250)
            ]
            
            movement_times = []
            successful_moves = 0
            
            for i, (x, y) in enumerate(test_positions):
                start = time.perf_counter()
                success = self.mouse.move_to(x, y)
                duration = time.perf_counter() - start
                movement_times.append(duration)
                
                if success:
                    successful_moves += 1
                
                self.logger.info(f"  Move {i+1}: ({x}, {y}) in {duration*1000:.3f}ms - {'✅' if success else '❌'}")
                await asyncio.sleep(0.05)  # Brief pause
            
            # Test clicks
            click_success = 0
            click_tests = 3
            
            for i in range(click_tests):
                x, y = 200 + i*50, 200
                success = self.mouse.click(x, y, 'left')
                if success:
                    click_success += 1
                
                self.logger.info(f"  Click {i+1}: ({x}, {y}) - {'✅' if success else '❌'}")
                await asyncio.sleep(0.1)
            
            avg_movement_time = sum(movement_times) / len(movement_times)
            
            phase_duration = time.perf_counter() - phase_start
            self.demo_results['mouse_performance'] = {
                'duration_seconds': round(phase_duration, 3),
                'movements_tested': len(test_positions),
                'successful_moves': successful_moves,
                'avg_movement_time_ms': round(avg_movement_time * 1000, 3),
                'clicks_tested': click_tests,
                'successful_clicks': click_success,
                'status': 'SUCCESS'
            }
            
            self.logger.info(f"  📊 Mouse Results: {successful_moves}/{len(test_positions)} moves, {click_success}/{click_tests} clicks")
            self.logger.info(f"✅ Phase 2 completed in {phase_duration:.3f}s")
            
        except Exception as e:
            self.demo_results['mouse_performance'] = {'status': 'FAILED', 'error': str(e)}
            raise
    
    async def _test_keyboard_performance(self):
        """Test optimized keyboard performance"""
        self.logger.info("⌨️ PHASE 3: Keyboard Performance Testing")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Test text typing
            test_texts = [
                "Hello World",
                "Testing 123",
                "Quick test",
                "Performance demo"
            ]
            
            typing_results = []
            for i, text in enumerate(test_texts):
                start = time.perf_counter()
                success = self.keyboard.type_text(text, delay_ms=10)
                duration = time.perf_counter() - start
                
                chars_per_second = len(text) / duration if duration > 0 else 0
                typing_results.append({
                    'text_length': len(text),
                    'duration_ms': round(duration * 1000, 3),
                    'chars_per_second': round(chars_per_second, 1),
                    'success': success
                })
                
                self.logger.info(f"  Text {i+1}: '{text}' → {chars_per_second:.1f} chars/sec - {'✅' if success else '❌'}")
                await asyncio.sleep(0.2)
            
            # Test special keys
            special_keys = [
                ('ENTER', win32con.VK_RETURN),
                ('SPACE', win32con.VK_SPACE),
                ('TAB', win32con.VK_TAB)
            ]
            
            key_results = []
            for key_name, key_code in special_keys:
                start = time.perf_counter()
                success = self.keyboard.press_key(key_code)
                duration = time.perf_counter() - start
                
                key_results.append({
                    'key': key_name,
                    'duration_ms': round(duration * 1000, 3),
                    'success': success
                })
                
                self.logger.info(f"  Key {key_name}: {duration*1000:.3f}ms - {'✅' if success else '❌'}")
                await asyncio.sleep(0.1)
            
            # Calculate averages
            avg_chars_per_sec = sum(r['chars_per_second'] for r in typing_results) / len(typing_results)
            typing_success_rate = sum(1 for r in typing_results if r['success']) / len(typing_results)
            
            phase_duration = time.perf_counter() - phase_start
            self.demo_results['keyboard_performance'] = {
                'duration_seconds': round(phase_duration, 3),
                'texts_tested': len(test_texts),
                'avg_chars_per_second': round(avg_chars_per_sec, 1),
                'typing_success_rate': round(typing_success_rate, 3),
                'special_keys_tested': len(special_keys),
                'typing_results': typing_results,
                'key_results': key_results,
                'status': 'SUCCESS'
            }
            
            self.logger.info(f"  📊 Keyboard Results: {avg_chars_per_sec:.1f} avg chars/sec, {typing_success_rate:.1%} success rate")
            self.logger.info(f"✅ Phase 3 completed in {phase_duration:.3f}s")
            
        except Exception as e:
            self.demo_results['keyboard_performance'] = {'status': 'FAILED', 'error': str(e)}
            raise
    
    async def _test_bulk_operations(self):
        """Test bulk operations performance"""
        self.logger.info("📦 PHASE 4: Bulk Operations Testing")
        self.logger.info("-" * 50)
        
        phase_start = time.perf_counter()
        
        try:
            # Bulk mouse movements
            bulk_positions = [(100 + i*15, 100 + i*10) for i in range(15)]
            
            bulk_start = time.perf_counter()
            successful_bulk_moves = 0
            
            for i, (x, y) in enumerate(bulk_positions):
                success = self.mouse.move_to(x, y)
                if success:
                    successful_bulk_moves += 1
                
                # Brief async pause every 5 operations
                if i % 5 == 0:
                    await asyncio.sleep(0.001)
            
            bulk_duration = time.perf_counter() - bulk_start
            moves_per_second = len(bulk_positions) / bulk_duration if bulk_duration > 0 else 0
            
            self.logger.info(f"  🖱️ Bulk moves: {successful_bulk_moves}/{len(bulk_positions)} successful")
            self.logger.info(f"  ⚡ Performance: {moves_per_second:.1f} moves/second")
            
            # Bulk typing
            bulk_texts = [f"Text{i}" for i in range(8)]
            
            typing_start = time.perf_counter()
            successful_bulk_types = 0
            total_chars = 0
            
            for text in bulk_texts:
                success = self.keyboard.type_text(text, delay_ms=2)
                if success:
                    successful_bulk_types += 1
                    total_chars += len(text)
                await asyncio.sleep(0.01)
            
            typing_duration = time.perf_counter() - typing_start
            chars_per_second = total_chars / typing_duration if typing_duration > 0 else 0
            
            self.logger.info(f"  ⌨️ Bulk typing: {successful_bulk_types}/{len(bulk_texts)} successful")
            self.logger.info(f"  ⚡ Performance: {chars_per_second:.1f} chars/second")
            
            phase_duration = time.perf_counter() - phase_start
            self.demo_results['bulk_operations'] = {
                'duration_seconds': round(phase_duration, 3),
                'bulk_moves': {
                    'total': len(bulk_positions),
                    'successful': successful_bulk_moves,
                    'moves_per_second': round(moves_per_second, 1)
                },
                'bulk_typing': {
                    'total': len(bulk_texts),
                    'successful': successful_bulk_types,
                    'chars_per_second': round(chars_per_second, 1)
                },
                'status': 'SUCCESS'
            }
            
            self.logger.info(f"✅ Phase 4 completed in {phase_duration:.3f}s")
            
        except Exception as e:
            self.demo_results['bulk_operations'] = {'status': 'FAILED', 'error': str(e)}
            raise
    
    async def _generate_final_report(self):
        """Generate final performance report"""
        self.logger.info("📈 PHASE 5: Final Performance Report")
        self.logger.info("-" * 50)
        
        try:
            # Calculate overall statistics
            total_demo_duration = time.perf_counter() - self.start_time
            successful_phases = sum(1 for phase in self.demo_results.values() if phase.get('status') == 'SUCCESS')
            total_phases = len(self.demo_results)
            
            # Collect metrics
            mouse_metrics = self.mouse.metrics.get_summary()
            keyboard_metrics = self.keyboard.metrics.get_summary()
            
            # Generate summary
            summary = {
                'demo_overview': {
                    'total_duration_seconds': round(total_demo_duration, 3),
                    'total_duration_minutes': round(total_demo_duration / 60, 2),
                    'phases_total': total_phases,
                    'phases_successful': successful_phases,
                    'overall_success_rate': successful_phases / total_phases if total_phases > 0 else 0,
                    'demo_timestamp': time.time()
                },
                'performance_summary': {
                    'mouse_avg_move_time_ms': self._get_metric('mouse_performance.avg_movement_time_ms', 0),
                    'keyboard_avg_chars_per_sec': self._get_metric('keyboard_performance.avg_chars_per_second', 0),
                    'bulk_moves_per_second': self._get_metric('bulk_operations.bulk_moves.moves_per_second', 0),
                    'bulk_chars_per_second': self._get_metric('bulk_operations.bulk_typing.chars_per_second', 0)
                },
                'component_metrics': {
                    'mouse_controller': mouse_metrics,
                    'keyboard_controller': keyboard_metrics
                },
                'detailed_results': self.demo_results
            }
            
            # Save report
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            
            report_file = report_dir / f"optimized_demo_report_{int(time.time())}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            # Log final summary
            self.logger.info("🎯 OPTIMIZED PRODUCTION DEMO COMPLETE!")
            self.logger.info("=" * 80)
            self.logger.info(f"📊 Overall Success Rate: {summary['demo_overview']['overall_success_rate']:.1%}")
            self.logger.info(f"⏱️ Total Duration: {summary['demo_overview']['total_duration_minutes']:.2f} minutes")
            self.logger.info(f"🎯 Phases Completed: {successful_phases}/{total_phases}")
            
            self.logger.info("\n🏆 Performance Highlights:")
            perf = summary['performance_summary']
            self.logger.info(f"  🖱️ Mouse Move Avg: {perf['mouse_avg_move_time_ms']:.3f}ms")
            self.logger.info(f"  ⌨️ Typing Speed: {perf['keyboard_avg_chars_per_sec']:.1f} chars/sec")
            self.logger.info(f"  📦 Bulk Moves: {perf['bulk_moves_per_second']:.1f} moves/sec")
            self.logger.info(f"  📦 Bulk Typing: {perf['bulk_chars_per_second']:.1f} chars/sec")
            
            self.logger.info(f"\n📄 Report saved: {report_file}")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
    
    def _get_metric(self, path: str, default: Any = 0) -> Any:
        """Extract a nested metric from demo results"""
        try:
            keys = path.split('.')
            value = self.demo_results
            for key in keys:
                value = value[key]
            return value if value is not None else default
        except (KeyError, TypeError):
            return default

async def main():
    """Main entry point"""
    try:
        demo = FixedStandaloneDemo()
        await demo.run_demo()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
