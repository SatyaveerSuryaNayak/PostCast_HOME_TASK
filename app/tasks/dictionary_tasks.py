import httpx
import asyncio
from typing import List, Optional
from app.core.celery_app import celery_app
from app.core.cache import cache
from app.core.database import AsyncSessionLocal
from app.config import settings
from app.schemas.paragraph import WordDefinition
from app.repositories.paragraph_repository import ParagraphRepository
import json
import time


@celery_app.task(name="update_dictionary_cache", bind=True, max_retries=3)
def update_dictionary_cache(self, paragraph_id: int = None):
    """
    Background task to update dictionary cache after new paragraph is added.
    
    Args:
        paragraph_id: ID of the newly added paragraph (optional, for logging)
    """
    try:
        # Run async function in new event loop (Celery workers are separate processes)
        return asyncio.run(_update_cache_async(paragraph_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


async def _update_cache_async(paragraph_id: int = None):
    """Async function to update dictionary cache."""
    async with AsyncSessionLocal() as db:
        try:
            repository = ParagraphRepository(db)
            
            # Recalculating word frequencies from all paragraphs
            word_frequencies = await repository.get_word_frequencies(limit=10)
            
            if not word_frequencies:
                # No paragraphs yet, clear cache
                cache.delete("top_words_definitions:10")
                cache.delete("word_frequencies:all")
                return {"status": "success", "message": "No paragraphs to process"}
            
            # Updating Level 1 cache (word frequencies)
            frequencies_dict = dict(word_frequencies)
            cache.set(
                "word_frequencies:all",
                frequencies_dict,
                ttl=settings.cache_ttl_word_frequencies
            )
            
            # Getting top words
            top_words = [word for word, _ in word_frequencies]
            
            # Fetching definitions for words in parallel
            word_definitions = []
            
            # Separate cached and uncached words
            cached_definitions = []
            words_to_fetch = []
            
            for word in top_words:
                cache_key = f"word_definition:{word}"
                cached_definition = cache.get(cache_key)
                
                if cached_definition:
                    cached_definitions.append(WordDefinition(**cached_definition))
                else:
                    words_to_fetch.append((word, cache_key))
            
            # Fetch uncached words in parallel
            word_definitions = cached_definitions.copy()
            if words_to_fetch:
                async with httpx.AsyncClient(timeout=settings.dictionary_api_timeout) as client:
                    # Create tasks for parallel fetching
                    tasks = [
                        _fetch_word_definition_async(client, word) 
                        for word, _ in words_to_fetch
                    ]
                    fetched_definitions = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results and cache them
                    for (word, cache_key), definition in zip(words_to_fetch, fetched_definitions):
                        if isinstance(definition, Exception) or definition is None:
                            continue
                        
                        try:
                            cache.set(
                                cache_key,
                                definition.model_dump(),
                                ttl=settings.cache_ttl_word_definitions
                            )
                        except Exception:
                            pass  # Continue even if caching fails
                        
                        word_definitions.append(definition)
            
            # Update Level 3 cache (final result)
            if word_definitions:
                result_dict = {
                    "words": [wd.model_dump() for wd in word_definitions]
                }
                cache.set(
                    "top_words_definitions:10",
                    result_dict,
                    ttl=settings.cache_ttl_top_words
                )
            
            return {
                "status": "success",
                "words_processed": len(word_definitions),
                "paragraph_id": paragraph_id
            }
        except Exception as e:
            raise


async def _fetch_word_definition_async(client: httpx.AsyncClient, word: str) -> Optional[WordDefinition]:
    """
    Fetch word definition from external API (async).
    
    Args:
        client: Async HTTP client instance
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
            
            # Extract definitions from the API response
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

