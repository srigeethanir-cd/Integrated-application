# Test Case Accelerator Backend

The backend is a production-oriented FastAPI foundation for the Test Case Accelerator platform. It currently contains infrastructure and architectural boundaries only; it intentionally includes no domain behavior, AI agents, parsing, retrieval, verification, coverage, or runtime execution.

## Structure

```text
app/
├── api/             # HTTP routing and versioned endpoints
├── core/            # Configuration, logging, constants, and security boundaries
├── database/        # SQLAlchemy base, sessions, repositories, and migrations
├── schemas/         # Pydantic transport schemas
├── services/        # Application service boundaries
├── agents/          # Reserved agent boundaries
├── prompts/         # Reserved prompt resources
├── cache/           # Cache abstractions
├── utils/           # Shared utilities
├── dependencies/    # FastAPI dependency providers
└── main.py          # FastAPI application entry point
tests/               # Unit, integration, and fixture packages
alembic/             # Alembic migration environment
docker/              # Container image definitions
docs/                # Project documentation
scripts/             # Operational scripts
```

## Local setup

Run all commands in this document from the `backend` directory.

1. Install Python 3.11 or newer and create a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and provide environment-specific values.
4. Start PostgreSQL and Redis:

   ```bash
   docker compose up -d postgres redis
   ```

5. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

The health endpoint is available at `http://localhost:8000/health`. Interactive API documentation is available at `/docs`.

## Container startup

Build and run the complete local stack with:

```bash
docker compose up --build
```

## Database migrations

Create and apply migrations through Alembic after database models are introduced:

```bash
alembic revision --autogenerate -m "migration description"
alembic upgrade head
```

The API validates the live Alembic revision during startup and refuses to
serve requests when the database is behind the application migration head.
Container deployments include the Alembic configuration and migration files.
Migrations can be applied explicitly with `alembic upgrade head`, or before
container startup by setting `RUN_DATABASE_MIGRATIONS=true`. Automatic
migration remains disabled by default for backward-compatible deployments.
