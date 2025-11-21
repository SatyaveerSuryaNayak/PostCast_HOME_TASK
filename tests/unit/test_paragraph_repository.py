"""Unit tests for ParagraphRepository."""
import pytest
from app.repositories.paragraph_repository import ParagraphRepository
from app.models.paragraph import Paragraph


class TestParagraphRepository:
    """Test cases for ParagraphRepository."""
    
    @pytest.mark.asyncio
    async def test_create_paragraph(self, db_session):
        """Test creating a paragraph."""
        repo = ParagraphRepository(db_session)
        content = "This is a test paragraph."
        
        paragraph = await repo.create(content)
        
        assert paragraph.id is not None
        assert paragraph.content == content
        assert paragraph.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session):
        """Test retrieving a paragraph by ID."""
        repo = ParagraphRepository(db_session)
        content = "Test paragraph for retrieval."
        
        created = await repo.create(content)
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == content
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """Test retrieving a non-existent paragraph."""
        repo = ParagraphRepository(db_session)
        result = await repo.get_by_id(999)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_or_operator(self, db_session):
        """Test search with OR operator."""
        repo = ParagraphRepository(db_session)
        
        # Create test paragraphs
        await repo.create("This paragraph contains word one.")
        await repo.create("This paragraph contains word two.")
        await repo.create("This paragraph contains word three.")
        await repo.create("This paragraph has no matching words.")
        
        results = await repo.search(["one", "two"], "or")
        
        assert len(results) == 2
        assert any("one" in p.content.lower() for p in results)
        assert any("two" in p.content.lower() for p in results)
    
    @pytest.mark.asyncio
    async def test_search_and_operator(self, db_session):
        """Test search with AND operator."""
        repo = ParagraphRepository(db_session)
        
        # Create test paragraphs
        await repo.create("This paragraph contains word one and two.")
        await repo.create("This paragraph contains only one.")
        await repo.create("This paragraph contains only two.")
        
        results = await repo.search(["one", "two"], "and")
        
        assert len(results) == 1
        assert "one" in results[0].content.lower()
        assert "two" in results[0].content.lower()
    
    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, db_session):
        """Test that search is case-insensitive."""
        repo = ParagraphRepository(db_session)
        
        await repo.create("This paragraph contains WORD ONE.")
        
        results = await repo.search(["word", "one"], "or")
        
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_search_whole_word_matching(self, db_session):
        """Test that search matches whole words only, not substrings."""
        repo = ParagraphRepository(db_session)
        
        # Create paragraphs with words that contain the search term as substring
        await repo.create("This paragraph contains the word one.")
        await repo.create("This paragraph contains none of the words.")
        await repo.create("This paragraph contains someone else.")
        await repo.create("This paragraph contains phone number.")
        
        # Search for "one" should only match the first paragraph, not "none", "someone", or "phone"
        results = await repo.search(["one"], "or")
        
        assert len(results) == 1
        assert "one" in results[0].content.lower()
        assert "none" not in results[0].content.lower()
        assert "someone" not in results[0].content.lower()
        assert "phone" not in results[0].content.lower()
    
    @pytest.mark.asyncio
    async def test_get_all(self, db_session):
        """Test retrieving all paragraphs."""
        repo = ParagraphRepository(db_session)
        
        await repo.create("First paragraph.")
        await repo.create("Second paragraph.")
        await repo.create("Third paragraph.")
        
        all_paragraphs = await repo.get_all()
        
        assert len(all_paragraphs) == 3
    
    @pytest.mark.asyncio
    async def test_get_word_frequencies(self, db_session):
        """Test getting word frequencies."""
        repo = ParagraphRepository(db_session)
        
        await repo.create("The quick brown fox jumps over the lazy dog.")
        await repo.create("The quick brown fox is very quick.")
        
        frequencies = await repo.get_word_frequencies(limit=5)
        
        assert len(frequencies) > 0
        # 'the' should be most frequent
        assert frequencies[0][0] == "the"
        assert frequencies[0][1] >= 2
    
    @pytest.mark.asyncio
    async def test_get_word_frequencies_empty(self, db_session):
        """Test word frequencies with no paragraphs."""
        repo = ParagraphRepository(db_session)
        
        frequencies = await repo.get_word_frequencies()
        
        assert len(frequencies) == 0

