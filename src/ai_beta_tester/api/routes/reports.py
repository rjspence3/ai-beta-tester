"""Report viewing endpoints."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


router = APIRouter()

# Default reports directory
REPORTS_DIR = Path("./reports")


class ReportSummary(BaseModel):
    """Summary of a report file."""
    filename: str
    path: str
    modified_at: datetime
    size_bytes: int


class ReportContent(BaseModel):
    """Full report content."""
    filename: str
    path: str
    content: str
    modified_at: datetime


@router.get("/reports", response_model=list[ReportSummary])
async def list_reports() -> list[ReportSummary]:
    """List all available reports.

    Scans the reports directory for markdown files, sorted by modification time (newest first).
    """
    reports = []

    if not REPORTS_DIR.exists():
        return reports

    # Find all markdown files recursively
    for report_file in REPORTS_DIR.rglob("*.md"):
        stat = report_file.stat()
        reports.append(ReportSummary(
            filename=report_file.name,
            path=str(report_file),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            size_bytes=stat.st_size,
        ))

    # Sort by modification time, newest first
    reports.sort(key=lambda r: r.modified_at, reverse=True)

    return reports


@router.get("/reports/{report_path:path}", response_model=ReportContent)
async def get_report(report_path: str) -> ReportContent:
    """Get the content of a specific report.

    The report_path can be just the filename or a relative path within the reports directory.
    """
    # Try to find the report
    target = REPORTS_DIR / report_path

    if not target.exists():
        # Try searching for the filename
        matches = list(REPORTS_DIR.rglob(report_path))
        if matches:
            target = matches[0]
        else:
            raise HTTPException(status_code=404, detail="Report not found")

    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Security check: ensure path is within reports directory
    try:
        target.resolve().relative_to(REPORTS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    content = target.read_text()
    stat = target.stat()

    return ReportContent(
        filename=target.name,
        path=str(target),
        content=content,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )


@router.get("/reports/{report_path:path}/download")
async def download_report(report_path: str):
    """Download a report as a file."""
    target = REPORTS_DIR / report_path

    if not target.exists():
        matches = list(REPORTS_DIR.rglob(report_path))
        if matches:
            target = matches[0]
        else:
            raise HTTPException(status_code=404, detail="Report not found")

    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Security check
    try:
        target.resolve().relative_to(REPORTS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=target,
        filename=target.name,
        media_type="text/markdown",
    )
