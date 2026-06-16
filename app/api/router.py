from fastapi import APIRouter
from app.api.endpoints import settings, courses, items, chat, profile, auth

# Master API Router
api_router = APIRouter()

# Include sub-routers.
# Since all sub-routers map their endpoints absolutely, we mount them without prefixes.
# This prevents prefix conflicts and guarantees 100% route alignment.
api_router.include_router(auth.router)
api_router.include_router(settings.router)
api_router.include_router(courses.router)
api_router.include_router(items.router)
api_router.include_router(chat.router)
api_router.include_router(profile.router)
