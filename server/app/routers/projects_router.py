from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException

from app.repositories.project_repository import (
    project_repository,
)


router = APIRouter()


APP_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = APP_DIR.parent
GENERATED_DIR = (
    SERVER_DIR / "generated"
).resolve()


@router.get("")
async def list_projects():
    projects = await project_repository.list_projects()

    return {
        "projects": projects,
        "count": len(projects),
    }


@router.get("/{project_id}")
async def get_project(
    project_id: str,
):
    project = await project_repository.get_project(
        project_id
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
):
    project = await project_repository.delete_project(
        project_id
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    filename = project.get("filename")

    file_deleted = False

    if filename:
        safe_filename = Path(
            unquote(filename)
        ).name

        candidate = (
            GENERATED_DIR / safe_filename
        ).resolve()

        if (
            GENERATED_DIR in candidate.parents
            and candidate.exists()
            and candidate.is_file()
        ):
            try:
                candidate.unlink()
                file_deleted = True
            except OSError:
                file_deleted = False

    return {
        "status": "deleted",
        "project_id": project_id,
        "file_deleted": file_deleted,
    }