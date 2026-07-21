"""
Production gRPC Server for MCP Smart Typer
==========================================

This module provides a production-ready gRPC server that exposes the unified
MCP Smart Typer capabilities to TypeScript clients with high performance,
reliability, and comprehensive error handling.

Features:
- High-performance async gRPC server
- Comprehensive error handling and recovery
- Request/response validation and sanitization
- Performance metrics and monitoring
- Health checks and status reporting
- Graceful shutdown handling
- Connection pooling and resource management

Author: MCP Smart Typer Team
Version: 2.0 (Production gRPC)
"""

import asyncio
import json
import logging
import time
import traceback
import uuid
from concurrent import futures
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import grpc

# Import protobuf generated classes (assuming they exist)
# These would be generated from .proto files
try:
    import mcp_smart_typer_pb2 as pb2
    import mcp_smart_typer_pb2_grpc as pb2_grpc
except ImportError:
    # Create mock protobuf classes for development
    class MockProto:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class pb2:
        DetectFieldsRequest = MockProto
        DetectFieldsResponse = MockProto
        TypeTextRequest = MockProto
        TypeTextResponse = MockProto
        BulkOperationRequest = MockProto
        BulkOperationResponse = MockProto
        HealthCheckRequest = MockProto
        HealthCheckResponse = MockProto
        PerformanceReportRequest = MockProto
        PerformanceReportResponse = MockProto

        FieldResult = MockProto
        JobStatus = MockProto
        OperationResult = MockProto

    class pb2_grpc:
        class MCPSmartTyperServiceServicer:
            pass

        def add_MCPSmartTyperServiceServicer_to_server(servicer, server):
            pass


# Import our unified system
from unified_mcp_integration import (
    AutomationJob,
    FieldDetectionResult,
    UnifiedMCPSmartTyper,
    create_unified_mcp_smart_typer,
)


