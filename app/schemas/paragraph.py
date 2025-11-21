"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict
from datetime import datetime
import json


class ParagraphResponse(BaseModel):
    """Response schema for a paragraph."""
    id: int
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Request schema for search endpoint."""
    words: List[str] = Field(..., min_length=1, description="List of words to search for")
    operator: Literal["and", "or"] = Field(..., description="Search operator: 'and' or 'or'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "words": ["one", "two", "three"],
                "operator": "or"
            }
        }


class SearchResponse(BaseModel):
    """Response schema for search endpoint."""
    paragraphs: List[ParagraphResponse]
    total_count: int


class WordDefinition(BaseModel):
    """Schema for word definition."""
    word: str
    definitions: List[str]
    phonetic: Optional[str] = None


class DictionaryResponse(BaseModel):
    """Response schema for dictionary endpoint."""
    words: List[WordDefinition]

