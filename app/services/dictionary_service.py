
from typing import List, Optional, Dict
import httpx
import asyncio
from app.repositories.paragraph_repository import ParagraphRepository
from app.schemas.paragraph import WordDefinition, DictionaryResponse
from app.config import settings
from app.core.cache import cache
import json
import time


class DictionaryService:
    """Service for dictionary-related operations with caching."""
    
    def __init__(self, repository: ParagraphRepository):
        self.repository = repository
    
    async def get_top_words_definitions(self, limit: int = 10) -> List[WordDefinition]:
        """
        Get definitions for top N most frequent words.
        
        Args:
            limit: Number of top words to get definitions for
            
        Returns:
            List of WordDefinition objects
        """
        # Check if Redis is available
        cache_available = cache.ping()
        
        if cache_available:
            #  Checking final result cache first 
            cache_key = f"top_words_definitions:{limit}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                return [WordDefinition(**word_data) for word_data in cached_result.get("words", [])]
            
            # Cache miss - need to calculate
            # Checking word frequencies cache
            frequencies_cache_key = "word_frequencies:all"
            cached_frequencies = cache.get(frequencies_cache_key)
            
            if cached_frequencies:
                word_frequencies = list(cached_frequencies.items())
                # Sort by frequency and take top N
                word_frequencies = sorted(word_frequencies, key=lambda x: x[1], reverse=True)[:limit]
            else:
                # Calculating from database
                word_frequencies = await self.repository.get_word_frequencies(limit)
                if word_frequencies:
                    # Cache the frequencies
                    try:
                        cache.set(
                            frequencies_cache_key,
                            dict(word_frequencies),
                            ttl=settings.cache_ttl_word_frequencies
                        )
                    except Exception:
                        pass  # Continue even if caching fails
            
            if not word_frequencies:
                return []
            
            # Get definitions (check cache for each word, fetch if missing)
            # First, separate cached and uncached words
            cached_definitions = []
            words_to_fetch = []
            
            for word, frequency in word_frequencies:
                word_cache_key = f"word_definition:{word}"
                cached_word_def = cache.get(word_cache_key)
                
                if cached_word_def:
                    cached_definitions.append(WordDefinition(**cached_word_def))
                else:
                    words_to_fetch.append((word, word_cache_key))
            
            # Fetch uncached words in parallel
            word_definitions = cached_definitions.copy()
            if words_to_fetch:
                async with httpx.AsyncClient(timeout=settings.dictionary_api_timeout) as client:
                    # Create tasks for parallel fetching
                    tasks = [
                        self._fetch_word_definition(client, word) 
                        for word, _ in words_to_fetch
                    ]
                    fetched_definitions = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results and cache them
                    for (word, word_cache_key), definition in zip(words_to_fetch, fetched_definitions):
                        if isinstance(definition, Exception) or definition is None:
                            continue
                        
                        # Cache the definition
                        try:
                                cache.set(
                                    word_cache_key,
                                    definition.model_dump(),
                                    ttl=settings.cache_ttl_word_definitions
                                )
                        except Exception:
                            pass  # Continue even if caching fails
                        
                        word_definitions.append(definition)
            
            # Updating final result cache
            if word_definitions:
                result_data = {
                    "words": [wd.model_dump() for wd in word_definitions]
                }
                try:
                    cache.set(
                        cache_key,
                        result_data,
                        ttl=settings.cache_ttl_top_words
                    )
                except Exception:
                    pass  # Continue even if caching fails
            
            return word_definitions
        else:
            word_frequencies = await self.repository.get_word_frequencies(limit)
            
            if not word_frequencies:
                return []
            
            
            word_definitions = []
            if word_frequencies:
                async with httpx.AsyncClient(timeout=settings.dictionary_api_timeout) as client:
                    # Fetch all definitions in parallel
                    tasks = [
                        self._fetch_word_definition(client, word) 
                        for word, _ in word_frequencies
                    ]
                    fetched_definitions = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Filter out None and exceptions
                    for definition in fetched_definitions:
                        if definition and not isinstance(definition, Exception):
                            word_definitions.append(definition)
            
            return word_definitions
    
    async def _fetch_word_definition(
        self, 
        client: httpx.AsyncClient, 
        word: str
    ) -> Optional[WordDefinition]:
        """
        Fetch word definition from external API.
        
        Args:
            client: HTTP client instance
            word: Word to get definition for
            
        Returns:
            WordDefinition if found, None otherwise
        """
        try:
            url = f"{settings.dictionary_api_url}/{word}"
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                definitions = []
                
                # Extracting definitions from the API response
                if "meanings" in entry:
                    for meaning in entry["meanings"]:
                        if "definitions" in meaning:
                            for def_item in meaning["definitions"]:
                                if "definition" in def_item:
                                    definitions.append(def_item["definition"])
                
                phonetic = entry.get("phonetic") or entry.get("phonetics", [{}])[0].get("text")
                
                return WordDefinition(
                    word=word,
                    definitions=definitions[:5],  # Limit to 5 definitions per word
                    phonetic=phonetic
                )
        except (httpx.HTTPError, KeyError, IndexError):
            # If word not found or API error, return None
            return None
        
        return None

