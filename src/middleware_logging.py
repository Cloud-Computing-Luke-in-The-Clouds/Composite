import logging
import time
from fastapi import Request
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Middleware to log requests before and after
async def log_requests(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    request.state.correlation_id = correlation_id

    logger.info(f"Correlation ID: {correlation_id} | Request: {request.method} {request.url}")

    # Log before the request is processed
    start_time = time.time()

    # Call the next process in the pipeline
    response = await call_next(request)

    # Log after the request is processed
    process_time = time.time() - start_time
    logger.info(
        f"Correlation ID: {correlation_id} | Response status: {response.status_code} "
        f"| Time: {process_time:.4f}s"
    )
    response.headers["X-Correlation-ID"] = correlation_id

    return response
