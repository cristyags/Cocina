from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import MenuItem, Notification, Order, OrderItem, User
from app.routers.auth import router as auth_router
from app.routers.menu import router as menu_router
from app.routers.orders import router as orders_router
from app.routers.ws import router as ws_router


app = FastAPI(title="TableFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "http://fe:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(menu_router)
app.include_router(orders_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
