from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from uuid import uuid4

from app.api.routes import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    @app.middleware("http")
    async def enforce_request_rate_limit(request: Request, call_next):
        from app.services.observability import emit, trace_id
        token = trace_id.set(request.headers.get("X-Trace-Id", uuid4().hex))
        emit("http.request", method=request.method, path=request.url.path)
        if request.url.path.startswith(settings.api_prefix):
            from app.services.governance import rate_limit
            try: rate_limit(request)
            except Exception as error:
                trace_id.reset(token); return JSONResponse(status_code=getattr(error, "status_code", 429), content={"detail": str(getattr(error, "detail", error))})
        response = await call_next(request); emit("http.response", status_code=response.status_code); trace_id.reset(token); return response
    return app


app = create_application()
