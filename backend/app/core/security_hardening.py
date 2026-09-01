import logging
from fastapi import Request, HTTPException, status
from functools import wraps
import time
from typing import Callable

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Security hardening middleware for FastAPI."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """Apply security middleware to request/response."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract headers
        headers = {name.decode(): value.decode() for name, value in scope.get("headers", [])}

        # Security headers to add
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                
                # Add security headers
                security_headers = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"),
                ]
                
                headers_list.extend(security_headers)
                message["headers"] = headers_list

            await send(message)

        await self.app(scope, receive, send_with_headers)


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_rate_limited(self, key: str) -> bool:
        """Check if request should be rate limited."""
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.window_seconds
        ]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return True

        self.requests[key].append(now)
        return False


class InputValidator:
    """Input validation and sanitization utilities."""

    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Validate UUID format."""
        import uuid
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        if len(username) < 3 or len(username) > 50:
            return False
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, username) is not None

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            raise ValueError("Input must be string")
        if len(value) > max_length:
            raise ValueError(f"String exceeds max length of {max_length}")
        return value.strip()


class AuditLogger:
    """Audit logging for sensitive operations."""

    def __init__(self):
        self.logger = logging.getLogger("audit")

    def log_auth_attempt(self, username: str, success: bool, ip: str):
        """Log authentication attempts."""
        status = "success" if success else "failure"
        self.logger.warning(f"AUTH_ATTEMPT: user={username}, status={status}, ip={ip}")

    def log_api_access(self, user_id: str, endpoint: str, method: str, status_code: int):
        """Log API access."""
        self.logger.info(f"API_ACCESS: user={user_id}, endpoint={endpoint}, method={method}, status={status_code}")

    def log_sensitive_operation(self, user_id: str, operation: str, resource: str, details: dict):
        """Log sensitive operations."""
        self.logger.warning(f"SENSITIVE_OP: user={user_id}, op={operation}, resource={resource}, details={details}")

    def log_error(self, user_id: str, error_type: str, message: str):
        """Log errors."""
        self.logger.error(f"ERROR: user={user_id}, type={error_type}, message={message}")


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if "payload" not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return await func(*args, **kwargs)
    return wrapper


def require_admin(func: Callable) -> Callable:
    """Decorator to require admin privileges."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        payload = kwargs.get("payload")
        if not payload or not payload.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return await func(*args, **kwargs)
    return wrapper
