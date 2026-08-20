from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware  # <-- 1. Import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, engine, get_db
from app.routers import items, users, categories, persons, auth
import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they do not exist (useful for development)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
        
    # Shutdown: Cleanly close connection pool
    await engine.dispose()

app = FastAPI(
    title="Dental Management API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all frontend origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Mount Routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(persons.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint that verifies API uptime and active DB connectivity.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unavailable: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
    }