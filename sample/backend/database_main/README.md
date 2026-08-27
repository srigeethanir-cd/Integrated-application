# Database Main

Unified database module for the AI Business Analyst Accelerator.

## Subfolder Structure:
- `core/`: Database engine, connection pool, transaction management, session factory.
- `models/`: SQLAlchemy ORM entity models (Projects, Epics, Stories, Blueprints, Artifacts, etc.).
- `repositories/`: Data access layer and specialized repository query classes.
- `migrations/`: Alembic schema migrations and version history.
- `story_database/`: Dynamic story schema generator and migration planner.
- `vector_db/`: Vector database integrations (Chroma, FAISS, Qdrant).
- `storage/`: Database files (e.g. SQLite database snapshot).
