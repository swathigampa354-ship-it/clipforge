# Rate limiter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


class RateLimiter:
    @staticmethod
    def limit(limit: str):
        return limiter.limit(limit)

    @staticmethod
    async def handler(request: Request, exception: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {exception.limit.limit}",
            },
        )
