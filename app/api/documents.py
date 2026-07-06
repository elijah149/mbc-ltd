from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.storage import upload_file, get_presigned_url
from app.models.user import User
from app.models.documents import Document
from app.schemas.documents import DocumentOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/documents", tags=["Document Management"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf", "image/png", "image/jpeg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE_MB = 20


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Document).all()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    department: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    file_url = upload_file(contents, file.filename, file.content_type)

    document = Document(title=title, file_url=file_url, uploaded_by=current_user.id, department=department)
    db.add(document)
    db.commit()
    db.refresh(document)

    log_action(db, user_id=current_user.id, action="Document uploaded", table_name="documents", record_id=document.id, new_value={"title": title, "file_url": file_url})
    return document


@router.get("/{document_id}/download-url")
def get_download_url(document_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"url": get_presigned_url(document.file_url)}
