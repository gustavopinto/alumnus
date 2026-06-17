import logging

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Note, NoteComment, NoteReaction, User
from ..schemas import NoteCommentOut, NoteOut
from ..deps import get_current_user
from ..services import note_service, upload_service
logger = logging.getLogger(__name__)
router = APIRouter(tags=["notes"])


@router.get("/users/{user_id}/notes", response_model=list[NoteOut])
def list_notes(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("professor", "admin", "superadmin") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    notes = note_service.list_by_user(db, user_id)
    return [NoteOut.from_orm_with_creator(n) for n in notes]


@router.post("/users/{user_id}/notes", response_model=NoteOut, status_code=201)
async def create_note(
    user_id: int,
    text: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("professor", "admin", "superadmin") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    file_url, file_name = None, None
    if file and file.filename:
        file_url, file_name = await upload_service.save_upload(file, db)

    note = note_service.create(
        db,
        user_id=user_id,
        text=text,
        file_url=file_url,
        file_name=file_name,
        created_by_id=current_user.id,
    )
    return NoteOut.from_orm_with_creator(note)


@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = note_service.get_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if current_user.role not in ("professor", "admin", "superadmin") and note.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para editar esta anotação")
    note = note_service.update(db, note, text)
    return NoteOut.from_orm_with_creator(note)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = note_service.get_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if current_user.role not in ("professor", "admin", "superadmin") and note.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode remover suas próprias anotações")
    note_service.delete(db, note)


# ── Reactions ─────────────────────────────────────────────────────────────────

@router.post("/notes/{note_id}/reactions", status_code=204)
def toggle_note_reaction(
    note_id: int,
    reaction_type: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if reaction_type not in ("like", "sad", "happy"):
        raise HTTPException(status_code=422, detail="Tipo de reação inválido")
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Anotação não encontrada")
    existing = db.query(NoteReaction).filter(
        NoteReaction.note_id == note_id,
        NoteReaction.user_id == current_user.id,
    ).first()
    if existing:
        if existing.type == reaction_type:
            db.delete(existing)
        else:
            existing.type = reaction_type
    else:
        db.add(NoteReaction(note_id=note_id, user_id=current_user.id, type=reaction_type))
    db.commit()


# ── Comments ──────────────────────────────────────────────────────────────────

@router.post("/notes/{note_id}/comments", response_model=NoteCommentOut, status_code=201)
def add_note_comment(
    note_id: int,
    text: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Anotação não encontrada")
    comment = NoteComment(note_id=note_id, text=text.strip(), author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return NoteCommentOut.from_orm_with_author(comment)


@router.delete("/notes/comments/{comment_id}", status_code=204)
def delete_note_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(NoteComment).filter(NoteComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if current_user.role not in ("professor", "admin", "superadmin") and comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    db.delete(comment)
    db.commit()
