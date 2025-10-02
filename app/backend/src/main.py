from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings

app = FastAPI(
    title="Fullstack Template API",
    description="FastAPI backend with authentication and AI integration",
    version="0.1.0",
    debug=settings.DEBUG,
    openapi_url=f"/api/v1/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Fullstack Template API", "version": "0.1.0"}


@app.get("/health_check")
async def health_check(check_db: bool = False) -> dict[str, str | bool]:
    """Health check endpoint to verify API is running.

    Args:
        check_db: If True, also checks database connectivity
    """
    result: dict[str, str | bool] = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }

    if check_db:
        from sqlalchemy import text
        from src.db.session import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                result["database"] = "connected"
        except Exception as e:
            result["status"] = "unhealthy"
            result["database"] = "disconnected"
            result["error"] = str(e)

    return result


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "src.main:app",
#         host=settings.BACKEND_HOST,
#         port=settings.BACKEND_PORT,
#         reload=settings.DEBUG,
#     )
