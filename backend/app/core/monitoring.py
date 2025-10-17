"""
Prometheus Monitoring
Metrics collection and instrumentation
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog

logger = structlog.get_logger()

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

user_registrations_total = Counter(
    'user_registrations_total',
    'Total user registrations'
)

user_logins_total = Counter(
    'user_logins_total',
    'Total user logins',
    ['status']
)

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['tier']
)

authentication_failures_total = Counter(
    'authentication_failures_total',
    'Total authentication failures',
    ['reason']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next):
        """
        Collect metrics for each request
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response with metrics collected
        """
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Track request duration
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()
        
        return response


async def metrics_endpoint(request: Request) -> Response:
    """
    Prometheus metrics endpoint
    
    Args:
        request: FastAPI request
        
    Returns:
        Prometheus metrics in text format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def track_user_registration():
    """Track user registration event"""
    user_registrations_total.inc()


def track_user_login(success: bool):
    """Track user login event"""
    status = "success" if success else "failure"
    user_logins_total.labels(status=status).inc()


def track_rate_limit_exceeded(tier: str):
    """Track rate limit exceeded event"""
    rate_limit_exceeded_total.labels(tier=tier).inc()


def track_authentication_failure(reason: str):
    """Track authentication failure"""
    authentication_failures_total.labels(reason=reason).inc()


def track_redis_operation(operation: str, success: bool):
    """Track Redis operation"""
    status = "success" if success else "failure"
    redis_operations_total.labels(operation=operation, status=status).inc()
