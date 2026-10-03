from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import settings
from app.services.governance import rate_limit
from app.services.observability import emit, trace_id


def create_application() -> FastAPI:
    settings.validate_for_runtime()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.environment == "development" else None,
        openapi_url="/openapi.json" if settings.environment == "development" else None,
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        token = trace_id.set(request.headers.get("X-Trace-Id") or uuid4().hex)
        try:
            emit("http.request", method=request.method, path=request.url.path)
            if request.url.path.startswith(settings.api_prefix):
                try:
                    rate_limit(request)
                except HTTPException as error:
                    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id.get()
            emit("http.response", status_code=response.status_code)
            return response
        finally:
            trace_id.reset(token)

    return app


app = create_application()
