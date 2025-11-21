from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.paragraph import DictionaryResponse
from app.services.dictionary_service import DictionaryService
from app.repositories.paragraph_repository import ParagraphRepository

router = APIRouter(tags=["dictionary"])


@router.get("/dictionary", response_model=DictionaryResponse)
async def get_dictionary(db: AsyncSession = Depends(get_db)):
    """
    Get definitions for top 10 most frequent words in stored paragraphs.
    
    Returns:
        List of word definitions
    """
    try:
        repository = ParagraphRepository(db)
        service = DictionaryService(repository)
        word_definitions = await service.get_top_words_definitions(limit=10)
        
        return DictionaryResponse(words=word_definitions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

