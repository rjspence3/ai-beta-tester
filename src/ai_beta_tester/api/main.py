"""FastAPI application for AI Beta Tester web UI."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


app = FastAPI(
    title="AI Beta Tester API",
    description="Backend API for AI Beta Tester web dashboard",
    version="0.1.0",
    lifespan=lifespan,
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
