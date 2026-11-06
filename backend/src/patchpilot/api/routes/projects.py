from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from patchpilot.db.models.project import ProjectModel
from patchpilot.db.session import get_db
from patchpilot.schemas.projects import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(req: ProjectCreate, db: Session = Depends(get_db)) -> ProjectModel:
    project = ProjectModel(
        name=req.name,
        repo_url=req.repo_url,
        default_branch=req.default_branch,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectModel]:
    return list(db.scalars(select(ProjectModel).order_by(ProjectModel.created_at.desc())).all())

