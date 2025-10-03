from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth
from src.core.config import get_settings
from src.core.lifespan import lifespan
from src.db.session import get_async_sessionmaker

app = FastAPI(
    title="Fullstack Template API",
    description="FastAPI backend with authentication and AI integration",
    version="0.1.0",
    debug=get_settings().DEBUG,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.get("/health_check")
async def health_check(check_db: bool = False) -> dict[str, str | bool]:
    """Health check endpoint to verify API is running.

    Args:
        check_db: If True, also checks database connectivity
    """
    settings = get_settings()
    result: dict[str, str | bool] = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }

    if check_db:
        from sqlalchemy import text

        session_factory = get_async_sessionmaker()

        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
                result["database"] = "connected"
        except Exception as e:  # pragma: no cover - diagnostic only
            result["status"] = "unhealthy"
            result["database"] = "disconnected"
            result["error"] = str(e)

    return result
