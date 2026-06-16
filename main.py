# ==============================================================================
# BLUE LEARN BACKEND ENTRY POINT
# ==============================================================================
# This is a thin entry point at the root level designed to guarantee 100% backward
# compatibility with standard startup commands (e.g. uvicorn main:app).
# All business logic, DB models, routing, and agents are modularly served under app/.
# ==============================================================================

from app.main import app

# Expose app for Uvicorn
__all__ = ["app"]
