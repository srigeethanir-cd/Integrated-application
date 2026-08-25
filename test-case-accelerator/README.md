# Test Case Accelerator

Test Case Accelerator is organized as a full-stack monorepo. The backend service is implemented with FastAPI, while the frontend boundary is reserved for future development.

## Repository structure

```text
test-case-accelerator/
├── backend/       # FastAPI service, database infrastructure, and containers
├── frontend/      # Reserved frontend workspace
├── docs/          # Shared project documentation
├── .github/       # Repository-level automation
├── .gitignore
└── README.md
```

Backend setup and operation are documented in [`backend/README.md`](backend/README.md). The frontend status is documented in [`frontend/README.md`](frontend/README.md).

## Running the backend

Run backend commands from the `backend` directory:

```bash
cd backend
docker compose up --build
```

Alternatively, run Docker Compose from the repository root:

```bash
docker compose -f backend/docker-compose.yml up --build
```
