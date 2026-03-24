from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import LayoutUpdate
from ..services import graph_service

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/")
def get_graph(
    institution_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    return graph_service.build_graph_payload(db, institution_id)


@router.put("/layout")
def update_layout(data: LayoutUpdate, db: Session = Depends(get_db)):
    positions = graph_service.merge_layout(db, data)
    return {"status": "ok", "positions": positions}
