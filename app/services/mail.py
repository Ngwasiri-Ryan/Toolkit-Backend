import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("mail")

def send_completion_email(to_email: str, job_id: str, download_url: str) -> bool:
    """
    Sends a transactional notification email when an asynchronous conversion completes.
    Uses Resend API directly via HTTP request. Falls back to console output if keys are empty.
    """
    subject = f"ToolKit Conversion Complete - Job {job_id}"
    html_content = f"""
    <h2>Your ToolKit File is Ready!</h2>
    <p>Your background task for job <strong>{job_id}</strong> has completed successfully.</p>
    <p><a href="{download_url}" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Download Processed File</a></p>
    <p>If the button doesn't work, copy and paste this link into your browser:</p>
    <p><a href="{download_url}">{download_url}</a></p>
    <br/>
    <p>Thank you for using ToolKit!</p>
    """
    
    # Offline Mock Fallback Mode
    if not settings.RESEND_API_KEY:
        logger.warning(
            f"[MOCK EMAIL SENT]\nTo: {to_email}\nSubject: {subject}\nBody: {html_content.strip()}"
        )
        print(f"[MOCK EMAIL] To: {to_email} | Job: {job_id} | Download: {download_url}")
        return True

    # Live Resend Dispatch Mode
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        response = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
        if response.status_code in (200, 201, 202):
            return True
        logger.error(f"Resend API error: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"Failed to send Resend email: {str(e)}")
        return False
