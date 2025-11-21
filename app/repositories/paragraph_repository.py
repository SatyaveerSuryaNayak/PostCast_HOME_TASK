from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, select, func, text
from typing import List, Optional
from app.models.paragraph import Paragraph
import re


class ParagraphRepository:
    """Repository for paragraph database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, content: str) -> Paragraph:
        """Create and store a new paragraph."""
        paragraph = Paragraph(content=content)
        self.db.add(paragraph)
        await self.db.commit()
        await self.db.refresh(paragraph)
        return paragraph
    
    async def get_by_id(self, paragraph_id: int) -> Optional[Paragraph]:
        """Get a paragraph by its ID."""
        result = await self.db.execute(
            select(Paragraph).filter(Paragraph.id == paragraph_id)
        )
        return result.scalar_one_or_none()
    
    async def search(self, words: List[str], operator: str) -> List[Paragraph]:
        """
        Search paragraphs by words with AND or OR operator.
        
        Args:
            words: List of words to search for
            operator: 'and' or 'or' operator
            
        Returns:
            List of matching paragraphs
        """
        if not words:
            return []
        
        # Sanitize words  input: removing special characters that could break regex
        # Keeping only alphanumeric characters and basic word characters
        sanitized_words = []
        for word in words:
            if not word:
                continue
            # Remove backslashes and other problematic characters
            # Keep only letters, numbers, and basic punctuation that are part of words
            sanitized = re.sub(r'[\\\/\*\?\[\]\(\)\{\}\+\|\.\^]', '', word.strip())
            if sanitized:  # Only add if word is not empty after sanitization
                sanitized_words.append(sanitized)
        
        if not sanitized_words:
            return []
        
        # Check database dialect
        try:
            dialect_name = self.db.bind.dialect.name if hasattr(self.db, 'bind') and self.db.bind else None
        except:
            dialect_name = None
        
        if dialect_name == 'postgresql':
            # PostgreSQL: Use regex with word boundaries for database-level filtering (scalable)
            # This filters at database level, so we don't load all paragraphs
            search_words_lower = [w.lower() for w in sanitized_words]
            conditions = []
            
            for word in search_words_lower:
                escaped_word = re.escape(word)
                # Use PostgreSQL regex with word boundaries (\y) for exact word matching
                # ~* is case-insensitive regex match operator
                condition = Paragraph.content.op('~*')(f'\\y{escaped_word}\\y')
                conditions.append(condition)
            
            if operator.lower() == "and":
                stmt = select(Paragraph).filter(and_(*conditions))
            else:
                stmt = select(Paragraph).filter(or_(*conditions))
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        else:
            # SQLite (tests): Fallback to Python-side filtering
            all_paragraphs = await self.get_all()
            search_words_lower = [w.lower() for w in sanitized_words]
            matching_paragraphs = []
            
            for paragraph in all_paragraphs:
                paragraph_words = self._extract_words(paragraph.content)
                
                if operator.lower() == "and":
                    if all(word in paragraph_words for word in search_words_lower):
                        matching_paragraphs.append(paragraph)
                else:
                    if any(word in paragraph_words for word in search_words_lower):
                        matching_paragraphs.append(paragraph)
            
            return matching_paragraphs
    
    async def get_all(self) -> List[Paragraph]:
        """Get all stored paragraphs."""
        result = await self.db.execute(select(Paragraph))
        return list(result.scalars().all())
    
    async def get_word_frequencies(self, limit: int = 10) -> List[tuple]:
        """
        Get top N most frequent words across all paragraphs.
        
        Args:
            limit: Number of top words to return
            
        Returns:
            List of tuples (word, frequency) sorted by frequency descending
        """
        # Get all paragraphs
        paragraphs = await self.get_all()
        
        if not paragraphs:
            return []
        
        word_count = {}
        for paragraph in paragraphs:
            words = self._extract_words(paragraph.content)
            for word in words:
                if len(word) > 2:  # Filter out very short words
                    word_count[word] = word_count.get(word, 0) + 1
        
        # Sort by frequency and return top N
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:limit]
    
    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Extract words from text, removing punctuation."""
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words

