from fastapi import FastAPI, Request
from sqlalchemy import text
from app.core.database import async_engine, Base
from app.routes import health, paragraphs, dictionary
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Portcast Home Task",
    description=" REST API'S for fetching, storing, and searching paragraphs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register routers
app.include_router(health.router)
app.include_router(paragraphs.router)
app.include_router(dictionary.router)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup. Fail if database is not available."""
    try:
        # Test database connection first
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        
        # Create tables if connection successful
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(" Database connection successful. Tables created/verified.")
    except Exception as e:
        logger.error(f" Failed to connect to database: {e}")
        logger.error("Application cannot start without database connection.")
        logger.error("Please ensure PostgreSQL is running and accessible.")
        raise  
