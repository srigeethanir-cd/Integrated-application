# Expected Stage 3 Results

- Async multipart endpoint with `UploadFile`, `File(...)`, `Form(...)`, and `get_db`.
- Streaming response and async chunk generator.
- MIME and 1 MiB size business rules.
- HTTP 413, 415, 422 and 404 mappings; custom upload exceptions.
- `StoredFile` CRUD model and three `/api/files` endpoints.
