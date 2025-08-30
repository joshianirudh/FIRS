#!/usr/bin/env python3
"""
Temporary Storage for FIRS - handles temporary storage of API responses.
"""
import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class TempStorage:
    """Manages temporary storage of API responses and data."""
    
    def __init__(self, temp_dir: str = "temp", default_ttl: int = 600):
        """
        Initialize temporary storage.
        
        Args:
            temp_dir: Directory to store temporary files
            default_ttl: Default time-to-live in seconds (10 minutes)
        """
        self.temp_dir = Path(temp_dir)
        self.default_ttl = default_ttl
        self.temp_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.temp_dir / "api_responses").mkdir(exist_ok=True)
        (self.temp_dir / "reports").mkdir(exist_ok=True)
        (self.temp_dir / "embeddings").mkdir(exist_ok=True)
        
        logger.info(f"Temporary storage initialized with directory: {self.temp_dir}")
    
    def store_api_response(self, ticker: str, api_name: str, data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """
        Store API response data temporarily.
        
        Args:
            ticker: Stock ticker symbol
            api_name: Name of the API (e.g., 'alpha_vantage', 'finnhub')
            data: API response data
            ttl: Time-to-live override
            
        Returns:
            Path to stored file
        """
        try:
            ttl = ttl or self.default_ttl
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create filename with metadata
            filename = f"{ticker}_{api_name}_{timestamp}.json"
            file_path = self.temp_dir / "api_responses" / filename
            
            # Store data with metadata
            storage_data = {
                "ticker": ticker,
                "api_name": api_name,
                "timestamp": datetime.now().isoformat(),
                "ttl": ttl,
                "data": data
            }
            
            with open(file_path, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            logger.info(f"Stored API response for {ticker} from {api_name} at {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error storing API response for {ticker} from {api_name}: {e}")
            raise
    
    def get_api_response(self, ticker: str, api_name: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get stored API response if available and not expired.
        
        Args:
            ticker: Stock ticker symbol
            api_name: Name of the API
            max_age: Maximum age in seconds (overrides stored TTL)
            
        Returns:
            API response data or None if not found/expired
        """
        try:
            api_dir = self.temp_dir / "api_responses"
            
            # Find most recent file for this ticker and API
            pattern = f"{ticker}_{api_name}_*.json"
            files = list(api_dir.glob(pattern))
            
            if not files:
                logger.info(f"No stored API response found for {ticker} from {api_name}")
                return None
            
            # Get most recent file
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            
            # Check if file is expired
            if max_age is None:
                # Use stored TTL
                with open(latest_file, 'r') as f:
                    stored_data = json.load(f)
                    max_age = stored_data.get("ttl", self.default_ttl)
            
            # Check file age
            file_age = datetime.now().timestamp() - latest_file.stat().st_mtime
            if file_age > max_age:
                logger.info(f"Stored API response for {ticker} from {api_name} is expired")
                return None
            
            # Load and return data
            with open(latest_file, 'r') as f:
                stored_data = json.load(f)
                logger.info(f"Retrieved stored API response for {ticker} from {api_name}")
                return stored_data["data"]
                
        except Exception as e:
            logger.error(f"Error retrieving API response for {ticker} from {api_name}: {e}")
            return None
    
    def store_report(self, ticker: str, report_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """
        Store generated report temporarily.
        
        Args:
            ticker: Stock ticker symbol
            report_data: Generated report data
            ttl: Time-to-live override
            
        Returns:
            Path to stored file
        """
        try:
            ttl = ttl or self.default_ttl
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"report_{ticker}_{timestamp}.json"
            file_path = self.temp_dir / "reports" / filename
            
            storage_data = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "ttl": ttl,
                "report": report_data
            }
            
            with open(file_path, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            logger.info(f"Stored report for {ticker} at {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error storing report for {ticker}: {e}")
            raise
    
    def get_report(self, ticker: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get stored report if available and not expired.
        
        Args:
            ticker: Stock ticker symbol
            max_age: Maximum age in seconds
            
        Returns:
            Report data or None if not found/expired
        """
        try:
            reports_dir = self.temp_dir / "reports"
            
            # Find most recent report for this ticker
            pattern = f"report_{ticker}_*.json"
            files = list(reports_dir.glob(pattern))
            
            if not files:
                logger.info(f"No stored report found for {ticker}")
                return None
            
            # Get most recent file
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            
            # Check if file is expired
            if max_age is None:
                with open(latest_file, 'r') as f:
                    stored_data = json.load(f)
                    max_age = stored_data.get("ttl", self.default_ttl)
            
            # Check file age
            file_age = datetime.now().timestamp() - latest_file.stat().st_mtime
            if file_age > max_age:
                logger.info(f"Stored report for {ticker} is expired")
                return None
            
            # Load and return data
            with open(latest_file, 'r') as f:
                stored_data = json.load(f)
                logger.info(f"Retrieved stored report for {ticker}")
                return stored_data["report"]
                
        except Exception as e:
            logger.error(f"Error retrieving report for {ticker}: {e}")
            return None
    
    def store_embeddings(self, ticker: str, embeddings_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """
        Store embeddings data temporarily.
        
        Args:
            ticker: Stock ticker symbol
            embeddings_data: Embeddings data
            ttl: Time-to-live override
            
        Returns:
            Path to stored file
        """
        try:
            ttl = ttl or self.default_ttl
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"embeddings_{ticker}_{timestamp}.json"
            file_path = self.temp_dir / "embeddings" / filename
            
            storage_data = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "ttl": ttl,
                "embeddings": embeddings_data
            }
            
            with open(file_path, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            logger.info(f"Stored embeddings for {ticker} at {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error storing embeddings for {ticker}: {e}")
            raise
    
    def cleanup_expired_files(self) -> int:
        """Remove expired temporary files. Returns number of files removed."""
        removed_count = 0
        
        for subdir in ["api_responses", "reports", "embeddings"]:
            dir_path = self.temp_dir / subdir
            if dir_path.exists():
                for file_path in dir_path.glob("*.json"):
                    try:
                        # Check if file is expired
                        with open(file_path, 'r') as f:
                            stored_data = json.load(f)
                            ttl = stored_data.get("ttl", self.default_ttl)
                        
                        file_age = datetime.now().timestamp() - file_path.stat().st_mtime
                        if file_age > ttl:
                            file_path.unlink()
                            removed_count += 1
                            logger.info(f"Removed expired temp file: {file_path}")
                            
                    except Exception as e:
                        logger.error(f"Error checking/removing temp file {file_path}: {e}")
        
        logger.info(f"Cleanup removed {removed_count} expired temporary files")
        return removed_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get temporary storage statistics."""
        stats = {}
        
        for subdir in ["api_responses", "reports", "embeddings"]:
            dir_path = self.temp_dir / subdir
            if dir_path.exists():
                files = list(dir_path.glob("*.json"))
                stats[subdir] = {
                    "count": len(files),
                    "size_mb": sum(f.stat().st_size for f in files) / (1024 * 1024)
                }
            else:
                stats[subdir] = {"count": 0, "size_mb": 0}
        
        return stats
    
    def clear_all(self) -> bool:
        """Clear all temporary storage."""
        try:
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
            
            # Recreate subdirectories
            (self.temp_dir / "api_responses").mkdir(exist_ok=True)
            (self.temp_dir / "reports").mkdir(exist_ok=True)
            (self.temp_dir / "embeddings").mkdir(exist_ok=True)
            
            logger.info("Cleared all temporary storage")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing temporary storage: {e}")
            return False
