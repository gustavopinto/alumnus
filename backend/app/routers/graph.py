import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Researcher, Relationship, GraphLayout
from ..schemas import LayoutUpdate
from ..slug import slugify

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["graph"])

STATUS_COLORS = {
    "graduacao": "#3B82F6",   # blue
    "mestrado": "#F59E0B",    # amber
    "doutorado": "#10B981",   # green
    "professor": "#7C3AED",   # purple
}


@router.get("/")
def get_graph(db: Session = Depends(get_db)):
    researchers = db.query(Researcher).filter(Researcher.ativo == True).all()
    relationships = db.query(Relationship).all()

    layout = db.query(GraphLayout).filter(GraphLayout.name == "default").first()
    positions = layout.layout_jsonb if layout else {}

    active_ids = {r.id for r in researchers}

    nodes = []
    for r in researchers:
        pos = positions.get(str(r.id), {"x": r.id * 100, "y": r.id * 80})
        nodes.append({
            "id": str(r.id),
            "type": "researcher",
            "position": pos,
            "data": {
                "name": r.nome,
                "slug": slugify(r.nome),
                "photoUrl": r.photo_url,
                "status": r.status,
                "color": STATUS_COLORS.get(r.status, "#6B7280"),
            },
        })

    edges = []
    for rel in relationships:
        if rel.source_researcher_id in active_ids and rel.target_researcher_id in active_ids:
            edges.append({
                "id": f"e{rel.id}",
                "source": str(rel.source_researcher_id),
                "target": str(rel.target_researcher_id),
            })

    return {"nodes": nodes, "edges": edges}


@router.put("/layout")
def update_layout(data: LayoutUpdate, db: Session = Depends(get_db)):
    layout = db.query(GraphLayout).filter(GraphLayout.name == "default").first()
    if not layout:
        layout = GraphLayout(name="default", layout_jsonb={})
        db.add(layout)

    current = dict(layout.layout_jsonb or {})
    layout.layout_jsonb = {**current, **data.positions}
    db.commit()
    db.refresh(layout)
    logger.info("Layout updated")
    return {"status": "ok", "positions": layout.layout_jsonb}
