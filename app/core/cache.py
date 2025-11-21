import redis
import json
from typing import Optional, Any, Dict
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client wrapper."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
        except Exception as e:
            logger.warning(f"Redis connection issue: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            # If Redis is down or JSON parsing fails, return None
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            # Serialize value to JSON
            serialized = json.dumps(value)
            if ttl:
                # Set with expiration
                return self.client.setex(key, ttl, serialized)
            # Set without expiration
            return self.client.set(key, serialized)
        except (redis.RedisError, TypeError) as e:
            # Return False if Redis is down or value can't be serialized
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.client.delete(key))
        except redis.RedisError:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except redis.RedisError:
            return False
    
    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False
    
    def clear_all(self) -> bool:
        """Clear all keys from cache. Use with caution!"""
        try:
            return self.client.flushdb()
        except redis.RedisError:
            return False


cache = RedisCache()

