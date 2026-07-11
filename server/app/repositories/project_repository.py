import asyncio
import json
import os
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = APP_DIR.parent

DATA_DIR = SERVER_DIR / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"


class ProjectRepository:
    """
    Small local JSON repository for PRANA project metadata.

    Images remain in:
        server/generated/

    Metadata remains in:
        server/data/projects.json

    Writes use a temporary file followed by os.replace()
    so the main JSON file is not partially overwritten.
    """

    def __init__(self) -> None:
        self.data_dir = DATA_DIR.resolve()
        self.projects_file = PROJECTS_FILE.resolve()

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = asyncio.Lock()

        self._ensure_store()

    def _ensure_store(self) -> None:
        if not self.projects_file.exists():
            self.projects_file.write_text(
                "[]",
                encoding="utf-8",
            )

    def _read_projects_sync(
        self,
    ) -> list[dict[str, Any]]:
        self._ensure_store()

        try:
            raw = self.projects_file.read_text(
                encoding="utf-8"
            )

            data = json.loads(raw)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "PRANA project metadata store "
                "contains invalid JSON"
            ) from exc

        except OSError as exc:
            raise RuntimeError(
                "Unable to read PRANA project store"
            ) from exc

        if not isinstance(data, list):
            raise RuntimeError(
                "PRANA project store must contain "
                "a JSON array"
            )

        return data

    def _write_projects_sync(
        self,
        projects: list[dict[str, Any]],
    ) -> None:
        temp_file = self.projects_file.with_suffix(
            ".json.tmp"
        )

        serialized = json.dumps(
            projects,
            indent=2,
            ensure_ascii=False,
        )

        try:
            temp_file.write_text(
                serialized,
                encoding="utf-8",
            )

            os.replace(
                temp_file,
                self.projects_file,
            )

        except OSError as exc:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except OSError:
                pass

            raise RuntimeError(
                "Unable to persist PRANA "
                "project metadata"
            ) from exc

    async def list_projects(
        self,
    ) -> list[dict[str, Any]]:
        async with self._lock:
            projects = self._read_projects_sync()

        return sorted(
            projects,
            key=lambda item: item.get(
                "created_at",
                "",
            ),
            reverse=True,
        )

    async def get_project(
        self,
        project_id: str,
    ) -> dict[str, Any] | None:
        async with self._lock:
            projects = self._read_projects_sync()

        for project in projects:
            if project.get("id") == project_id:
                return project

        return None

    async def create_project(
        self,
        project: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._lock:
            projects = self._read_projects_sync()

            existing_index = next(
                (
                    index
                    for index, item
                    in enumerate(projects)
                    if item.get("id")
                    == project.get("id")
                ),
                None,
            )

            if existing_index is not None:
                projects[existing_index] = project
            else:
                projects.append(project)

            self._write_projects_sync(
                projects
            )

        return project

    async def delete_project(
        self,
        project_id: str,
    ) -> dict[str, Any] | None:
        async with self._lock:
            projects = self._read_projects_sync()

            target = next(
                (
                    item
                    for item in projects
                    if item.get("id")
                    == project_id
                ),
                None,
            )

            if target is None:
                return None

            remaining = [
                item
                for item in projects
                if item.get("id")
                != project_id
            ]

            self._write_projects_sync(
                remaining
            )

        return target


project_repository = ProjectRepository()