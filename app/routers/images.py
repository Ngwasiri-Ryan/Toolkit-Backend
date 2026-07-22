from fastapi import APIRouter, UploadFile, File, Query, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import io
import datetime
from sqlalchemy.orm import Session
from app.services import image_service, storage
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.database import DBUser, DBJob
from app.tasks.worker import task_remove_background
from app.core.security import validate_safe_filename, validate_file_size, sanitize_svg_content
from app.core.middleware import check_daily_quota

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/compress")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = Query(70, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if file.filename.lower().endswith(".svg") or file.content_type == "image/svg+xml":
        content = sanitize_svg_content(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    result = image_service.compress_image(content, quality=quality)
    return StreamingResponse(io.BytesIO(result), media_type=file.content_type)

@router.post("/resize")
async def resize_image(
    file: UploadFile = File(...), 
    width: int = Query(...), 
    height: int = Query(...),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if file.filename.lower().endswith(".svg") or file.content_type == "image/svg+xml":
        content = sanitize_svg_content(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    result = image_service.resize_image(content, width, height)
    return StreamingResponse(io.BytesIO(result), media_type=file.content_type)

@router.post("/crop")
async def crop_image(
    file: UploadFile = File(...),
    left: int = Query(...), top: int = Query(...),
    right: int = Query(...), bottom: int = Query(...),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if file.filename.lower().endswith(".svg") or file.content_type == "image/svg+xml":
        content = sanitize_svg_content(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    result = image_service.crop_image(content, left, top, right, bottom)
    return StreamingResponse(io.BytesIO(result), media_type=file.content_type)

@router.post("/grayscale")
async def grayscale_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if file.filename.lower().endswith(".svg") or file.content_type == "image/svg+xml":
        content = sanitize_svg_content(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    result = image_service.grayscale_image(content)
    return StreamingResponse(io.BytesIO(result), media_type=file.content_type)

@router.post("/convert")
async def convert_image(
    file: UploadFile = File(...), 
    format: str = Query(...),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if file.filename.lower().endswith(".svg") or file.content_type == "image/svg+xml":
        content = sanitize_svg_content(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    result = image_service.convert_image_format(content, format)
    # Determine fallback media type based on format string
    media_type = f"image/{format.lower()}"
    return StreamingResponse(io.BytesIO(result), media_type=media_type)

@router.post("/remove-background")
async def remove_background(
    file: UploadFile = File(...),
    session_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    validate_safe_filename(file.filename)
    content = await file.read()
    validate_file_size(content)
    if file.filename.lower().endswith(".svg") or file.content_type == "image/svg+xml":
        content = sanitize_svg_content(content)
    if current_user:
        check_daily_quota(current_user, db)
        
    # Save input file to storage
    file_name = f"input_{datetime.datetime.now().timestamp()}_{file.filename}"
    input_path = storage.upload_file(content, file_name)
    
    # Create DB Job
    job = DBJob(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        tool="remove-background",
        status="pending",
        input_path=input_path,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger Celery Task
    task_remove_background.delay(job.id)
    
    return {
        "job_id": job.id,
        "status": job.status,
        "tool": job.tool,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }
