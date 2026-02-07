from fastapi import FastAPI

from app.db.session import engine, SessionLocal
from app.db.base import Base

from app.db.init_db import ensure_admin
from app.routers.auth import router as auth_router
from app.routers.reservations import router as reservations_router
from app.routers.cinema import router as cinema_router
from app.routers.availability import router as availability_router
from app.routers.reviews import router as reviews_router
from app.routers.favorites import router as favorites_router
from app.routers.admin_tools import router as admin_tools_router
from app.routers.admin import router as admin_router
from app.routers.users import router as users_router
from app.routers.provider_reservations import router as provider_reservations_router


app = FastAPI(title="Cinema Reservations API")

Base.metadata.create_all(bind=engine)

# seed admin
with SessionLocal() as db:
    ensure_admin(db)

app.include_router(auth_router)
app.include_router(cinema_router)
app.include_router(availability_router)
app.include_router(reservations_router)
app.include_router(reviews_router)
app.include_router(favorites_router)
app.include_router(admin_tools_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(provider_reservations_router)

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
