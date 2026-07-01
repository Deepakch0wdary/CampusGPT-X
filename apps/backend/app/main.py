from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import register_error_handlers
from app.api.v1.router import api_router

# Initialize logging configuration
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CampusGPT X - AI-Powered Smart Campus Operating System Foundation",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS Policy Config
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Exception mapping configuration
register_error_handlers(app)

# Include sub-routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    """Welcome endpoint pointing developers to API documentation."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API.",
        "docs_url": "/docs",
        "version": "1.0.0"
    }
