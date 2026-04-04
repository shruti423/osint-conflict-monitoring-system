import time
from typing import Optional, Any

class TTLCache:
    """
    A simple Time-To-Live (TTL) in-memory cache.
    Prevents the backend from spamming external APIs on concurrent requests.
    """
    def __init__(self, ttl_seconds: int = 120):
        self.ttl_seconds = ttl_seconds
        self.cache_store = {}

    def get(self, key: str) -> Optional[Any]:
        """Returns the cached data if it exists and is still fresh. Otherwise, returns None."""
        if key in self.cache_store:
            item = self.cache_store[key]
            # Check if the current time minus the saved time is within our TTL window
            if time.time() - item['timestamp'] < self.ttl_seconds:
                print(f"⚡ CACHE HIT for '{key}'")
                return item['data']
            else:
                print(f"♻️ CACHE EXPIRED for '{key}'")
                del self.cache_store[key]
        
        print(f"🔍 CACHE MISS for '{key}'")
        return None

    def set(self, key: str, data: Any):
        """Saves data to the cache with the current timestamp."""
        self.cache_store[key] = {
            'data': data,
            'timestamp': time.time()
        }
        print(f"💾 CACHE SAVED for '{key}'")

# Instantiate a global cache object that our FastAPI routes will use
# Setting TTL to 120 seconds (2 minutes) for real-time OSINT feel
dashboard_cache = TTLCache(ttl_seconds=120)