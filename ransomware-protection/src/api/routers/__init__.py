from fastapi import APIRouter
from src.api.routers import auth, alerts, hosts, events, dashboard, ml

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(hosts.router, prefix="/hosts", tags=["Hosts"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(ml.router, prefix="/ml", tags=["ML Models"])
