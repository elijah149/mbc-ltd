from fastapi import APIRouter

from app.api import auth, users, staff, production, inventory, finance, operations, documents, notifications, audit, dashboard

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(staff.router)
api_router.include_router(production.router)
api_router.include_router(production.weighing_router)
api_router.include_router(inventory.router)
api_router.include_router(finance.router)
api_router.include_router(operations.router)
api_router.include_router(documents.router)
api_router.include_router(notifications.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
