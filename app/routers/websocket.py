from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.database import DBJob
import asyncio

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    try:
        client = aioredis.from_url(settings.REDIS_URL)
        pubsub = client.pubsub()
        await pubsub.subscribe(f"job:{job_id}")
        
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    status = message["data"].decode("utf-8")
                    await websocket.send_json({"job_id": job_id, "status": status})
                    if status in ("completed", "failed"):
                        break
            except asyncio.TimeoutError:
                pass
            
            try:
                # Check for client disconnect without hanging indefinitely
                await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            except WebSocketDisconnect:
                break
    except Exception:
        # Fallback to DB polling if Redis is unavailable
        while True:
            db = SessionLocal()
            try:
                job = db.query(DBJob).filter(DBJob.id == job_id).first()
                if job:
                    try:
                        await websocket.send_json({"job_id": job_id, "status": job.status})
                    except Exception:
                        break
                    if job.status in ("completed", "failed"):
                        break
                else:
                    break
            except Exception:
                break
            finally:
                db.close()
            await asyncio.sleep(2.0)
