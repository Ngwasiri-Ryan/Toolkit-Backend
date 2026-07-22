import redis
from app.core.config import settings
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.database import DBJob
from app.services import storage, document_service

def notify_job_update(job_id: str, status: str):
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.publish(f"job:{job_id}", status)
    except Exception:
        pass

@celery_app.task(name="task_remove_background")
def task_remove_background(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(DBJob).filter(DBJob.id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        db.commit()
        notify_job_update(job_id, "processing")
        
        # Fetch file and remove background
        input_bytes = storage.download_file(job.input_path)
        from rembg import remove
        output_bytes = remove(input_bytes)
        
        # Save and update job status
        file_name = f"processed_{job.id}.png"
        output_path = storage.upload_file(output_bytes, file_name)
        complete_job_and_notify(db, job, output_path)
    except Exception as e:
        db.rollback()
        job = db.query(DBJob).filter(DBJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
            notify_job_update(job_id, "failed")
    finally:
        db.close()

def complete_job_and_notify(db, job, output_path):
    job.status = "completed"
    job.output_path = output_path
    db.commit()
    notify_job_update(str(job.id), "completed")
    
    if job.user_id:
        from app.models.database import DBUser
        from app.services.mail import send_completion_email
        user = db.query(DBUser).filter(DBUser.id == job.user_id).first()
        if user and user.email:
            download_url = f"https://toolkit.dev/api/v1/jobs/{job.id}/download"
            send_completion_email(user.email, str(job.id), download_url)

@celery_app.task(name="task_convert_document")
def task_convert_document(job_id: str, target_format: str):
    db = SessionLocal()
    try:
        job = db.query(DBJob).filter(DBJob.id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        db.commit()
        notify_job_update(job_id, "processing")
        
        input_bytes = storage.download_file(job.input_path)
        
        # Determine conversion type
        fmt = target_format.lower()
        if fmt == "pdf":
            output_bytes = document_service.convert_md_to_pdf(input_bytes)
            ext = "pdf"
        elif fmt == "md":
            output_bytes = document_service.convert_docx_to_md(input_bytes)
            ext = "md"
        else:
            raise ValueError(f"Unsupported format: {target_format}")
            
        file_name = f"processed_{job.id}.{ext}"
        output_path = storage.upload_file(output_bytes, file_name)
        complete_job_and_notify(db, job, output_path)
    except Exception as e:
        db.rollback()
        job = db.query(DBJob).filter(DBJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
            notify_job_update(job_id, "failed")
    finally:
        db.close()
