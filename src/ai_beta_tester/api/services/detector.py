"""Project type detection service."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectInfo:
    """Detected project information."""
    name: str
    path: str
    project_type: str | None = None
    url: str | None = None
    port: int | None = None
    registered: bool = False
    recommended_personalities: list[str] | None = None


PORTS_JSON_PATH = Path.home() / "Development" / "dev" / "ports.json"


def load_ports_registry() -> dict:
    """Load the ports registry from ~/Development/dev/ports.json."""
    if not PORTS_JSON_PATH.exists():
        return {}

    with open(PORTS_JSON_PATH) as f:
        return json.load(f)


def find_project_in_registry(project_path: Path) -> tuple[str, dict, str] | None:
    """Find a project in the ports registry by its path.

    Returns: (slug, config, framework_type) or None if not found.
    """
    registry = load_ports_registry()
    dev_root = Path.home() / "Development"

    # Normalize the path relative to Development folder
    try:
        rel_path = project_path.resolve().relative_to(dev_root)
    except ValueError:
        return None

    rel_path_str = str(rel_path)

    # Search through all framework types
    for framework_type, projects in registry.items():
        for slug, config in projects.items():
            if config.get("path") == rel_path_str or config.get("path") == str(project_path.name):
                return (slug, config, framework_type)

    return None


def detect_project_type(project_path: Path) -> str | None:
    """Detect project type from manifest files."""
    package_json = project_path / "package.json"
    pyproject = project_path / "pyproject.toml"
    setup_py = project_path / "setup.py"
    requirements = project_path / "requirements.txt"

    if package_json.exists():
        try:
            with open(package_json) as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            if "next" in deps:
                return "nextjs"
            elif "vite" in deps:
                return "vite"
            elif "react" in deps:
                return "react"
            elif "vue" in deps:
                return "vue"
            else:
                return "node"
        except (json.JSONDecodeError, IOError):
            return "node"

    if pyproject.exists() or setup_py.exists() or requirements.exists():
        # Check for FastAPI or Streamlit
        req_files = [pyproject, requirements]
        for req_file in req_files:
            if req_file.exists():
                content = req_file.read_text().lower()
                if "fastapi" in content:
                    return "fastapi"
                elif "streamlit" in content:
                    return "streamlit"
        return "python"

    return None


def get_recommended_personalities(project_type: str | None) -> list[str]:
    """Get recommended test personalities based on project type."""
    recommendations = {
        "nextjs": ["speedrunner", "chaos_gremlin", "adhd_founder", "methodical_newcomer"],
        "vite": ["speedrunner", "chaos_gremlin", "adhd_founder", "methodical_newcomer"],
        "react": ["speedrunner", "chaos_gremlin", "methodical_newcomer"],
        "fastapi": ["technical_exploit", "hybrid_auditor", "chaos_gremlin"],
        "streamlit": ["speedrunner", "methodical_newcomer", "overloaded_manager"],
        "python": ["technical_exploit", "chaos_gremlin"],
    }
    return recommendations.get(project_type or "", ["speedrunner"])


def detect_project(path: str | Path) -> ProjectInfo:
    """Detect project information from a directory path.

    Checks:
    1. Package.json for Node/Next/Vite projects
    2. pyproject.toml/setup.py for Python projects
    3. ~/Development/dev/ports.json for registered URL
    """
    project_path = Path(path).resolve()

    if not project_path.exists() or not project_path.is_dir():
        return ProjectInfo(
            name=project_path.name,
            path=str(project_path),
        )

    # Try to find in registry first
    registry_result = find_project_in_registry(project_path)

    if registry_result:
        slug, config, framework_type = registry_result
        port = config.get("port")
        url = f"http://{slug}.test/"
        project_type = framework_type
    else:
        # Detect type from files
        project_type = detect_project_type(project_path)
        port = None
        url = None

    return ProjectInfo(
        name=project_path.name,
        path=str(project_path),
        project_type=project_type,
        url=url,
        port=port,
        registered=registry_result is not None,
        recommended_personalities=get_recommended_personalities(project_type),
    )
