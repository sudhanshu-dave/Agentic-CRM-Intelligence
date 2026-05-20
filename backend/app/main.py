from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import settings
from app.core.errors import (
    AppError,
    app_error_handler,
    validation_exception_handler,
)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-powered CRM email triage and agentic operations platform.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


app.include_router(health.router)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Agentic CRM Intelligence Platform API is running.",
        "docs": "/docs",
        "health": "/health",
    }