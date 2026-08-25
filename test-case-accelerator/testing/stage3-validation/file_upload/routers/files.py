from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import StoredFile
from schemas import FileMetadata
from services.files import FileTooLargeError, InvalidMimeTypeError, store_file, stream_content
router = APIRouter(prefix="/files")
@router.post("/", response_model=FileMetadata, status_code=201)
async def upload(file: UploadFile = File(...), label: str = Form(..., min_length=2, max_length=80), db: Session = Depends(get_db)):
    try:
        return await store_file(db, file, label)
    except InvalidMimeTypeError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    except FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
@router.get("/{file_id}")
def download(file_id: int, db: Session = Depends(get_db)):
    stored = db.get(StoredFile, file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="file not found")
    return StreamingResponse(stream_content(stored), media_type=stored.content_type, headers={"Content-Disposition": f'attachment; filename="{stored.filename}"'})
@router.delete("/{file_id}", status_code=204)
def delete(file_id: int, db: Session = Depends(get_db)):
    stored = db.get(StoredFile, file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="file not found")
    db.delete(stored); db.commit()
