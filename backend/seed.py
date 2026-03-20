"""Seed script — run with: docker compose exec backend python seed.py"""

import sys
sys.path.insert(0, "/app")

from app.database import SessionLocal, engine
from app.models import Base, Student, Relationship, GraphLayout

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing data
db.query(Relationship).delete()
db.query(GraphLayout).delete()
db.query(Student).delete()
db.commit()

# --- Professor (orientador) ---
professor = Student(
    nome="Gustavo Pinto",
    status="professor",
    ativo=True,
)
db.add(professor)
db.flush()

# --- Alunos ---
students_data = [
    {"nome": "Emmanuel Dias Pereira", "status": "doutorado"},
    {"nome": "Leandro Veloso Dos Santos", "status": "mestrado"},
    {"nome": "Dannilo Cabral Rabelo", "status": "mestrado"},
    {"nome": "Ronivaldo Ferreira Silva Junior", "status": "mestrado"},
    {"nome": "Pedro Lucas Almeida Andre", "status": "graduacao"},
    {"nome": "Christian de Jesus da Costa Marinho", "status": "graduacao"},
    {"nome": "Daniel Naiff Da Costa", "status": "graduacao"},
]

student_objs = []
for s in students_data:
    obj = Student(nome=s["nome"], status=s["status"], orientador_id=professor.id, ativo=True)
    db.add(obj)
    student_objs.append(obj)

db.flush()

# --- Relações de orientação ---
for obj in student_objs:
    db.add(Relationship(
        source_student_id=professor.id,
        target_student_id=obj.id,
        relation_type="orienta",
    ))

# --- Layout inicial (2 fileiras abaixo do professor, sem sobreposição) ---
positions = {}
cx, cy = 600, 50
positions[str(professor.id)] = {"x": cx, "y": cy}

node_w, node_h = 200, 130  # largura e altura estimada dos nós com margem
row1 = student_objs[:4]  # primeira fileira: 4 alunos
row2 = student_objs[4:]  # segunda fileira: 3 alunos

for i, obj in enumerate(row1):
    x = cx - ((len(row1) - 1) * node_w / 2) + i * node_w
    y = cy + 200
    positions[str(obj.id)] = {"x": round(x), "y": round(y)}

for i, obj in enumerate(row2):
    x = cx - ((len(row2) - 1) * node_w / 2) + i * node_w
    y = cy + 400
    positions[str(obj.id)] = {"x": round(x), "y": round(y)}

db.add(GraphLayout(name="default", layout_jsonb=positions))

db.commit()
db.close()

print(f"Seed complete: 1 professor + {len(student_objs)} students + {len(student_objs)} relationships")
