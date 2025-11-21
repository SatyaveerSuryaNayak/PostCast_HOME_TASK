"""Unit tests for ParagraphService."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.paragraph_service import ParagraphService
from app.models.paragraph import Paragraph


class TestParagraphService:
    """Test cases for ParagraphService."""
    
    @pytest.mark.asyncio
    @patch('app.services.paragraph_service.httpx.AsyncClient')
    async def test_fetch_and_store_paragraph(self, mock_client_class, db_session):
        """Test fetching and storing a paragraph."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "This is a fetched paragraph."
        mock_response.raise_for_status = Mock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        service = ParagraphService(db_session)
        paragraph = await service.fetch_and_store_paragraph()
        
        assert paragraph.id is not None
        assert paragraph.content == "This is a fetched paragraph."
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_paragraphs(self, db_session):
        """Test searching paragraphs."""
        service = ParagraphService(db_session)
        
        # Create test data
        await service.repository.create("This contains word one.")
        await service.repository.create("This contains word two.")
        await service.repository.create("This contains both one and two.")
        
        # Test OR operator
        results = await service.search_paragraphs(["one", "two"], "or")
        assert len(results) == 3
        
        # Test AND operator
        results = await service.search_paragraphs(["one", "two"], "and")
        assert len(results) == 1

