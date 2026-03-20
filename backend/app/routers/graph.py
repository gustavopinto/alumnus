import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, Relationship, GraphLayout
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
    students = db.query(Student).filter(Student.ativo == True).all()
    relationships = db.query(Relationship).all()

    layout = db.query(GraphLayout).filter(GraphLayout.name == "default").first()
    positions = layout.layout_jsonb if layout else {}

    active_ids = {s.id for s in students}

    nodes = []
    for s in students:
        pos = positions.get(str(s.id), {"x": s.id * 100, "y": s.id * 80})
        nodes.append({
            "id": str(s.id),
            "type": "student",
            "position": pos,
            "data": {
                "name": s.nome,
                "slug": slugify(s.nome),
                "photoUrl": s.photo_url,
                "status": s.status,
                "color": STATUS_COLORS.get(s.status, "#6B7280"),
            },
        })

    edges = []
    for r in relationships:
        if r.source_student_id in active_ids and r.target_student_id in active_ids:
            edges.append({
                "id": f"e{r.id}",
                "source": str(r.source_student_id),
                "target": str(r.target_student_id),
            })

    return {"nodes": nodes, "edges": edges}


@router.put("/layout")
def update_layout(data: LayoutUpdate, db: Session = Depends(get_db)):
    layout = db.query(GraphLayout).filter(GraphLayout.name == "default").first()
    if not layout:
        layout = GraphLayout(name="default", layout_jsonb={})
        db.add(layout)

    current = layout.layout_jsonb or {}
    current.update(data.positions)
    layout.layout_jsonb = current
    db.commit()
    db.refresh(layout)
    logger.info("Layout updated")
    return {"status": "ok", "positions": layout.layout_jsonb}
