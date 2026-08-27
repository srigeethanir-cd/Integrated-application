# Test-Case-Generation

AI-powered test case generation platform with automated browser crawling, image analysis, and LLM-driven scenario generation.

## Quick Start (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with WSL2 backend on Windows)
- Docker Compose v2+

### Setup

1. **Clone the repository** and navigate to the project root:
   ```powershell
   cd Test-Case-Generation
   ```

2. **(Optional) Configure environment variables**:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your GROQ_API_KEY, CEREBRAS_API_KEY, etc.
   ```

3. **Build and start all services**:
   ```powershell
   docker compose up --build -d
   ```

4. **Open the application**:
   - **Web UI**: [http://localhost:8080](http://localhost:8080)
   - **API Swagger Docs**: [http://localhost:8080/docs](http://localhost:8080/docs)
   - **Health Check**: [http://localhost:8080/health](http://localhost:8080/health)

### Useful Commands

| Command | Description |
|---|---|
| `docker compose up --build -d` | Build and start all services in the background |
| `docker compose up -d` | Start all services (skip build if images exist) |
| `docker compose down` | Stop and remove all containers |
| `docker compose down -v` | Stop containers and **delete all data volumes** |
| `docker compose logs -f backend` | Follow backend logs |
| `docker compose logs -f frontend` | Follow frontend logs |
| `docker compose logs -f nginx` | Follow NGINX logs |
| `docker compose restart backend` | Restart only the backend |
| `docker compose build backend` | Rebuild only the backend image |
| `docker compose build frontend` | Rebuild only the frontend image |

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Browser                       │
│              http://localhost:8080                   │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   NGINX (:80)   │  ← Port 8080 on host
              │  Reverse Proxy  │
              └───┬─────────┬───┘
          /api/*  │         │  /*
          /docs   │         │
          /health │         │
              ┌───▼───┐ ┌───▼──────┐
              │Backend│ │ Frontend │
              │(:8006)│ │ (:3000)  │
              └──┬──┬─┘ └──────────┘
                 │  │
          ┌──────▼┐ ┌▼──────┐
          │Postgres│ │ Redis │
          │(:5432) │ │(:6379)│
          └────────┘ └───────┘
```

### Services

| Service | Image | Internal Port | Description |
|---|---|---|---|
| `postgres` | `postgres:16-alpine` | 5432 | PostgreSQL database |
| `redis` | `redis:7-alpine` | 6379 | Redis cache |
| `backend` | Custom (Python 3.12) | 8006 | FastAPI backend with Playwright + ML |
| `frontend` | Custom (Node 20) | 3000 | Next.js frontend |
| `nginx` | `nginx:alpine` | 80 → host 8080 | Reverse proxy |

### Environment Variables

Key variables (set in root `.env`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | Local PostgreSQL container | Override to use external database |
| `REDIS_URL` | Local Redis container | Override to use external Redis |
| `GROQ_API_KEY` | _(empty)_ | Groq LLM API key |
| `CEREBRAS_API_KEY` | _(empty)_ | Cerebras LLM API key |

### Persistent Volumes

| Volume | Purpose |
|---|---|
| `postgres_data` | PostgreSQL data |
| `redis_data` | Redis append-only file |
| `backend_storage` | Uploaded images and analysis cache |
| `backend_artifacts` | Automation test artifacts |

---

## Local Development (without Docker)

### Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8006
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```
