"""FastAPI application for AI Beta Tester web UI."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from ai_beta_tester.api.routes import filesystem, sessions, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup: ensure reports directory exists
    Path("./reports").mkdir(exist_ok=True)
    yield
    # Shutdown: clean up any running sessions
    from ai_beta_tester.api.routes.sessions import session_manager
    await session_manager.shutdown()


# ── Authentication ────────────────────────────────────────────────────────────
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(key: str | None = Security(_API_KEY_HEADER)) -> None:
    """Validate the X-API-Key header against the API_KEY environment variable.

    Set API_KEY in the environment before starting the server. Requests without
    a matching key receive 401.
    """
    expected = os.environ.get("API_KEY")
    if not expected:
        # If no API_KEY is configured the server refuses all requests rather
        # than silently becoming public.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY not configured on server",
        )
    if key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


app = FastAPI(
    title="AI Beta Tester API",
    description="Backend API for AI Beta Tester web dashboard",
    version="0.1.0",
    lifespan=lifespan,
    dependencies=[Depends(_require_api_key)],
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3080",
        "http://ai-beta-tester.test",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(filesystem.router, prefix="/api", tags=["filesystem"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(reports.router, prefix="/api", tags=["reports"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-beta-tester-api"}
