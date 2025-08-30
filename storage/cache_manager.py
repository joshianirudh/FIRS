#!/usr/bin/env python3
"""
Cache Manager for FIRS - handles caching of LLM responses and API data.
"""
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of LLM responses and API data."""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 600):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (10 minutes)
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / "llm").mkdir(exist_ok=True)
        (self.cache_dir / "api").mkdir(exist_ok=True)
        (self.cache_dir / "reports").mkdir(exist_ok=True)
        
        logger.info(f"Cache manager initialized with directory: {self.cache_dir}")
    
    def _generate_cache_key(self, data: Union[str, Dict[str, Any]]) -> str:
        """Generate a cache key from data."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_type: str, key: str) -> Path:
        """Get the full path for a cache file."""
        return self.cache_dir / cache_type / f"{key}.cache"
    
    def _is_cache_valid(self, cache_path: Path, ttl: int) -> bool:
        """Check if cache is still valid based on TTL."""
        if not cache_path.exists():
            return False
        
        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age.total_seconds() < ttl
    
    def get_cached_response(self, cache_type: str, data: Union[str, Dict[str, Any]], ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get cached response if available and valid.
        
        Args:
            cache_type: Type of cache (llm, api, reports)
            data: Data to generate cache key from
            ttl: Time-to-live override
            
        Returns:
            Cached response or None if not found/invalid
        """
        try:
            cache_key = self._generate_cache_key(data)
            cache_path = self._get_cache_path(cache_type, cache_key)
            ttl = ttl or self.default_ttl
            
            if self._is_cache_valid(cache_path, ttl):
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    logger.info(f"Cache hit for {cache_type}: {cache_key}")
                    return cached_data
            else:
                logger.info(f"Cache miss for {cache_type}: {cache_key} (expired or not found)")
                return None
                
        except Exception as e:
            logger.error(f"Error reading cache for {cache_type}: {e}")
            return None
    
    def cache_response(self, cache_type: str, data: Union[str, Dict[str, Any]], response: Any) -> bool:
        """
        Cache a response.
        
        Args:
            cache_type: Type of cache (llm, api, reports)
            data: Data to generate cache key from
            response: Response to cache
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(data)
            cache_path = self._get_cache_path(cache_type, cache_key)
            
            # Create cache entry with metadata
            cache_entry = {
                "response": response,
                "cached_at": datetime.now().isoformat(),
                "cache_key": cache_key,
                "cache_type": cache_type
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_entry, f)
            
            logger.info(f"Cached response for {cache_type}: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching response for {cache_type}: {e}")
            return False
    
    def invalidate_cache(self, cache_type: str, data: Union[str, Dict[str, Any]]) -> bool:
        """Invalidate a specific cache entry."""
        try:
            cache_key = self._generate_cache_key(data)
            cache_path = self._get_cache_path(cache_type, cache_key)
            
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Invalidated cache for {cache_type}: {cache_key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {cache_type}: {e}")
            return False
    
    def clear_cache(self, cache_type: Optional[str] = None) -> bool:
        """Clear all cache or specific cache type."""
        try:
            if cache_type:
                cache_path = self.cache_dir / cache_type
                if cache_path.exists():
                    for cache_file in cache_path.glob("*.cache"):
                        cache_file.unlink()
                    logger.info(f"Cleared {cache_type} cache")
            else:
                # Clear all caches
                for cache_type_dir in ["llm", "api", "reports"]:
                    cache_path = self.cache_dir / cache_type_dir
                    if cache_path.exists():
                        for cache_file in cache_path.glob("*.cache"):
                            cache_file.unlink()
                logger.info("Cleared all caches")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {}
        
        for cache_type in ["llm", "api", "reports"]:
            cache_path = self.cache_dir / cache_type
            if cache_path.exists():
                cache_files = list(cache_path.glob("*.cache"))
                stats[cache_type] = {
                    "count": len(cache_files),
                    "size_mb": sum(f.stat().st_size for f in cache_files) / (1024 * 1024)
                }
            else:
                stats[cache_type] = {"count": 0, "size_mb": 0}
        
        return stats
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns number of files removed."""
        removed_count = 0
        
        for cache_type in ["llm", "api", "reports"]:
            cache_path = self.cache_dir / cache_type
            if cache_path.exists():
                for cache_file in cache_path.glob("*.cache"):
                    if not self._is_cache_valid(cache_file, self.default_ttl):
                        try:
                            cache_file.unlink()
                            removed_count += 1
                            logger.info(f"Removed expired cache: {cache_file}")
                        except Exception as e:
                            logger.error(f"Error removing expired cache {cache_file}: {e}")
        
        logger.info(f"Cleanup removed {removed_count} expired cache files")
        return removed_count
