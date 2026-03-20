# Alumnus

A web platform for professors to manage and visualize their academic network as an interactive graph. Each student is a node; relationships between students are edges. Clicking a node opens the student's profile page with notes and work history.

## Features

- **Interactive graph** — drag nodes, zoom, pan; layout is persisted per session
- **Student profiles** — notes with chronological history and file attachments (images/PDFs)
- **Role-based access** — professors see the full graph and manage students; students are redirected to their own profile upon login
- **Authentication** — JWT-based login and registration

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Flow (`@xyflow/react`), Tailwind CSS, Vite |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 |
| Database | PostgreSQL 16 |
| Auth | JWT (`python-jose`), bcrypt (`passlib`) |
| Infra | Docker, Docker Compose |

## Getting Started

### Prerequisites

- Docker and Docker Compose

### 1. Clone and configure

```bash
git clone <repo-url>
cd alumnus
cp .env.example .env
```

Edit `.env` and set a strong `SECRET_KEY`:

```env
SECRET_KEY=replace_with_a_long_random_string
```

### 2. Start the stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

### 3. Seed initial data (optional)

Populates the database with a professor node and 7 students:

```bash
docker compose cp backend/seed.py backend:/app/seed.py
docker compose exec backend python seed.py
```

### 4. Create your account

Navigate to `http://localhost:5173/register` and sign up as **Professor** to access the graph, or as **Student** (linked to an existing student record) to access your own profile.

## Project Structure

```
alumnus/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, startup
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── deps.py          # Auth dependencies (JWT)
│   │   ├── fileutils.py     # Upload validation and image compression
│   │   ├── slug.py          # Name-to-slug utility
│   │   └── routers/
│   │       ├── auth.py      # POST /auth/register, /auth/login, GET /auth/me
│   │       ├── students.py  # CRUD /students
│   │       ├── graph.py     # GET /graph, PUT /graph/layout
│   │       ├── notes.py     # Notes with file attachments
│   │       ├── works.py     # Projects, articles, publications
│   │       └── upload.py    # POST /upload/photo
│   ├── uploads/             # Uploaded files (mounted as Docker volume)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Routes
│   │   ├── auth.js          # Token helpers
│   │   ├── api.js           # API client (injects Bearer token)
│   │   ├── components/
│   │   │   ├── GraphView.jsx
│   │   │   ├── StudentNode.jsx
│   │   │   ├── Sidebar.jsx  # Student list + Deadlines
│   │   │   ├── Legend.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── RegisterPage.jsx
│   │       └── StudentPage.jsx
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── seed.py
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user info |
| GET | `/students/` | List students |
| GET | `/graph/` | Graph nodes + edges |
| PUT | `/graph/layout` | Save node positions |
| GET | `/students/{id}/notes` | Notes history |
| POST | `/students/{id}/notes` | Add note (+ optional file) |

## Student Status Colors

| Status | Color |
|---|---|
| Professor | Purple |
| PhD | Green |
| Master's | Amber |
| Undergraduate | Blue |

## File Uploads

- Accepted formats: JPEG, PNG, GIF, WebP, PDF
- Maximum size: 5 MB
- Images are automatically resized (max 1024 px) and compressed to JPEG quality 60
