from fastapi import APIRouter, Request
from typing import Dict
import time

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

