import os
import json

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from fastapi import APIRouter, Depends, Response, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import DeadlineInterest, Researcher
from ..schemas import DeadlineInterestOut
from ..deps import get_current_user
from ..models import User
from ..slug import slugify

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


def _to_out(db: Session, interest: DeadlineInterest) -> DeadlineInterestOut:
    photo = None
    profile_slug = None
    u = interest.user
    if not u:
        return DeadlineInterestOut(
            deadline_key=interest.deadline_key,
            user_id=interest.user_id,
            user_name="",
            user_photo_url=None,
            profile_slug=None,
        )
    if u.researcher:
        photo = u.researcher.photo_url
        profile_slug = slugify(u.researcher.nome)
    elif u.researcher_id is not None:
        r = db.query(Researcher).filter(Researcher.id == u.researcher_id).first()
        if r:
            photo = r.photo_url
            profile_slug = slugify(r.nome)
    if profile_slug is None and u.nome:
        profile_slug = slugify(u.nome)
    return DeadlineInterestOut(
        deadline_key=interest.deadline_key,
        user_id=interest.user_id,
        user_name=u.nome,
        user_photo_url=photo,
        profile_slug=profile_slug,
    )


@router.get("/interests", response_model=list[DeadlineInterestOut])
def list_interests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    interests = (
        db.query(DeadlineInterest)
        .options(joinedload(DeadlineInterest.user).joinedload(User.researcher))
        .all()
    )
    return [_to_out(db, i) for i in interests]


@router.post("/{key:path}/interest", status_code=204)
def toggle_interest(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(DeadlineInterest).filter_by(deadline_key=key, user_id=current_user.id).first()
    if existing:
        db.delete(existing)
    else:
        db.add(DeadlineInterest(deadline_key=key, user_id=current_user.id))
    db.commit()
    return Response(status_code=204)


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

    # 1. HEAD para verificar status antes de baixar
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
            msg = messages.get(
                head.status_code,
                f"A página retornou um erro inesperado (código {head.status_code}).",
            )
            raise HTTPException(status_code=422, detail=msg)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="Não foi possível alcançar a URL. Verifique sua conexão ou tente novamente.")

    # 2. Busca o HTML completo
    try:
        resp = httpx.get(body.url, timeout=15, follow_redirects=True, headers=headers)
        resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=422, detail="Erro ao baixar o conteúdo da página. Tente novamente.")

    # 2. Extrai texto relevante com BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Limita para não estourar tokens
    text = text[:12_000]

    # 3. Chama OpenAI para extrair os deadlines
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = (
        "Você é um assistente que extrai prazos (deadlines) de chamadas para submissão de artigos "
        "a partir do texto de páginas web de conferências ou workshops acadêmicos. "
        "Retorne APENAS um array JSON (sem markdown, sem código, sem explicação) com os deadlines encontrados. "
        "Cada item deve ter os campos: "
        "\"label\" (nome da conferência/evento + ano, ex: \"ICSE 2026\"), "
        "\"date\" (data no formato YYYY-MM-DD — use o prazo de submissão de artigos completos ou abstracts), "
        "\"url\" (a URL original fornecida pelo usuário). "
        "Se não encontrar nenhum deadline, retorne []. "
        "Priorize o prazo de submissão de papers completos (full papers). "
        "Se houver múltiplos prazos relevantes (ex: abstract + full paper), inclua ambos com labels distintos."
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
        raise HTTPException(status_code=502, detail="OpenAI retornou resposta inesperada.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao chamar OpenAI: {e}")

    return [ExtractedDeadline(**d) for d in deadlines]
