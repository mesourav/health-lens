from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    # Only needed when the frontend is served from a different origin.
    # In dev, Vite proxies /api to this server, so the browser stays same-origin.
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Mounted at /api to match the frontend's VITE_CHAT_API_URL=/api and the Vite proxy.
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
