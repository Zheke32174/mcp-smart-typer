# Browser Automation Layer Documentation

## Overview

The browser automation layer provides comprehensive Playwright-based browser automation capabilities for the MCP Smart Typer project. This layer enables intelligent interaction with web pages, including DOM analysis, field detection, and human-like typing simulation.

## Features

### Core Capabilities

- **Multi-browser Support**: Chrome, Edge, Firefox, and WebKit
- **Connection Modes**: Attach to existing browser instances or launch new ones
- **DOM Analysis**: Intelligent detection and classification of input fields
- **Smart Field Identification**: Stable field IDs based on page URL + selectors + hash
- **Human-like Typing**: Configurable delays and natural typing patterns
- **Screenshot Capture**: Full page or element-specific screenshots for ML/OCR
- **Fallback Mechanisms**: Clipboard paste fallback when direct typing fails

### DOM Analysis Features

The system analyzes web pages to identify and classify form fields:

- **Input Elements**: `<input>` tags with various types
- **Text Areas**: `<textarea>` elements
- **Content Editable**: Elements with `contenteditable` attribute
- **Type Inference**: Intelligent guessing of field purpose (email, password, search, etc.)
- **Label Detection**: Finds associated labels using multiple strategies
- **Field Properties**: Extracts names, IDs, classes, placeholders, ARIA labels

## Architecture

### Core Classes

#### `PlaywrightBrowserAutomation`
Main automation class providing browser control and DOM analysis.

```python
from browser_automation import PlaywrightBrowserAutomation, BrowserConfig

# Create configuration
config = BrowserConfig(
    browser_type="chromium",
    headless=False,
    connect_to_existing=True,
    viewport_width=1366,
    viewport_height=768
)

# Use as async context manager
async with PlaywrightBrowserAutomation(config) as browser:
    await browser.navigate("https://example.com")
    fields = await browser.analyze_dom()
    # ... perform operations
```

#### `BrowserConfig`
Configuration class for browser automation settings.

```python
@dataclass
class BrowserConfig:
    browser_type: str = "chromium"     # chromium, firefox, webkit
    headless: bool = False             # Run in headless mode
    viewport_width: int = 1366         # Browser viewport width
    viewport_height: int = 768         # Browser viewport height
    user_agent: Optional[str] = None   # Custom user agent
    timeout: int = 30000               # Default timeout in milliseconds
    connect_to_existing: bool = True   # Try to connect to existing browser
    browser_executable_path: Optional[str] = None  # Custom browser path
    args: Optional[List[str]] = None   # Additional browser arguments
```

#### `FieldInfo`
Data class containing comprehensive information about detected form fields.

```python
@dataclass
class FieldInfo:
    field_id: str                    # Stable unique identifier
    element_type: str                # input, textarea, contenteditable
    input_type: Optional[str]        # HTML input type attribute
    selector: str                    # CSS selector
    xpath: str                       # XPath selector
    label: Optional[str]             # Associated label text
    placeholder: Optional[str]       # Placeholder text
    aria_label: Optional[str]        # ARIA label
    name: Optional[str]              # Name attribute
    id: Optional[str]                # ID attribute
    class_name: Optional[str]        # CSS class names
    inferred_type: str               # Inferred field purpose
    confidence: float                # Confidence in type inference
    bounds: Optional[Dict[str, float]]  # Element position and size
    is_visible: bool                 # Visibility state
    is_enabled: bool                 # Enabled state
```

## Usage Examples

### Basic DOM Analysis

```python
import asyncio
from browser_automation import create_browser_automation, BrowserConfig

async def analyze_page():
    config = BrowserConfig(browser_type="chromium", headless=False)
    
    async with PlaywrightBrowserAutomation(config) as browser:
        # Navigate to page
        await browser.navigate("https://example.com/login")
        
        # Analyze DOM for input fields
        fields = await browser.analyze_dom()
        
        print(f"Found {len(fields)} input fields:")
        for field in fields:
            print(f"- {field.inferred_type}: {field.selector}")
            print(f"  Label: {field.label}")
            print(f"  Confidence: {field.confidence:.2f}")

asyncio.run(analyze_page())
```

### Human-like Typing

```python
async def type_in_form():
    async with PlaywrightBrowserAutomation() as browser:
        await browser.navigate("https://example.com/form")
        
        # Type with human-like delays
        success = await browser.type_text(
            field_selector="#email",
            text="user@example.com",
            human_like=True,
            clear_first=True
        )
        
        if success:
            print("Successfully typed in email field")
        else:
            print("Failed to type - trying fallback methods")
```

### Screenshot Capture

```python
async def capture_page():
    async with PlaywrightBrowserAutomation() as browser:
        await browser.navigate("https://example.com")
        
        # Full page screenshot
        screenshot_data = await browser.capture_screenshot(
            path="full_page.png",
            full_page=True
        )
        
        # Element-specific screenshot
        form_screenshot = await browser.capture_screenshot(
            path="form_only.png",
            element_selector="form"
        )
```

### Field Type Inference

The system uses multiple strategies to infer field types:

1. **HTML Type Attributes**: Direct inspection of `type` attribute
2. **Pattern Matching**: Regex patterns against field attributes and labels
3. **Context Analysis**: Surrounding elements and labels
4. **Heuristic Scoring**: Confidence-based matching

