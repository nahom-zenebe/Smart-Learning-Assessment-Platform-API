import time
from starlette.middlware.base import  BaseHTTPMiddleware
from fastapi import Request
import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("request_logger")


class LoggingMiddleware:
    async def dispatch(self,request:Request,call_next):
        start_time=time.time()

        resposne=await call_next(request)

        process_time = (time.time() - start_time) * 1000  # in ms
        logger.info(
            f"{request.method} {request.url.path} completed_in={process_time:.2f}ms status_code={response.status_code}"
        )

        # Add custom header with response time
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
