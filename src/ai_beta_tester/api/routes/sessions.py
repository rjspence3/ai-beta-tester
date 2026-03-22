"""Session management endpoints with SSE support."""

import asyncio
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai_beta_tester.api.events import event_manager, EventType
from ai_beta_tester.models import SessionConfig
from ai_beta_tester.orchestrator import Orchestrator, OrchestratorConfig
from ai_beta_tester.personalities import get_personality, list_personalities


router = APIRouter()


# ============================================
# Pydantic Models
# ============================================

class PersonalityInfo(BaseModel):
    """Information about a test personality."""
    name: str
    description: str


class CreateSessionRequest(BaseModel):
    """Request to create a new test session."""
    target_url: str
    goal: str
    personalities: list[str]
    max_actions: int = Field(default=50, ge=1, le=200)
    max_duration_seconds: int = Field(default=300, ge=10, le=1800)


class SessionSummary(BaseModel):
    """Summary of a test session."""
    id: str
    target_url: str
    goal: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    agent_count: int
    finding_count: int


class AgentProgress(BaseModel):
    """Progress of a single agent in a session."""
    personality: str
    status: str
    action_count: int
    finding_count: int


class SessionDetail(BaseModel):
    """Detailed session information."""
    id: str
    target_url: str
    goal: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    agents: list[AgentProgress]
    total_findings: int


# ============================================
# Session Manager
# ============================================

class SessionManager:
    """Manages running and completed sessions."""

    def __init__(self):
        self._sessions: dict[UUID, dict] = {}
        self._tasks: dict[UUID, asyncio.Task] = {}

    def get_session(self, session_id: UUID) -> dict | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return list(self._sessions.values())

    async def create_session(
        self,
        request: CreateSessionRequest,
        background_tasks: BackgroundTasks,
    ) -> dict:
        """Create and start a new test session."""
        # Create orchestrator
        orchestrator = Orchestrator(OrchestratorConfig())

        # Create session config
        session_config = SessionConfig(
            max_actions=request.max_actions,
            max_duration_seconds=request.max_duration_seconds,
        )

        # Create a placeholder session record
        # The actual session object will be created by the orchestrator
        from uuid import uuid4
        session_id = uuid4()

        session_record = {
            "id": str(session_id),
            "target_url": request.target_url,
            "goal": request.goal,
            "personalities": request.personalities,
            "status": "starting",
            "started_at": datetime.now(),
            "completed_at": None,
            "session_object": None,
            "error": None,
        }
        self._sessions[session_id] = session_record

        # Create event publisher for this session
        publisher = event_manager.create_publisher(session_id)

        # Run session in background
        async def run_session_task():
            try:
                session_record["status"] = "running"
                await publisher.publish(EventType.SESSION_STARTED, {
                    "session_id": str(session_id),
                    "target_url": request.target_url,
                    "goal": request.goal,
                    "personalities": request.personalities,
                })

                # Run the orchestrator with event callback
                async def event_callback(event_type: str, data: dict):
                    await publisher.publish(EventType(event_type), data)

                session = await orchestrator.run_session(
                    target_url=request.target_url,
                    goal=request.goal,
                    personalities=request.personalities,
                    session_config=session_config,
                    event_callback=event_callback,
                )

                session_record["session_object"] = session
                session_record["status"] = "completed"
                session_record["completed_at"] = datetime.now()

                await publisher.publish(EventType.SESSION_COMPLETED, {
                    "session_id": str(session_id),
                    "status": "completed",
                    "agent_count": len(session.agent_runs),
                    "total_findings": sum(r.finding_count for r in session.agent_runs),
                })

            except Exception as e:
                session_record["status"] = "failed"
                session_record["error"] = str(e)
                session_record["completed_at"] = datetime.now()

                await publisher.publish(EventType.ERROR, {
                    "session_id": str(session_id),
                    "error": str(e),
                })

            finally:
                await event_manager.close_publisher(session_id)
                self._tasks.pop(session_id, None)

        # Start background task
        task = asyncio.create_task(run_session_task())
        self._tasks[session_id] = task

        return session_record

    async def cancel_session(self, session_id: UUID) -> bool:
        """Cancel a running session."""
        task = self._tasks.get(session_id)
        if task and not task.done():
            task.cancel()
            session = self._sessions.get(session_id)
            if session:
                session["status"] = "cancelled"
                session["completed_at"] = datetime.now()
            return True
        return False

    async def shutdown(self):
        """Cancel all running sessions."""
        for session_id in list(self._tasks.keys()):
            await self.cancel_session(session_id)


# Global session manager
session_manager = SessionManager()


# ============================================
# Endpoints
# ============================================

@router.get("/personalities", response_model=list[PersonalityInfo])
async def get_personalities() -> list[PersonalityInfo]:
    """List all available test personalities."""
    personalities = []
    for name in list_personalities():
        cls = get_personality(name)
        personalities.append(PersonalityInfo(
            name=name,
            description=cls.description,
        ))
    return personalities


@router.post("/sessions", response_model=SessionSummary)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
) -> SessionSummary:
    """Create and start a new test session.

    The session runs in the background. Use the SSE endpoint to monitor progress.
    """
    # Validate personalities
    available = list_personalities()
    for name in request.personalities:
        if name not in available:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown personality '{name}'. Available: {available}"
            )

    session_record = await session_manager.create_session(request, background_tasks)

    return SessionSummary(
        id=session_record["id"],
        target_url=session_record["target_url"],
        goal=session_record["goal"],
        status=session_record["status"],
        started_at=session_record["started_at"],
        completed_at=session_record["completed_at"],
        agent_count=len(request.personalities),
        finding_count=0,
    )


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions() -> list[SessionSummary]:
    """List all sessions (running and completed)."""
    summaries = []
    for record in session_manager.list_sessions():
        session_obj = record.get("session_object")
        finding_count = 0
        if session_obj:
            finding_count = sum(r.finding_count for r in session_obj.agent_runs)

        summaries.append(SessionSummary(
            id=record["id"],
            target_url=record["target_url"],
            goal=record["goal"],
            status=record["status"],
            started_at=record["started_at"],
            completed_at=record["completed_at"],
            agent_count=len(record.get("personalities", [])),
            finding_count=finding_count,
        ))
    return summaries


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str) -> SessionDetail:
    """Get detailed information about a session."""
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    record = session_manager.get_session(uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")

    agents = []
    total_findings = 0
    session_obj = record.get("session_object")

    if session_obj:
        for run in session_obj.agent_runs:
            agents.append(AgentProgress(
                personality=run.personality,
                status=run.status.value,
                action_count=run.action_count,
                finding_count=run.finding_count,
            ))
            total_findings += run.finding_count

    return SessionDetail(
        id=record["id"],
        target_url=record["target_url"],
        goal=record["goal"],
        status=record["status"],
        started_at=record["started_at"],
        completed_at=record["completed_at"],
        agents=agents,
        total_findings=total_findings,
    )


@router.get("/sessions/{session_id}/events")
async def session_events(session_id: str):
    """Subscribe to real-time session events via Server-Sent Events."""
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    publisher = event_manager.get_publisher(uuid)
    if not publisher:
        raise HTTPException(status_code=404, detail="Session not found or already completed")

    return StreamingResponse(
        publisher.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/sessions/{session_id}")
async def cancel_session(session_id: str):
    """Cancel a running session."""
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    cancelled = await session_manager.cancel_session(uuid)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Session not running or already completed")

    return {"status": "cancelled", "session_id": session_id}
