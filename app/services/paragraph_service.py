
from typing import List, Optional, Dict
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.paragraph_repository import ParagraphRepository
from app.models.paragraph import Paragraph
from app.config import settings
import time
import json
from datetime import datetime


class ParagraphService:
    """Service for paragraph-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.repository = ParagraphRepository(db)
    
    async def fetch_and_store_paragraph(self) -> Paragraph:
        """
        Fetch a paragraph from external API and store it.
        
        Returns:
            The stored paragraph
            
        Raises:
            httpx.HTTPError: If the external API request fails
        """
        # Fetching paragraph from external API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.metaphorpsum_url)
            response.raise_for_status()
            content = response.text.strip()
        
        # Save to database
        return await self.repository.create(content)
    
    async def search_paragraphs(self, words: List[str], operator: str) -> List[Paragraph]:
        """
        Search paragraphs by words with AND or OR operator.
        
        Args:
            words: List of words to search for
            operator: 'and' or 'or' operator
            
        Returns:
            List of matching paragraphs
        """
        return await self.repository.search(words, operator)

