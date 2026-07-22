from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import DBJob, DBUser
from app.core.auth import get_current_user
from app.services import storage
import io
import os

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    session_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.user_id and (not current_user or current_user.id != job.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this job")
    if not job.user_id and job.session_id and job.session_id != session_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
    return {
        "job_id": job.id,
        "tool": job.tool,
        "status": job.status,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }

@router.get("/{job_id}/download")
async def download_job_result(
    job_id: str,
    session_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: DBUser | None = Depends(get_current_user)
):
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.user_id and (not current_user or current_user.id != job.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this job")
    if not job.user_id and job.session_id and job.session_id != session_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job status is {job.status}, not completed")
        
    if not job.output_path:
        raise HTTPException(status_code=404, detail="Output path not set for job")
        
    try:
        file_bytes = storage.download_file(job.output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve file: {str(e)}")
        
    filename = os.path.basename(job.output_path)
    ext = filename.split(".")[-1].lower()
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "md": "text/markdown"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
