#!/usr/bin/env python3
"""
MCP Smart Typer - Native Helpers
Main entry point for the native automation service.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

try:
    from uia_grpc_server import UIAGrpcServer
except ImportError:
    print("Warning: UIA gRPC server not available")
    UIAGrpcServer = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the native helpers service."""
    parser = argparse.ArgumentParser(
        description="MCP Smart Typer Native Helpers - Windows UIA Automation Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --port 50051              # Start UIA automation server
  %(prog)s --verbose                 # Enable verbose logging
  %(prog)s --help                    # Show this help message
        """,
    )

    parser.add_argument(
        "--port", type=int, default=50051, help="Port to listen on (default: 50051)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--host", default="localhost", help="Host to bind to (default: localhost)"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not UIAGrpcServer:
        logger.error("UIA gRPC server is not available. Please check dependencies.")
        sys.exit(1)

    logger.info(f"Starting Windows UIA automation server on {args.host}:{args.port}")
    server = UIAGrpcServer(port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