class MCPSmartTyperServicer(pb2_grpc.MCPSmartTyperServiceServicer):
    """
    Production gRPC servicer for MCP Smart Typer operations
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.unified_typer = None
        self._shutdown_event = asyncio.Event()
        self._request_count = 0
        self._error_count = 0
        self._start_time = time.time()

        # Initialize unified typer
        asyncio.create_task(self._initialize_unified_typer())

        self.logger.info("MCP Smart Typer gRPC Servicer initialized")

    async def _initialize_unified_typer(self):
        """Initialize the unified typer system"""
        try:
            self.unified_typer = await create_unified_mcp_smart_typer(self.config)
            self.logger.info("Unified MCP Smart Typer initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize unified typer: {e}")
            raise

    def _increment_request_count(self):
        """Increment request counter for metrics"""
        self._request_count += 1

    def _increment_error_count(self):
        """Increment error counter for metrics"""
        self._error_count += 1

    def _validate_request(self, request, required_fields: List[str]) -> bool:
        """Validate that request has required fields"""
        for field in required_fields:
            if not hasattr(request, field) or not getattr(request, field):
                return False
        return True

    def _create_error_response(
        self, response_class, message: str, error_code: str = "INTERNAL_ERROR"
    ):
        """Create standardized error response"""
        response = response_class()
        response.success = False
        response.error_message = message
        response.error_code = error_code
        response.timestamp = int(time.time() * 1000)  # milliseconds
        return response

    def _sanitize_context(self, context_dict: Dict) -> Dict:
        """Sanitize context dictionary for security"""
        sanitized = {}
        for key, value in context_dict.items():
            # Remove sensitive information
            if any(
                sensitive in key.lower() for sensitive in ["password", "token", "secret", "key"]
            ):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = str(value)[:200]  # Limit length
        return sanitized

    async def DetectFields(self, request, context):
        """Detect input fields using unified detection strategies"""
        self._increment_request_count()

        try:
            # Validate request
            if not self._validate_request(request, ["context"]):
                self._increment_error_count()
                return self._create_error_response(
                    pb2.DetectFieldsResponse,
                    "Invalid request: missing required fields",
                    "INVALID_REQUEST",
                )

            # Ensure unified typer is initialized
            if not self.unified_typer:
                await self._initialize_unified_typer()

            # Convert protobuf context to dict
            context_dict = json.loads(request.context) if request.context else {}
            context_dict = self._sanitize_context(context_dict)

            # Add request metadata
            context_dict.update(
                {
                    "request_id": str(uuid.uuid4()),
                    "client_info": context.peer() if context else "unknown",
                    "max_priority": getattr(request, "max_priority", 3),
                }
            )

            self.logger.info(f"Field detection requested with context: {list(context_dict.keys())}")

            # Perform field detection
            start_time = time.perf_counter()
            fields = await self.unified_typer.detect_fields(context_dict)
            duration = time.perf_counter() - start_time

            # Create response
            response = pb2.DetectFieldsResponse()
            response.success = True
            response.field_count = len(fields)
            response.processing_time_ms = int(duration * 1000)
            response.timestamp = int(time.time() * 1000)

            # Convert fields to protobuf format
            for field in fields:
                field_pb = response.fields.add()
                field_pb.field_id = field.field_id
                field_pb.field_type = field.field_type
                field_pb.confidence = field.confidence
                field_pb.source = field.source
                field_pb.position_x = field.position[0]
                field_pb.position_y = field.position[1]
                field_pb.size_width = field.size[0]
                field_pb.size_height = field.size[1]
                field_pb.properties = json.dumps(field.properties)
                field_pb.metadata = json.dumps(field.metadata)
                field_pb.timestamp = int(field.timestamp * 1000)

            self.logger.info(
                f"Field detection completed: {len(fields)} fields found in {duration:.3f}s"
            )
            return response

        except Exception as e:
            self._increment_error_count()
            self.logger.error(f"Field detection failed: {e}")
            self.logger.error(traceback.format_exc())
            return self._create_error_response(
                pb2.DetectFieldsResponse, f"Field detection failed: {str(e)}"
            )

    async def TypeText(self, request, context):
        """Type text into a specified field"""
        self._increment_request_count()

        try:
            # Validate request
            if not self._validate_request(request, ["field_id", "text", "context"]):
                self._increment_error_count()
                return self._create_error_response(
                    pb2.TypeTextResponse,
                    "Invalid request: missing required fields",
                    "INVALID_REQUEST",
                )

            # Ensure unified typer is initialized
            if not self.unified_typer:
                await self._initialize_unified_typer()

            # Convert protobuf context to dict
            context_dict = json.loads(request.context) if request.context else {}
            context_dict = self._sanitize_context(context_dict)

            # Add request metadata
            context_dict.update(
                {
                    "request_id": str(uuid.uuid4()),
                    "client_info": context.peer() if context else "unknown",
                    "typing_delay_ms": getattr(request, "typing_delay_ms", 10),
                }
            )

            self.logger.info(
                f"Text typing requested for field {request.field_id} (length: {len(request.text)})"
            )

            # Perform text typing
            start_time = time.perf_counter()
            success = await self.unified_typer.type_text(
                request.field_id, request.text, context_dict
            )
            duration = time.perf_counter() - start_time

            # Create response
            response = pb2.TypeTextResponse()
            response.success = success
            response.field_id = request.field_id
            response.text_length = len(request.text)
            response.processing_time_ms = int(duration * 1000)
            response.timestamp = int(time.time() * 1000)

            if not success:
                response.error_message = "Text typing failed - field may not be accessible"
                response.error_code = "TYPING_FAILED"

            self.logger.info(f"Text typing completed: success={success}, duration={duration:.3f}s")
            return response

        except Exception as e:
            self._increment_error_count()
            self.logger.error(f"Text typing failed: {e}")
            self.logger.error(traceback.format_exc())
            return self._create_error_response(
                pb2.TypeTextResponse, f"Text typing failed: {str(e)}"
            )

    async def BulkOperations(self, request, context):
        """Execute multiple operations in bulk for optimal performance"""
        self._increment_request_count()

        try:
            # Validate request
            if not self._validate_request(request, ["operations"]):
                self._increment_error_count()
                return self._create_error_response(
                    pb2.BulkOperationResponse,
                    "Invalid request: missing operations",
                    "INVALID_REQUEST",
                )

            # Ensure unified typer is initialized
            if not self.unified_typer:
                await self._initialize_unified_typer()

            # Convert protobuf operations to list of dicts
            operations = []
            for op_pb in request.operations:
                operation = {
                    "type": op_pb.type,
                    "action": op_pb.action,
                    "parameters": json.loads(op_pb.parameters) if op_pb.parameters else {},
                    "id": op_pb.id or str(uuid.uuid4()),
                }
                operations.append(operation)

            self.logger.info(f"Bulk operations requested: {len(operations)} operations")

            # Perform bulk operations
            start_time = time.perf_counter()
            results = await self.unified_typer.bulk_operations(operations)
            duration = time.perf_counter() - start_time

            # Create response
            response = pb2.BulkOperationResponse()
            response.success = True
            response.operation_count = len(operations)
            response.processing_time_ms = int(duration * 1000)
            response.timestamp = int(time.time() * 1000)

            # Convert results to protobuf format
            success_count = 0
            for result in results:
                result_pb = response.results.add()
                result_pb.operation_id = result.get("operation", {}).get("id", "")
                result_pb.success = result.get("success", False)
                result_pb.error_message = result.get("error", "")
                result_pb.timestamp = int(result.get("timestamp", time.perf_counter()) * 1000)

                if result.get("success"):
                    success_count += 1

            response.success_count = success_count
            response.failure_count = len(operations) - success_count

            self.logger.info(
                f"Bulk operations completed: {success_count}/{len(operations)} successful in {duration:.3f}s"
            )
            return response

        except Exception as e:
            self._increment_error_count()
            self.logger.error(f"Bulk operations failed: {e}")
            self.logger.error(traceback.format_exc())
            return self._create_error_response(
                pb2.BulkOperationResponse, f"Bulk operations failed: {str(e)}"
            )

    async def GetJobStatus(self, request, context):
        """Get the status of a specific automation job"""
        self._increment_request_count()

        try:
            if not self.unified_typer:
                await self._initialize_unified_typer()

            job = self.unified_typer.get_job_status(request.job_id)

            response = pb2.JobStatusResponse()
            if job:
                response.found = True
                response.job_id = job.job_id
                response.job_type = job.job_type
                response.status = job.status
                response.progress = job.progress
                response.start_time = int(job.start_time * 1000)
                if job.end_time:
                    response.end_time = int(job.end_time * 1000)
                if job.error:
                    response.error_message = job.error
                if job.result:
                    response.result = (
                        json.dumps(job.result)
                        if isinstance(job.result, (dict, list))
                        else str(job.result)
                    )
            else:
                response.found = False
                response.error_message = f"Job {request.job_id} not found"

            return response

        except Exception as e:
            self._increment_error_count()
            self.logger.error(f"Get job status failed: {e}")
            return self._create_error_response(
                pb2.JobStatusResponse, f"Get job status failed: {str(e)}"
            )

    async def GetPerformanceReport(self, request, context):
        """Get comprehensive performance and health report"""
        self._increment_request_count()

        try:
            if not self.unified_typer:
                await self._initialize_unified_typer()

            # Get performance report from unified typer
            report = self.unified_typer.get_performance_report()

            # Add server-level metrics
            uptime_seconds = time.time() - self._start_time
            report["server_metrics"] = {
                "uptime_seconds": uptime_seconds,
                "request_count": self._request_count,
                "error_count": self._error_count,
                "error_rate": self._error_count / max(self._request_count, 1),
                "requests_per_second": self._request_count / max(uptime_seconds, 1),
            }

            # Create response
            response = pb2.PerformanceReportResponse()
            response.success = True
            response.report = json.dumps(report, indent=2)
            response.timestamp = int(time.time() * 1000)

            return response

        except Exception as e:
            self._increment_error_count()
            self.logger.error(f"Get performance report failed: {e}")
            return self._create_error_response(
                pb2.PerformanceReportResponse, f"Performance report failed: {str(e)}"
            )

    async def HealthCheck(self, request, context):
        """Health check endpoint for monitoring"""
        try:
            # Check if unified typer is healthy
            is_healthy = (
                self.unified_typer is not None
                and hasattr(self.unified_typer, "device_controller")
                and self.unified_typer.device_controller is not None
            )

            response = pb2.HealthCheckResponse()
            response.status = "SERVING" if is_healthy else "NOT_SERVING"
            response.timestamp = int(time.time() * 1000)
            response.uptime_seconds = int(time.time() - self._start_time)
            response.request_count = self._request_count
            response.error_count = self._error_count

            return response

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            response = pb2.HealthCheckResponse()
            response.status = "NOT_SERVING"
            response.error_message = str(e)
            response.timestamp = int(time.time() * 1000)
            return response

    async def shutdown(self):
        """Gracefully shutdown the servicer"""
        self.logger.info("Shutting down MCP Smart Typer servicer...")

        if self.unified_typer:
            await self.unified_typer.shutdown()

        self._shutdown_event.set()
        self.logger.info("Servicer shutdown completed")


class ProductionGRPCServer:
    """
    Production-ready gRPC server for MCP Smart Typer
    """

    def __init__(self, port: int = 50051, max_workers: int = 10, config: Optional[Dict] = None):
        self.port = port
        self.max_workers = max_workers
        self.config = config or {}
        self.server = None
        self.servicer = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start the gRPC server"""
        try:
            # Create servicer
            self.servicer = MCPSmartTyperServicer(self.config)

            # Create server with thread pool
            self.server = grpc.aio.server(
                futures.ThreadPoolExecutor(max_workers=self.max_workers),
                options=[
                    ("grpc.keepalive_time_ms", 30000),
                    ("grpc.keepalive_timeout_ms", 5000),
                    ("grpc.keepalive_permit_without_calls", True),
                    ("grpc.http2.max_pings_without_data", 0),
                    ("grpc.http2.min_time_between_pings_ms", 10000),
                    ("grpc.http2.min_ping_interval_without_data_ms", 300000),
                    ("grpc.max_receive_message_length", 4 * 1024 * 1024),  # 4MB
                    ("grpc.max_send_message_length", 4 * 1024 * 1024),  # 4MB
                ],
            )

            # Add servicer to server
            pb2_grpc.add_MCPSmartTyperServiceServicer_to_server(self.servicer, self.server)

            # Bind to port
            listen_addr = f"[::]:{self.port}"
            self.server.add_insecure_port(listen_addr)

            # Start server
            await self.server.start()

            self.logger.info(f"MCP Smart Typer gRPC server started on {listen_addr}")
            self.logger.info(f"Server configuration: max_workers={self.max_workers}")

            # Wait for termination
            await self.server.wait_for_termination()

        except Exception as e:
            self.logger.error(f"Failed to start gRPC server: {e}")
            self.logger.error(traceback.format_exc())
            raise

    async def stop(self, grace_period: float = 30.0):
        """Stop the gRPC server gracefully"""
        if self.server:
            self.logger.info(f"Stopping gRPC server (grace period: {grace_period}s)...")

            # Shutdown servicer first
            if self.servicer:
                await self.servicer.shutdown()

            # Stop server
            await self.server.stop(grace_period)
            self.logger.info("gRPC server stopped")


async def main():
    """Main entry point for the production gRPC server"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Smart Typer Production gRPC Server")
    parser.add_argument("--port", type=int, default=50051, help="Port to listen on")
    parser.add_argument("--max-workers", type=int, default=10, help="Maximum worker threads")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("mcp_grpc_server.log"), logging.StreamHandler()],
    )

    # Load configuration
    config = {}
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load config file {args.config}: {e}")

    # Create and start server
    server = ProductionGRPCServer(port=args.port, max_workers=args.max_workers, config=config)

    try:
        await server.start()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
