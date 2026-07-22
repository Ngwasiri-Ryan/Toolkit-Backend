from fastapi import APIRouter, UploadFile, File, Query, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import io
import datetime
from sqlalchemy.orm import Session
from app.services import pdf_service, storage
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.database import DBUser, DBJob
from app.tasks.worker import task_convert_document
from app.core.security import validate_safe_filename, validate_file_size
from app.core.middleware import check_daily_quota

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/merge-pdf")
async def merge_pdfs(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    if current_user:
        check_daily_quota(current_user, db)
        
    pdf_contents = []
    for file in files:
        validate_safe_filename(file.filename)
        content = await file.read()
        validate_file_size(content)
        pdf_contents.append(content)
        
    result = pdf_service.merge_pdfs(pdf_contents)
    return StreamingResponse(
        io.BytesIO(result), 
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=merged.pdf"}
    )

@router.post("/split-pdf")
async def split_pdf(
    file: UploadFile = File(...),
    start_page: int = Query(1, ge=1),
    end_page: int = Query(...),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    result = pdf_service.split_pdf(content, start_page, end_page)
    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=split_{start_page}_{end_page}.pdf"}
    )

@router.post("/convert/md-to-pdf")
async def convert_md_to_pdf(
    file: UploadFile = File(...),
    session_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    file_name = f"input_{datetime.datetime.now().timestamp()}_{file.filename}"
    input_path = storage.upload_file(content, file_name)
    
    job = DBJob(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        tool="md-to-pdf",
        status="pending",
        input_path=input_path,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    task_convert_document.delay(job.id, "pdf")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "tool": job.tool,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }

@router.post("/convert/docx-to-md")
async def convert_docx_to_md(
    file: UploadFile = File(...),
    session_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    file_name = f"input_{datetime.datetime.now().timestamp()}_{file.filename}"
    input_path = storage.upload_file(content, file_name)
    
    job = DBJob(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        tool="docx-to-md",
        status="pending",
        input_path=input_path,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    task_convert_document.delay(job.id, "md")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "tool": job.tool,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }
