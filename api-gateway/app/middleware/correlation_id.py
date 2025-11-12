import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Store in request state
        request.state.correlation_id = correlation_id
        
        # Call next middleware/endpoint
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

