from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import httpx
import json
from datetime import datetime

from app.core.database import get_db
from app.schemas.paragraph import (
    ParagraphResponse,
    SearchRequest,
    SearchResponse
)
from app.services.paragraph_service import ParagraphService
from app.tasks.dictionary_tasks import update_dictionary_cache

router = APIRouter(tags=["paragraphs"])


@router.post("/fetch", response_model=ParagraphResponse, status_code=201)
async def fetch_paragraph(db: AsyncSession = Depends(get_db)):
    """
    Fetch a paragraph from external API and store it.
    Triggers background job to update dictionary cache.
    
    Returns:
        The stored paragraph with its ID and creation timestamp
    """
    try:
        service = ParagraphService(db)
        paragraph = await service.fetch_and_store_paragraph()
        
        # Trigger background job to update dictionary cache
        try:
            update_dictionary_cache.delay(paragraph_id=paragraph.id)
        except Exception as e:
            # If Celery/Redis is down, continue - API should still work
            # will Add proper logging here for production
            pass
        
        return paragraph
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch paragraph from external API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_paragraphs(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search through stored paragraphs.
    
    Args:
        request: Search request with words and operator (and/or)
        
    Returns:
        List of matching paragraphs and total count
    """
    try:
        service = ParagraphService(db)
        paragraphs = await service.search_paragraphs(request.words, request.operator)
        
        return SearchResponse(
            paragraphs=paragraphs,
            total_count=len(paragraphs)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

