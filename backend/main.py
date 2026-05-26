from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes import auth_router, users_router, rooms_router, qr_board_router
from services import mqtt_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    mqtt_service.start()
    yield
    mqtt_service.stop()


app = FastAPI(title="Raydot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(rooms_router)
app.include_router(qr_board_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
