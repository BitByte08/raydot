from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.rooms import router as rooms_router
from routes.qr_board import router as qr_board_router

__all__ = ["auth_router", "users_router", "rooms_router", "qr_board_router"]
