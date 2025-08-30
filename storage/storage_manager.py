#!/usr/bin/env python3
"""
Storage Manager for FIRS - orchestrates caching, temporary storage, and vector database operations.
"""
import json
import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from .cache_manager import CacheManager
from .temp_storage import TempStorage
from .vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class StorageManager:
    """Main storage manager that coordinates all storage operations."""
    
    def __init__(self, 
                 cache_dir: str = "cache",
                 temp_dir: str = "temp",
                 qdrant_url: str = "http://localhost:6333",
                 enable_vector_storage: bool = True):
        """
        Initialize storage manager.
        
        Args:
            cache_dir: Directory for cache files
            temp_dir: Directory for temporary files
            qdrant_url: Qdrant server URL
            enable_vector_storage: Whether to enable vector database operations
        """
        self.cache_manager = CacheManager(cache_dir)
        self.temp_storage = TempStorage(temp_dir)
        self.enable_vector_storage = enable_vector_storage
        
        if enable_vector_storage:
            self.vector_db = VectorDatabase(qdrant_url)
        else:
            self.vector_db = None
        
        logger.info("Storage manager initialized")
    
    async def initialize(self) -> bool:
        """Initialize all storage components."""
        try:
            # Test vector database connection if enabled
            if self.enable_vector_storage and self.vector_db:
                if not await self.vector_db.test_connection():
                    logger.warning("Vector database connection failed, disabling vector storage")
                    self.enable_vector_storage = False
                    self.vector_db = None
                else:
                    # Create collection if it doesn't exist
                    await self.vector_db.create_collection()
            
            logger.info("Storage manager initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Storage manager initialization failed: {e}")
            return False
    
    # Cache Management Methods
    
    def get_cached_llm_response(self, prompt: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Get cached LLM response if available."""
        return self.cache_manager.get_cached_response("llm", prompt, ttl)
    
    def cache_llm_response(self, prompt: str, response: Any) -> bool:
        """Cache LLM response."""
        return self.cache_manager.cache_response("llm", prompt, response)
    
    def get_cached_api_response(self, api_name: str, params: Dict[str, Any], ttl: Optional[int] = None) -> Optional[Any]:
        """Get cached API response if available."""
        cache_key = {"api": api_name, "params": params}
        return self.cache_manager.get_cached_response("api", cache_key, ttl)
    
    def cache_api_response(self, api_name: str, params: Dict[str, Any], response: Any) -> bool:
        """Cache API response."""
        cache_key = {"api": api_name, "params": params}
        return self.cache_manager.cache_response("api", cache_key, response)
    
    def get_cached_report(self, ticker: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Get cached report if available."""
        return self.cache_manager.get_cached_response("reports", {"ticker": ticker}, ttl)
    
    def cache_report(self, ticker: str, report: Any) -> bool:
        """Cache generated report."""
        return self.cache_manager.cache_response("reports", {"ticker": ticker}, report)
    
    # Temporary Storage Methods
    
    def store_api_response_temp(self, ticker: str, api_name: str, data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """Store API response in temporary storage."""
        return self.temp_storage.store_api_response(ticker, api_name, data, ttl)
    
    def get_api_response_temp(self, ticker: str, api_name: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get API response from temporary storage."""
        return self.temp_storage.get_api_response(ticker, api_name, max_age)
    
    def store_report_temp(self, ticker: str, report_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """Store report in temporary storage."""
        return self.temp_storage.store_report(ticker, report_data, ttl)
    
    def get_report_temp(self, ticker: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get report from temporary storage."""
        return self.temp_storage.get_report(ticker, max_age)
    
    # Vector Database Methods
    
    async def store_financial_data(self, ticker: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store financial data in vector database."""
        if not self.enable_vector_storage or not self.vector_db:
            logger.warning("Vector storage disabled, skipping storage")
            return False
        
        return await self.vector_db.store_document(ticker, "financial_data", data, metadata)
    
    async def store_news_data(self, ticker: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store news data in vector database."""
        if not self.enable_vector_storage or not self.vector_db:
            logger.warning("Vector storage disabled, skipping storage")
            return False
        
        return await self.vector_db.store_document(ticker, "news", data, metadata)
    
    async def store_report_data(self, ticker: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store report data in vector database."""
        if not self.enable_vector_storage or not self.vector_db:
            logger.warning("Vector storage disabled, skipping storage")
            return False
        
        return await self.vector_db.store_document(ticker, "report", data, metadata)
    
    async def search_similar_documents(self, 
                                     query: str, 
                                     ticker: Optional[str] = None, 
                                     document_type: Optional[str] = None,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents in vector database."""
        if not self.enable_vector_storage or not self.vector_db:
            logger.warning("Vector storage disabled, returning empty results")
            return []
        
        return await self.vector_db.search_similar(query, ticker, document_type, limit)
    
    # Smart Data Retrieval with Fallback
    
    async def get_or_fetch_data(self, 
                               ticker: str, 
                               api_name: str, 
                               fetch_func, 
                               force_refresh: bool = False,
                               cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Smart data retrieval with caching and fallback.
        
        Args:
            ticker: Stock ticker symbol
            api_name: Name of the API
            fetch_func: Function to fetch data if not cached
            force_refresh: Force refresh ignoring cache
            cache_ttl: Cache TTL override
            
        Returns:
            Data from cache or fresh fetch
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self.get_cached_api_response(api_name, {"ticker": ticker}, cache_ttl)
            if cached_data:
                logger.info(f"Using cached {api_name} data for {ticker}")
                return cached_data
        
        # Check temporary storage
        temp_data = self.get_api_response_temp(ticker, api_name, cache_ttl)
        if temp_data and not force_refresh:
            logger.info(f"Using temporary {api_name} data for {ticker}")
            # Cache it for future use
            self.cache_api_response(api_name, {"ticker": ticker}, temp_data)
            return temp_data
        
        # Fetch fresh data
        logger.info(f"Fetching fresh {api_name} data for {ticker}")
        try:
            fresh_data = await fetch_func(ticker)
            
            # Store in both cache and temporary storage
            self.cache_api_response(api_name, {"ticker": ticker}, fresh_data)
            self.store_api_response_temp(ticker, api_name, fresh_data, cache_ttl)
            
            # Store in vector database if enabled
            if self.enable_vector_storage:
                await self.store_financial_data(ticker, fresh_data, {"source": api_name})
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"Failed to fetch {api_name} data for {ticker}: {e}")
            
            # Return cached data if available (even if expired)
            if temp_data:
                logger.info(f"Returning expired temporary data for {ticker}")
                return temp_data
            
            # Return empty data structure
            return {"error": f"Failed to fetch data: {str(e)}", "ticker": ticker}
    
    async def get_or_generate_report(self, 
                                   ticker: str, 
                                   generate_func, 
                                   force_refresh: bool = False,
                                   cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Smart report retrieval with caching and fallback.
        
        Args:
            ticker: Stock ticker symbol
            generate_func: Function to generate report if not cached
            force_refresh: Force refresh ignoring cache
            cache_ttl: Cache TTL override
            
        Returns:
            Report from cache or fresh generation
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_report = self.get_cached_report(ticker, cache_ttl)
            if cached_report:
                logger.info(f"Using cached report for {ticker}")
                return cached_report
        
        # Check temporary storage
        temp_report = self.get_report_temp(ticker, cache_ttl)
        if temp_report and not force_refresh:
            logger.info(f"Using temporary report for {ticker}")
            # Cache it for future use
            self.cache_report(ticker, temp_report)
            return temp_report
        
        # Generate fresh report
        logger.info(f"Generating fresh report for {ticker}")
        try:
            fresh_report = await generate_func(ticker)
            
            # Store in both cache and temporary storage
            self.cache_report(ticker, fresh_report)
            self.store_report_temp(ticker, fresh_report, cache_ttl)
            
            # Store in vector database if enabled
            if self.enable_vector_storage:
                # Store the complete report
                await self.store_report_data(ticker, fresh_report)
                
                # Also store individual components for better searchability
                if "financial_summary" in fresh_report:
                    await self.store_financial_data(ticker, fresh_report["financial_summary"], {"source": "comprehensive_report"})
                
                if "web_data" in fresh_report:
                    await self.store_news_data(ticker, fresh_report["web_data"], {"source": "comprehensive_report"})
            
            return fresh_report
            
        except Exception as e:
            logger.error(f"Failed to generate report for {ticker}: {e}")
            
            # Return cached report if available (even if expired)
            if temp_report:
                logger.info(f"Returning expired temporary report for {ticker}")
                return temp_report
            
            # Return error structure
            return {"error": f"Failed to generate report: {str(e)}", "ticker": ticker}
    
    # Utility Methods
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics."""
        stats = {
            "cache": self.cache_manager.get_cache_stats(),
            "temp_storage": self.temp_storage.get_storage_stats(),
            "vector_storage_enabled": self.enable_vector_storage
        }
        
        if self.enable_vector_storage and self.vector_db:
            # This would need to be async, so we'll just note it's enabled
            stats["vector_db"] = {"status": "enabled", "url": self.vector_db.qdrant_url}
        else:
            stats["vector_db"] = {"status": "disabled"}
        
        return stats
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data from all storage systems."""
        cleanup_stats = {
            "cache_files_removed": self.cache_manager.cleanup_expired_cache(),
            "temp_files_removed": self.temp_storage.cleanup_expired_files()
        }
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def clear_all_storage(self) -> bool:
        """Clear all storage (cache and temporary files)."""
        try:
            cache_cleared = self.cache_manager.clear_cache()
            temp_cleared = self.temp_storage.clear_all()
            
            if cache_cleared and temp_cleared:
                logger.info("All storage cleared successfully")
                return True
            else:
                logger.warning("⚠️  Some storage clearing operations failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error clearing storage: {e}")
            return False
    
    async def search_financial_knowledge(self, 
                                       query: str, 
                                       ticker: Optional[str] = None,
                                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search across all stored financial knowledge.
        
        Args:
            query: Search query
            ticker: Optional ticker filter
            limit: Maximum results
            
        Returns:
            List of relevant documents
        """
        if not self.enable_vector_storage or not self.vector_db:
            logger.warning("Vector storage disabled, cannot search")
            return []
        
        return await self.vector_db.search_similar(query, ticker, None, limit)
