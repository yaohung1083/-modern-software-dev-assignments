from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note
from ..schemas import NoteCreate, NoteRead, NoteSearchResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteRead])
def list_notes(db: Session = Depends(get_db)) -> list[NoteRead]:
    rows = db.execute(select(Note)).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/search/", response_model=NoteSearchResponse)
def search_notes(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: Literal["created_desc", "title_asc"] = "created_desc",
    db: Session = Depends(get_db),
) -> NoteSearchResponse:
    query = select(Note)
    if q:
        query = query.where(
            func.lower(Note.title).contains(q.lower(), autoescape=True)
            | func.lower(Note.content).contains(q.lower(), autoescape=True)
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    if sort == "title_asc":
        query = query.order_by(Note.title.asc(), Note.id.asc())
    else:
        query = query.order_by(Note.created_at.desc(), Note.id.desc())
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return NoteSearchResponse(
        items=[NoteRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)
