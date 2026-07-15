import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base, run_migrations
from app.api.router import api_router
from app.logger import logger, _file_handler

# Attach the rotating file handler to uvicorn's loggers so server
# access/error logs also land in logs/blue_learn.log
import logging
for _uv_logger in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    logging.getLogger(_uv_logger).addHandler(_file_handler)

# Initialize database migrations and schema checks prior to app booting
run_migrations()
Base.metadata.create_all(bind=engine)

# Create core FastAPI application instance
app = FastAPI(
    title="Blue Learn API",
    description="Modularized, standard, and highly structured dynamic learning backend.",
    version="2.0.0"
)

# Configure CORS Cross-Origin settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the combined master API router
app.include_router(api_router)

# Serve static web resources
os.makedirs("static", exist_ok=True)
app.mount("/assets", StaticFiles(directory="static"), name="assets")

# Catch-all endpoint to serve the single-page application (React frontend)
@app.get("/{full_path:path}", include_in_schema=False)
def serve_react_app(full_path: str):
    """
    Serves index.html for all non-matching paths, allowing the frontend
    single-page application router to handle page views.
    """
    index_file = "static/index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        # Graceful return if index.html is missing
        return {"status": "success", "message": "Backend API is online. Frontend resources not found."}

@app.on_event("startup")
def startup_event():
    import asyncio
    from app.services.profile_service import nightly_profile_updater
    asyncio.create_task(nightly_profile_updater())
