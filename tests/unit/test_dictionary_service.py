"""Unit tests for DictionaryService."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.dictionary_service import DictionaryService
from app.repositories.paragraph_repository import ParagraphRepository


class TestDictionaryService:
    """Test cases for DictionaryService."""
    
    @pytest.mark.asyncio
    @patch('app.services.dictionary_service.httpx.AsyncClient')
    async def test_get_top_words_definitions(self, mock_client_class, db_session):
        """Test getting definitions for top words."""
        # Setup repository with test data
        repo = ParagraphRepository(db_session)
        await repo.create("The quick brown fox jumps over the lazy dog.")
        await repo.create("The quick brown fox is very quick.")
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = [{
            "word": "the",
            "phonetic": "/ðə/",
            "meanings": [{
                "definitions": [
                    {"definition": "Used to refer to a specific person or thing."}
                ]
            }]
        }]
        mock_response.raise_for_status = Mock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        service = DictionaryService(repo)
        definitions = await service.get_top_words_definitions(limit=5)
        
        assert len(definitions) > 0
        assert definitions[0].word == "the"
        assert len(definitions[0].definitions) > 0
    
    @pytest.mark.asyncio
    @patch('app.services.dictionary_service.cache')
    async def test_get_top_words_definitions_empty(self, mock_cache, db_session):
        """Test getting definitions with no paragraphs."""
        # Mock cache to be unavailable (returns False for ping)
        mock_cache.ping.return_value = False
        
        repo = ParagraphRepository(db_session)
        service = DictionaryService(repo)
        
        definitions = await service.get_top_words_definitions()
        
        assert len(definitions) == 0

