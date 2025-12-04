"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import health, incidents, sites
from backend.app.config import settings

# Create FastAPI app
app = FastAPI(
    title="CUAS OSINT Dashboard V2",
    description="AI-first drone incident tracking and operator analysis platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(incidents.router, tags=["Incidents"])
app.include_router(sites.router, tags=["Sites"])


@app.get("/")
def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "CUAS OSINT Dashboard V2 API",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }
