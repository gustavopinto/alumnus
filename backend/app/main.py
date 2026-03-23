import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, Base
from .routers import researchers, relationships, graph, upload, works, notes, auth, files, reminders, manual, deadlines, admin, groups, institutions, professors, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Alumnus API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(researchers.router,   prefix="/api")
app.include_router(relationships.router, prefix="/api")
app.include_router(graph.router,         prefix="/api")
app.include_router(upload.router,        prefix="/api")
app.include_router(works.router,         prefix="/api")
app.include_router(notes.router,         prefix="/api")
app.include_router(auth.router,          prefix="/api")
app.include_router(files.router,         prefix="/api")
app.include_router(reminders.router,     prefix="/api")
app.include_router(manual.router,        prefix="/api")
app.include_router(deadlines.router,     prefix="/api")
app.include_router(admin.router,        prefix="/api")
app.include_router(groups.router,       prefix="/api")
app.include_router(institutions.router, prefix="/api")
app.include_router(professors.router,  prefix="/api")
app.include_router(users.router,       prefix="/api")


@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Alumnus API ready")


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve React frontend for all other routes (must be last)
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    _screenshots_dir = FRONTEND_DIST / "screenshots"
    if _screenshots_dir.exists():
        app.mount("/screenshots", StaticFiles(directory=_screenshots_dir), name="screenshots")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        static_file = FRONTEND_DIST / full_path
        if static_file.is_file():
            return FileResponse(static_file)
        return FileResponse(FRONTEND_DIST / "index.html")
