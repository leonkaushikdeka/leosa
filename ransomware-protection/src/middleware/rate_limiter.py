import time
from collections import defaultdict
from typing import Dict

from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 100, burst_size: int = 20):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.clients: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        current_time = time.time()

        client_requests = self.clients[client_id]
        client_requests[:] = [t for t in client_requests if current_time - t < 60]

        if len(client_requests) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429, content={"detail": "Rate limit exceeded. Please try again later."}
            )

        client_requests.append(current_time)
        response = await call_next(request)
        return response

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


def rate_limit_dependency(requests_per_minute: int = 100, burst_size: int = 20):
    async def check_rate_limit(request: Request):
        pass

    return Depends(check_rate_limit)
