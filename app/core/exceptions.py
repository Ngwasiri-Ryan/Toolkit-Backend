from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class ToolKitException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

class FileTooLargeError(ToolKitException):
    def __init__(self, detail: str = "File size exceeds the allowed limit"):
        super().__init__(status_code=413, detail=detail)

class UnsupportedFormatError(ToolKitException):
    def __init__(self, detail: str = "Unsupported file format"):
        super().__init__(status_code=415, detail=detail)

class QuotaExceededError(ToolKitException):
    def __init__(self, detail: str = "Daily conversion limit exceeded"):
        super().__init__(status_code=429, detail=detail)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ToolKitException)
    async def toolkit_exception_handler(request: Request, exc: ToolKitException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
