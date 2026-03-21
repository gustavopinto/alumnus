# Alumnus

A web platform for professors to manage and visualize their research group as an interactive graph. Each researcher is a node; relationships between researchers are edges. Clicking a node opens the researcher's profile page with notes, meeting history, and work records.

## Features

- **Interactive graph** — drag nodes, zoom, pan; layout is persisted per session
- **Researcher profiles** — social links, WhatsApp, research interests, meeting notes with file attachments
- **Work history** — projects, articles in progress, and publications per researcher
- **Reminders** — sidebar dropdown with due dates, upcoming/overdue separation
- **Deadlines** — conference deadlines listed in the sidebar
- **Role-based access** — professors see the full graph and manage researchers; students are redirected to their own profile upon login
- **Authentication** — JWT-based login and registration
- **SQL migrations** — versioned `.sql` files applied automatically on startup

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
git clone https://github.com/gustavopinto/alumnus
cd alumnus
cp .env.example .env
```

Edit `.env` and set a strong `SECRET_KEY`:

```env
SECRET_KEY=replace_with_a_long_random_string
```

### 2. Start the app

```bash
bash dev.sh
```

This will:
1. Stop any previously running containers
2. Build and start all services (db, backend, frontend)
3. Wait for PostgreSQL to be ready
4. Apply any pending database migrations

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

### 3. Stop the app

```bash
bash dev.sh stop
```

### 4. View logs

```bash
docker compose logs -f
```

### 5. Seed initial data (optional)

Populates the database with a professor node and sample researchers:

```bash
docker compose cp backend/seed.py backend:/app/seed.py
docker compose exec backend python seed.py
```

### 6. Create your account

Navigate to `http://localhost:5173/register` and sign up as **Professor** to access the full graph, or as a **researcher** (linked to an existing email) to access your own profile.

## Project Structure

```
alumnus/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app and startup
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── deps.py              # Auth dependencies (JWT, optional user)
│   │   ├── database.py          # Engine and session
│   │   ├── fileutils.py         # Upload validation, compression, DB blob store
│   │   ├── slug.py              # Name-to-slug utility
│   │   ├── services/            # Persistence + domain logic (used by routers)
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── researcher_service.py
│   │   │   ├── manual_service.py
│   │   │   ├── board_service.py
│   │   │   ├── work_service.py
│   │   │   ├── relationship_service.py
│   │   │   ├── note_service.py
│   │   │   ├── reminder_service.py
│   │   │   ├── graph_service.py
│   │   │   ├── file_service.py
│   │   │   └── upload_service.py
│   │   └── routers/             # HTTP only: Depends, status codes, response mapping
│   │       ├── auth.py
│   │       ├── researchers.py
│   │       ├── relationships.py
│   │       ├── graph.py
│   │       ├── notes.py
│   │       ├── works.py
│   │       ├── reminders.py
│   │       ├── board.py
│   │       ├── manual.py
│   │       ├── files.py         # GET stored uploads by id
│   │       └── upload.py
│   ├── migrations/              # Versioned SQL migration files
│   ├── migrate.py               # Migration runner
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Routes
│   │   ├── auth.js              # Token helpers
│   │   ├── api.js               # API client (injects Bearer token)
│   │   ├── components/
│   │   │   ├── GraphView.jsx
│   │   │   ├── ResearcherNode.jsx  # Graph node component
│   │   │   ├── Sidebar.jsx      # Group, Reminders, Deadlines
│   │   │   ├── ResearcherForm.jsx  # Add/edit researcher form
│   │   │   ├── Footer.jsx       # GitHub link footer
│   │   │   ├── Legend.jsx
│   │   │   ├── Toast.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── RegisterPage.jsx
│   │       ├── ResearcherPage.jsx  # Researcher profile page
│   │       ├── RemindersPage.jsx
│   │       └── BoardPage.jsx    # Mural (post-its)
│   └── Dockerfile
├── docker-compose.yml
├── dev.sh                       # Start/stop helper
├── .env.example
└── seed.py
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/researchers/` | List researchers |
| POST | `/api/researchers/` | Create researcher |
| PUT | `/api/researchers/{id}` | Update researcher |
| DELETE | `/api/researchers/{id}` | Deactivate researcher |
| GET | `/api/researchers/{id}/user` | Get linked user account |
| GET | `/api/graph/` | Graph nodes + edges |
| PUT | `/api/graph/layout` | Save node positions |
| GET | `/api/researchers/{id}/notes` | Meeting notes |
| POST | `/api/researchers/{id}/notes` | Add note (+ optional file) |
| GET | `/api/researchers/{id}/works` | Works list |
| POST | `/api/researchers/{id}/works` | Add work |
| GET | `/api/reminders/` | List reminders |
| POST | `/api/reminders/` | Create reminder |
| PUT | `/api/reminders/{id}` | Update reminder |
| DELETE | `/api/reminders/{id}` | Delete reminder |
| GET | `/api/relationships/` | List relationships |
| POST | `/api/relationships/` | Create relationship |

## Researcher Status Colors

| Status | Color |
|---|---|
| Professor | Purple |
| PhD (Doutorado) | Green |
| Master's (Mestrado) | Amber |
| Undergraduate (Graduação) | Blue |

## Database Migrations

Migrations live in `backend/migrations/` as numbered `.sql` files. They are applied automatically when the app starts via `dev.sh`. To run them manually:

```bash
docker compose exec backend python3 /app/migrate.py
```

## File Uploads

- Accepted formats: JPEG, PNG, GIF, WebP, PDF
- Maximum size: 5 MB
- Images are automatically resized (max 1024 px) and compressed to JPEG quality 60

---

Want a feature? [Open an issue on GitHub](https://github.com/gustavopinto/alumnus)
