# Expected Stage 3 Results

- Custom errors `JobNotFoundError`, `JobConflictError`, `DependencyUnavailableError`.
- Nested calls `update -> transition -> load_job/validate_transition`.
- HTTP 404, 409, 422 and exception-handler 503.
- Dependency metadata and commit/refresh/rollback flows.
