from collections.abc import AsyncIterator
from fastapi import UploadFile
from sqlalchemy.orm import Session
from models import StoredFile

ALLOWED_TYPES = {"text/plain", "application/json", "image/png"}
MAX_SIZE = 1_048_576

class InvalidMimeTypeError(Exception):
    pass
class FileTooLargeError(Exception):
    pass

async def read_chunks(upload: UploadFile) -> bytes:
    chunks = []
    size = 0
    while chunk := await upload.read(64 * 1024):
        size += len(chunk)
        if size > MAX_SIZE:
            raise FileTooLargeError("file exceeds 1 MiB")
        chunks.append(chunk)
    return b"".join(chunks)

async def store_file(db: Session, upload: UploadFile, label: str) -> StoredFile:
    if upload.content_type not in ALLOWED_TYPES:
        raise InvalidMimeTypeError("unsupported MIME type")
    content = await read_chunks(upload)
    if not content:
        raise ValueError("empty files are not accepted")
    stored = StoredFile(filename=upload.filename or "unnamed", content_type=upload.content_type, label=label, size=len(content), content=content)
    db.add(stored); db.commit(); db.refresh(stored)
    return stored

async def stream_content(stored: StoredFile) -> AsyncIterator[bytes]:
    for offset in range(0, len(stored.content), 64 * 1024):
        yield stored.content[offset:offset + 64 * 1024]
