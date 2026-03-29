import logging
import os
import json
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from fastapi import APIRouter, Depends, Response, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Deadline, DeadlineInterest, Researcher, User
from ..schemas import DeadlineCreate, DeadlineOut, DeadlineInterestOut
from ..deps import get_current_user, require_professor, require_dashboard
from ..slug import slugify

logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


def _interest_out(db: Session, interest: DeadlineInterest) -> DeadlineInterestOut:
    u = interest.user
    if not u:
        return DeadlineInterestOut(
            deadline_id=interest.deadline_id,
            user_id=interest.user_id,
            user_name="",
        )
    # Photo is stored on User; fall back to researcher name for profile slug
    photo = u.photo_url
    thumb = u.photo_thumb_url or photo
    profile_slug = None
    if u.researcher:
        profile_slug = slugify(u.researcher.nome)
    elif u.researcher_id is not None:
        r = db.query(Researcher).filter(Researcher.id == u.researcher_id).first()
        if r:
            profile_slug = slugify(r.nome)
    if profile_slug is None and u.nome:
        profile_slug = slugify(u.nome)
    return DeadlineInterestOut(
        deadline_id=interest.deadline_id,
        user_id=interest.user_id,
        user_name=u.nome,
        user_photo_url=photo,
        user_photo_thumb_url=thumb,
        profile_slug=profile_slug,
    )


# ── CRUD Deadlines ────────────────────────────────────────────────────────────

@router.get("/", response_model=list[DeadlineOut])
def list_deadlines(
    institution_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Deadline)
    if institution_id is not None:
        q = q.filter(Deadline.institution_id == institution_id)
    return q.order_by(Deadline.date).all()


@router.post("/", response_model=DeadlineOut, status_code=201)
def create_deadline(
    data: DeadlineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = Deadline(
        label=data.label,
        url=data.url,
        date=data.date,
        institution_id=data.institution_id,
        created_by_id=current_user.id,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{deadline_id}", status_code=204)
def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deadline não encontrado")
    is_admin = current_user.role in ("professor", "superadmin")
    is_creator = d.created_by_id == current_user.id
    if not is_admin and not is_creator:
        raise HTTPException(status_code=403, detail="Sem permissão para remover este deadline")
    db.delete(d)
    db.commit()
    return Response(status_code=204)


# ── Interests ─────────────────────────────────────────────────────────────────

@router.get("/interests", response_model=list[DeadlineInterestOut])
def list_interests(
    institution_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(DeadlineInterest)
        .options(
            joinedload(DeadlineInterest.user).joinedload(User.researcher),
            joinedload(DeadlineInterest.deadline),
        )
    )
    if institution_id is not None:
        q = q.join(Deadline).filter(Deadline.institution_id == institution_id)
    return [_interest_out(db, i) for i in q.all()]


@router.post("/{deadline_id}/interest", status_code=204)
def toggle_interest(
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deadline não encontrado")
    existing = db.query(DeadlineInterest).filter_by(
        deadline_id=deadline_id, user_id=current_user.id
    ).first()
    if existing:
        db.delete(existing)
    else:
        db.add(DeadlineInterest(deadline_id=deadline_id, user_id=current_user.id))
    db.commit()
    return Response(status_code=204)


# ── Extract from URL ──────────────────────────────────────────────────────────

class ExtractUrlRequest(BaseModel):
    url: str


class ExtractedDeadline(BaseModel):
    label: str
    date: str   # YYYY-MM-DD
    url: str


@router.post("/extract-url", response_model=list[ExtractedDeadline])
def extract_deadline_from_url(
    body: ExtractUrlRequest,
    current_user: User = Depends(get_current_user),
):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY não configurada no servidor.")

    headers = {"User-Agent": "Mozilla/5.0 (compatible; AlumnusBot/1.0)"}

    try:
        head = httpx.head(body.url, timeout=10, follow_redirects=True, headers=headers)
        if head.status_code >= 400:
            messages = {
                400: "A página retornou que a requisição é inválida (400).",
                401: "A página requer autenticação (401).",
                403: "O acesso a essa página é restrito (403).",
                404: "Página não encontrada. Verifique se a URL está correta (404).",
                410: "Essa página não existe mais (410).",
                429: "O servidor bloqueou o acesso temporariamente. Tente novamente em alguns minutos (429).",
                500: "O servidor da página encontrou um erro interno (500).",
                502: "O servidor da página está com problemas. Tente novamente mais tarde (502).",
                503: "O servidor da página está indisponível no momento (503).",
            }
            msg = messages.get(head.status_code, f"A página retornou um erro inesperado (código {head.status_code}).")
            raise HTTPException(status_code=422, detail=msg)
    except HTTPException:
        raise
    except Exception:
        logger.warning("HEAD request falhou para url=%s", body.url)
        raise HTTPException(status_code=422, detail="Não foi possível alcançar a URL.")

    try:
        resp = httpx.get(body.url, timeout=15, follow_redirects=True, headers=headers)
        resp.raise_for_status()
    except Exception:
        logger.warning("GET request falhou para url=%s", body.url)
        raise HTTPException(status_code=422, detail="Erro ao baixar o conteúdo da página.")

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)[:12_000]

    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = (
        "Você é um assistente que extrai prazos (deadlines) de chamadas para submissão de artigos "
        "a partir do texto de páginas web de conferências ou workshops acadêmicos. "
        "Retorne APENAS um array JSON (sem markdown, sem código, sem explicação) com os deadlines encontrados. "
        "Cada item deve ter os campos: "
        "\"label\" (nome da conferência/evento + ano, ex: \"ICSE 2026\"), "
        "\"date\" (data no formato YYYY-MM-DD), "
        "\"url\" (a URL original fornecida pelo usuário). "
        "Se não encontrar nenhum deadline, retorne []. "
        "Priorize o prazo de submissão de papers completos (full papers)."
    )
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {body.url}\n\nConteúdo da página:\n{text}"},
            ],
            temperature=0,
            max_tokens=OPENAI_MAX_TOKENS,
        )
        raw = completion.choices[0].message.content.strip()
        deadlines = json.loads(raw)
        if not isinstance(deadlines, list):
            deadlines = [deadlines]
    except json.JSONDecodeError:
        logger.error("OpenAI retornou JSON inválido para url=%s: %r", body.url, raw)
        raise HTTPException(status_code=502, detail="OpenAI retornou resposta inesperada.")
    except Exception as e:
        logger.error("Erro ao chamar OpenAI para url=%s: %s", body.url, e)
        raise HTTPException(status_code=502, detail=f"Erro ao chamar OpenAI: {e}")

    return [ExtractedDeadline(**d) for d in deadlines]