```python
# Type inference patterns (built-in)
patterns = {
    "email": [
        (re.compile(r"email", re.IGNORECASE), 0.9),
        (re.compile(r"e-?mail", re.IGNORECASE), 0.8),
    ],
    "password": [
        (re.compile(r"password", re.IGNORECASE), 0.95),
        (re.compile(r"passwd", re.IGNORECASE), 0.9),
    ],
    "search": [
        (re.compile(r"search", re.IGNORECASE), 0.9),
        (re.compile(r"query", re.IGNORECASE), 0.8),
    ]
    # ... more patterns
}
```

### Stable Field Identification

Fields are assigned stable IDs based on:

- Page URL (domain + path)
- CSS selector
- XPath selector
- Element attributes (name, id, type)

```python
def _generate_field_id(page_url, css_selector, xpath, attributes):
    id_components = [
        urlparse(page_url).netloc + urlparse(page_url).path,
        css_selector,
        xpath,
        attributes.get("name", ""),
        attributes.get("id", ""),
        attributes.get("type", "")
    ]
    combined = "|".join(filter(None, id_components))
    return hashlib.sha256(combined.encode()).hexdigest()[:16]
```

## Extended gRPC Server

The `ExtendedUIAutomationServicer` provides gRPC endpoints for browser automation:

```python
from browser_server import create_extended_server

async def run_server():
    server, servicer = await create_extended_server("localhost", 50051)
    
    await server.start()
    print("Extended server running with browser automation...")
    
    try:
        await server.wait_for_termination()
    finally:
        await servicer.__aexit__(None, None, None)
```

### Available gRPC Methods

- `NavigateToBrowser`: Navigate to a URL
- `AnalyzeBrowserDOM`: Analyze page for input fields
- `TypeInBrowserField`: Type text with human-like delays
- `CaptureScreenshot`: Take screenshots
- `GetBrowserPageInfo`: Get page information
- `ClickBrowserElement`: Click elements
- `WaitForBrowserElement`: Wait for elements to appear
- `ConfigureBrowser`: Configure browser settings

## Installation and Setup

### Dependencies

```bash
pip install playwright>=1.40.0 lxml>=4.9.0
```

### Browser Installation

```bash
# Install Playwright browsers
playwright install chromium firefox webkit
```

### Development Setup

```bash
# Install in development mode
pip install -e .

# Run tests
python test_browser_automation.py --test google
python test_browser_automation.py --test typing
python test_browser_automation.py --test analyze --url https://example.com
```

## Configuration Options

### Browser Connection

The system can connect to existing browser instances or launch new ones:

```python
# Connect to existing browser (preferred)
config = BrowserConfig(connect_to_existing=True)

# Launch new browser instance
config = BrowserConfig(
    connect_to_existing=False,
    headless=True,  # Run headless
    args=["--no-sandbox", "--disable-dev-shm-usage"]
)
```

### Typing Simulation

Configure human-like typing behavior:

```python
class PlaywrightBrowserAutomation:
    def __init__(self, config):
        # Typing simulation parameters
        self._min_delay = 0.05      # 50ms minimum delay
        self._max_delay = 0.15      # 150ms maximum delay
        self._word_pause = 0.2      # 200ms pause between words
```

### Debugging and Logging

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Browser will log connection attempts, navigation, and operations
```

## Error Handling and Fallbacks

The system includes multiple fallback mechanisms:

1. **Browser Connection**: Try multiple browser types and ports
2. **Element Selection**: Use multiple selector strategies (CSS, XPath, field ID)
3. **Text Input**: Fallback to clipboard paste if direct typing fails
4. **Timeout Handling**: Configurable timeouts with graceful degradation

```python
async def type_text_with_fallbacks(self, selector, text):
    try:
        # Try direct typing
        await element.type(text)
    except Exception:
        try:
            # Try clipboard paste
            await self._paste_text_fallback(selector, text)
        except Exception:
            # Log error and return failure
            return False
    return True
```

## Performance Considerations

- **Browser Reuse**: Instances are cached and reused across requests
- **Lazy Loading**: Browsers are only launched when needed
- **Resource Cleanup**: Automatic cleanup of browser instances
- **Viewport Optimization**: Configurable viewport sizes for performance

## Security Considerations

- **Sandbox Mode**: Browsers run with security restrictions
- **Local Access Only**: No remote debugging ports exposed by default
- **User Data Isolation**: Each instance uses separate user data directories
- **Permission Model**: Limited access to system resources

## Testing

The test suite includes:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full workflow testing
- **Browser Compatibility**: Testing across different browsers
- **Performance Tests**: Response time and resource usage

```bash
# Run comprehensive tests
python test_browser_automation.py --test google
python test_browser_automation.py --test typing
python test_browser_automation.py --test analyze --url https://github.com/login
```

## Troubleshooting

### Common Issues

1. **Browser Not Found**
   - Install browsers: `playwright install`
   - Check PATH for browser executables

2. **Connection Failed**
   - Ensure browser is running with debugging port
   - Check firewall settings
   - Verify port availability

3. **Element Not Found**
   - Check selector syntax
   - Wait for page load completion
   - Verify element visibility

4. **Typing Failed**
   - Check field is enabled and visible
   - Verify element has focus
   - Try clipboard fallback

### Debug Mode

Enable debug logging for detailed operation information:

```python
import logging
logging.getLogger("browser_automation").setLevel(logging.DEBUG)
```

This comprehensive browser automation layer provides robust, intelligent web page interaction capabilities with excellent error handling and fallback mechanisms.
