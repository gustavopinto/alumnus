import logging

from sqlalchemy.orm import Session

from ..models import GraphLayout, Professor, Relationship, Researcher
from ..schemas import LayoutUpdate
from ..slug import slugify

logger = logging.getLogger(__name__)

STATUS_COLORS = {
    "graduacao": "#3B82F6",
    "mestrado":  "#F59E0B",
    "doutorado": "#10B981",
    "postdoc":   "#06B6D4",
    "professor": "#7C3AED",
}


def build_graph_payload(db: Session) -> dict:
    professors    = db.query(Professor).filter(Professor.ativo == True).all()
    researchers   = db.query(Researcher).filter(Researcher.ativo == True).all()
    relationships = db.query(Relationship).all()

    layout    = db.query(GraphLayout).filter(GraphLayout.name == "default").first()
    positions = layout.layout_jsonb if layout else {}

    nodes = []

    # Nós de professores — id prefixado com "p"
    for p in professors:
        node_id = f"p{p.id}"
        pos = positions.get(node_id, {"x": 400, "y": 100})
        nodes.append({
            "id": node_id,
            "type": "researcher",
            "position": pos,
            "data": {
                "name":     p.nome,
                "slug":     slugify(p.nome),
                "photoUrl": p.user.photo_url if p.user else None,
                "status":   "professor",
                "color":    STATUS_COLORS["professor"],
            },
        })

    # Nós de pesquisadores
    active_researcher_ids = {r.id for r in researchers}
    for r in researchers:
        node_id = str(r.id)
        pos = positions.get(node_id, {"x": r.id * 100, "y": r.id * 80})
        nodes.append({
            "id": node_id,
            "type": "researcher",
            "position": pos,
            "data": {
                "name":     r.nome,
                "slug":     slugify(r.nome),
                "photoUrl": r.user.photo_url if r.user else None,
                "status":   r.status,
                "color":    STATUS_COLORS.get(r.status, "#6B7280"),
            },
        })

    edges = []

    # Arestas implícitas: orientador → pesquisador (via orientador_id)
    for r in researchers:
        if r.orientador_id:
            edges.append({
                "id":     f"orient-{r.id}",
                "source": f"p{r.orientador_id}",
                "target": str(r.id),
            })

    # Arestas explícitas: researcher ↔ researcher
    for rel in relationships:
        if rel.source_researcher_id in active_researcher_ids and rel.target_researcher_id in active_researcher_ids:
            edges.append({
                "id":     f"e{rel.id}",
                "source": str(rel.source_researcher_id),
                "target": str(rel.target_researcher_id),
            })

    return {"nodes": nodes, "edges": edges}


def merge_layout(db: Session, data: LayoutUpdate) -> dict:
    layout = db.query(GraphLayout).filter(GraphLayout.name == "default").first()
    if not layout:
        layout = GraphLayout(name="default", layout_jsonb={})
        db.add(layout)

    current = dict(layout.layout_jsonb or {})
    layout.layout_jsonb = {**current, **data.positions}
    db.commit()
    db.refresh(layout)
    logger.info("Layout updated")
    return layout.layout_jsonb
