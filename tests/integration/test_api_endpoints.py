import pytest
from unittest.mock import patch, Mock


class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    @patch('app.services.paragraph_service.httpx.AsyncClient')
    def test_fetch_endpoint(self, mock_client_class, client):
        """Test /fetch endpoint."""
        # Mock HTTP response
        from unittest.mock import AsyncMock
        mock_response = Mock()
        mock_response.text = "This is a test paragraph from the API."
        mock_response.raise_for_status = Mock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        response = client.post("/fetch")
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "content" in data
        assert "created_at" in data
        assert data["content"] == "This is a test paragraph from the API."
    
    def test_search_endpoint_or(self, client):
        """Test /search endpoint with OR operator."""
        from unittest.mock import AsyncMock
        # First, create some test paragraphs
        with patch('app.services.paragraph_service.httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.text = "This paragraph contains word one."
            mock_response.raise_for_status = Mock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            client.post("/fetch")
        
        with patch('app.services.paragraph_service.httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.text = "This paragraph contains word two."
            mock_response.raise_for_status = Mock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            client.post("/fetch")
        
        # Now test search
        search_request = {
            "words": ["one", "two"],
            "operator": "or"
        }
        
        response = client.post("/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "paragraphs" in data
        assert "total_count" in data
        assert data["total_count"] >= 1
    
    def test_search_endpoint_and(self, client):
        """Test /search endpoint with AND operator."""
        from unittest.mock import AsyncMock
        # Create a paragraph with both words
        with patch('app.services.paragraph_service.httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.text = "This paragraph contains both word one and word two."
            mock_response.raise_for_status = Mock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            client.post("/fetch")
        
        # Test search with AND
        search_request = {
            "words": ["one", "two"],
            "operator": "and"
        }
        
        response = client.post("/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "paragraphs" in data
        assert "total_count" in data
    
    def test_search_endpoint_validation(self, client):
        """Test /search endpoint validation."""
        # Test with invalid operator
        search_request = {
            "words": ["one"],
            "operator": "invalid"
        }
        
        response = client.post("/search", json=search_request)
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.dictionary_service.httpx.AsyncClient')
    def test_dictionary_endpoint(self, mock_client_class, client):
        """Test /dictionary endpoint."""
        from unittest.mock import AsyncMock
        # First, create some paragraphs
        with patch('app.services.paragraph_service.httpx.AsyncClient') as mock_client_class_fetch:
            mock_response = Mock()
            mock_response.text = "The quick brown fox jumps over the lazy dog."
            mock_response.raise_for_status = Mock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class_fetch.return_value = mock_client
            
            client.post("/fetch")
        
        # Mock dictionary API response
        mock_dict_response = Mock()
        mock_dict_response.json.return_value = [{
            "word": "the",
            "phonetic": "/ðə/",
            "meanings": [{
                "definitions": [
                    {"definition": "Used to refer to a specific person or thing."}
                ]
            }]
        }]
        mock_dict_response.raise_for_status = Mock()
        
        mock_dict_client = AsyncMock()
        mock_dict_client.__aenter__ = AsyncMock(return_value=mock_dict_client)
        mock_dict_client.__aexit__ = AsyncMock(return_value=False)
        mock_dict_client.get = AsyncMock(return_value=mock_dict_response)
        mock_client_class.return_value = mock_dict_client
        
        response = client.get("/dictionary")
        
        assert response.status_code == 200
        data = response.json()
        assert "words" in data
        assert isinstance(data["words"], list)
    
