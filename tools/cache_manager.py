"""
Cache Manager for API responses.
Thread-safe caching with TTL (time-to-live) support.
"""

import hashlib
import json
import time
import threading
from typing import Any, Callable


class CacheManager:
    """Thread-safe cache with TTL for API responses."""
    
    def __init__(self):
        self.cache = {}  # {key: {"data": ..., "expires": ..., "created": ...}}
        self.lock = threading.Lock()
        self.ttls = {
            "weather": 1800,   # 30 minutes (weather changes slowly)
            "news": 600,       # 10 minutes (news updates frequently)
            "github": 3600     # 1 hour (GitHub data rarely changes)
        }
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate a unique cache key from function name and arguments."""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Any | None:
        """Retrieve data from cache if valid."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() < entry["expires"]:
                    self.hits += 1
                    return entry["data"]
                # Expired - remove it
                del self.cache[key]
            self.misses += 1
            return None
    
    def set(self, key: str, data: Any, ttl: int):
        """Store data in cache with TTL."""
        with self.lock:
            self.cache[key] = {
                "data": data,
                "expires": time.time() + ttl,
                "created": time.time()
            }
    
    def cache_call(self, func: Callable, tool_type: str, *args, **kwargs) -> Any:
        """
        Execute function with caching.
        
        Args:
            func: The function to cache
            tool_type: Type of tool ("weather", "news", "github")
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Function result (from cache or fresh call)
        """
        key = self._generate_key(func.__name__, *args, **kwargs)
        cached_result = self.get(key)
        
        if cached_result is not None:
            return cached_result
        
        # Cache miss - execute function
        result = func(*args, **kwargs)
        ttl = self.ttls.get(tool_type, 300)  # Default 5 minutes
        self.set(key, result, ttl)
        return result
    
    def clear(self):
        """Clear all cached data."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "size": len(self.cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "total_requests": total
            }
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time >= entry["expires"]
            ]
            for key in expired_keys:
                del self.cache[key]


# Global cache instance
cache_manager = CacheManager()
