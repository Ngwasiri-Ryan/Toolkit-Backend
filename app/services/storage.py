import os
import boto3
from app.core.config import settings

LOCAL_STORAGE_DIR = os.path.abspath("local_storage")
os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

def is_s3_configured() -> bool:
    return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.S3_ENDPOINT_URL or None
    )

def upload_file(file_bytes: bytes, file_name: str) -> str:
    if is_s3_configured():
        s3 = get_s3_client()
        s3.put_object(Bucket=settings.STORAGE_BUCKET, Key=file_name, Body=file_bytes)
        return f"s3://{settings.STORAGE_BUCKET}/{file_name}"
    
    # Fallback to local file persistence
    local_path = os.path.join(LOCAL_STORAGE_DIR, file_name)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    return local_path

def get_signed_url(file_name: str, expires_in: int = 3600) -> str:
    if is_s3_configured():
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.STORAGE_BUCKET, "Key": file_name},
            ExpiresIn=expires_in
        )
        return url
    
    # Fallback return absolute file path
    local_path = os.path.join(LOCAL_STORAGE_DIR, file_name)
    return f"file:///{local_path.replace(os.sep, '/')}"

def download_file(file_path: str) -> bytes:
    if is_s3_configured() and file_path.startswith("s3://"):
        s3 = get_s3_client()
        parts = file_path[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1]
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    
    clean_path = file_path
    if clean_path.startswith("file:///"):
        clean_path = clean_path[8:]
    with open(clean_path, "rb") as f:
        return f.read()
