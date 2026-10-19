"""Run the Phase 2 pipeline skeleton from the repository root."""

from pathlib import Path

from src.orchestrator import build_demo_orchestrator
from src.settings import decision_log_path


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    orchestrator = build_demo_orchestrator(
        project_root,
        decision_log_path(project_root),
    )
    result = orchestrator.run("What is the undergraduate application deadline?")
    print(result["final_response"])
