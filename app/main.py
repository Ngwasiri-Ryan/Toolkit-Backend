from fastapi import FastAPI
from app.core.config import settings
from app.core.middleware import setup_middlewares
from app.core.exceptions import register_exception_handlers
from app.db.init_db import init_db
from app.routers import general, documents, images, utilities, auth, jobs, websocket, billing

def create_app() -> FastAPI:
    # Initialize DB tables
    init_db()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc"
    )
    
    # Configure Middleware and Exceptions
    setup_middlewares(app)
    register_exception_handlers(app)
    
    # Include API Routers
    app.include_router(general.router, prefix=settings.API_V1_STR)
    app.include_router(auth.router, prefix=settings.API_V1_STR)
    app.include_router(documents.router, prefix=settings.API_V1_STR)
    app.include_router(images.router, prefix=settings.API_V1_STR)
    app.include_router(utilities.router, prefix=settings.API_V1_STR)
    app.include_router(jobs.router, prefix=settings.API_V1_STR)
    app.include_router(billing.router, prefix=settings.API_V1_STR)
    app.include_router(websocket.router)
    
    return app

app = create_app()
