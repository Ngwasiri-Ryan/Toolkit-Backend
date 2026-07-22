from fastapi import APIRouter, Query, Body
from fastapi.responses import JSONResponse, StreamingResponse
from app.services import utility_service, qr_service
from pydantic import BaseModel
import io

router = APIRouter(prefix="/utilities", tags=["utilities"])

class DiffRequest(BaseModel):
    text1: str
    text2: str

@router.get("/qr-generate")
async def generate_qr(text: str = Query(..., description="Text or URL to encode in QR code")):
    result = qr_service.generate_styled_qr(text)
    return StreamingResponse(io.BytesIO(result), media_type="image/png")

@router.post("/hash")
async def generate_hash(text: str = Body(...), algo: str = Query("sha256")):
    res = utility_service.hash_string(text, algo)
    return {"algorithm": algo, "hash": res, "status": "completed"}

@router.post("/diff")
async def generate_diff(req: DiffRequest):
    html_diff = utility_service.generate_diff(req.text1, req.text2)
    return JSONResponse(content={"html_diff": html_diff})

@router.post("/json-format")
async def format_json(text: str = Body(...), minify: bool = Query(False)):
    res = utility_service.format_json(text, minify)
    return {"formatted": res}

@router.post("/csv-to-json")
async def csv_to_json(csv_text: str = Body(...)):
    res = utility_service.csv_to_json(csv_text)
    return {"json": res}

@router.post("/json-to-csv")
async def json_to_csv(json_text: str = Body(...)):
    res = utility_service.json_to_csv(json_text)
    return {"csv": res}

@router.post("/base64/encode")
async def base64_encode(text: str = Body(...)):
    res = utility_service.base64_encode(text.encode("utf-8"))
    return {"encoded": res}

@router.post("/base64/decode")
async def base64_decode(text: str = Body(...)):
    res = utility_service.base64_decode(text).decode("utf-8")
    return {"decoded": res}
