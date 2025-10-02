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


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "src.main:app",
#         host=settings.BACKEND_HOST,
#         port=settings.BACKEND_PORT,
#         reload=settings.DEBUG,
#     )
