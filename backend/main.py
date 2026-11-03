import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="SiteDesk Core API",
    description="AI-Assisted Trade Counter Engine for Company A (DK/NO/SE)",
    version="1.0.0"
)

# CORS setup for Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str

@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to SiteDesk Core API",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["General"])
def health_check():
    db_status = "connected" if os.getenv("DATABASE_URL") else "not_configured"
    return {
        "status": "healthy",
        "service": "SiteDesk FastAPI Backend",
        "database": db_status
    }
