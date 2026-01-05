"""Filesystem browsing endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_beta_tester.api.services.detector import detect_project, ProjectInfo


router = APIRouter()


class DirectoryEntry(BaseModel):
    """A single entry in a directory listing."""
    name: str
    path: str
    is_directory: bool
    is_project: bool = False
    project_type: str | None = None


class DirectoryListing(BaseModel):
    """Response for directory listing."""
    path: str
    parent: str | None
    entries: list[DirectoryEntry]


class ProjectDetectionResponse(BaseModel):
    """Response for project detection."""
    name: str
    path: str
    project_type: str | None
    url: str | None
    port: int | None
    registered: bool
    recommended_personalities: list[str] | None


# Default starting directory
DEFAULT_ROOT = Path.home() / "Development"


def is_project_directory(path: Path) -> tuple[bool, str | None]:
    """Check if a directory is a project root."""
    indicators = {
        "package.json": "node",
        "pyproject.toml": "python",
        "setup.py": "python",
        "Cargo.toml": "rust",
        "go.mod": "go",
    }
    for indicator, proj_type in indicators.items():
        if (path / indicator).exists():
            return True, proj_type
    return False, None


@router.get("/browse", response_model=DirectoryListing)
async def browse_directory(
    path: str = Query(default="", description="Directory path to browse")
) -> DirectoryListing:
    """Browse a directory and list its contents.

    Returns directories first, sorted alphabetically, with project indicators.
    """
    # Use default root if no path provided
    if not path:
        target = DEFAULT_ROOT
    else:
        target = Path(path).expanduser().resolve()

    # Security: only allow browsing under home directory
    home = Path.home()
    try:
        target.relative_to(home)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Cannot browse outside home directory"
        )

    if not target.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries: list[DirectoryEntry] = []

    # List directory contents
    try:
        for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            # Skip hidden files and common non-project directories
            if item.name.startswith(".") or item.name in {"node_modules", "__pycache__", ".venv", "venv", "dist", "build"}:
                continue

            is_dir = item.is_dir()
            is_proj, proj_type = (False, None)

            if is_dir:
                is_proj, proj_type = is_project_directory(item)

            entries.append(DirectoryEntry(
                name=item.name,
                path=str(item),
                is_directory=is_dir,
                is_project=is_proj,
                project_type=proj_type,
            ))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Calculate parent path
    parent = str(target.parent) if target != home else None

    return DirectoryListing(
        path=str(target),
        parent=parent,
        entries=entries,
    )


@router.get("/detect", response_model=ProjectDetectionResponse)
async def detect_project_info(
    path: str = Query(..., description="Project directory path to analyze")
) -> ProjectDetectionResponse:
    """Detect project type and find registered URL.

    Analyzes the directory to determine:
    - Project type (Next.js, Vite, FastAPI, etc.)
    - Registered URL from ports.json
    - Recommended test personalities
    """
    target = Path(path).expanduser().resolve()

    if not target.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    info = detect_project(target)

    return ProjectDetectionResponse(
        name=info.name,
        path=info.path,
        project_type=info.project_type,
        url=info.url,
        port=info.port,
        registered=info.registered,
        recommended_personalities=info.recommended_personalities,
    )
