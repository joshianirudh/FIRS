#!/usr/bin/env python3
"""
Main entry point for the Financial Intelligence System.
Generates comprehensive financial reports and stores them in Qdrant.

Usage:
    python main.py                    # Generate report for AAPL
    python main.py TSLA              # Generate report for TSLA
    python main.py --force AAPL      # Force refresh ignoring cache
"""
import asyncio
import json
import logging
import sys
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from preprocessing.create_report import FinancialReportGenerator
from storage.storage_manager import StorageManager
from config import config


# Configure logging
logging.basicConfig(
    level=getattr(logging, config["system"]["log_level"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_comprehensive_report_with_storage(ticker: str, storage_manager: StorageManager, force_refresh: bool = False) -> Dict[str, Any]:
    """Generate comprehensive report using storage manager for caching and vector storage."""
    try:
        # Check if we have a cached report
        if not force_refresh:
            cached_report = storage_manager.get_cached_report(ticker)
            if cached_report:
                logger.info(f"Using cached report for {ticker}")
                return cached_report
        
        # Generate fresh comprehensive report with real data
        logger.info(f"Generating comprehensive report for {ticker}")
        report_generator = FinancialReportGenerator()
        await report_generator.initialize()
        
        # Generate the full report with data from all sources
        report = await report_generator.generate_financial_report(ticker)
        
        # Check if report generation was successful
        if "error" in report:
            logger.error(f"Report generation failed: {report['error']}")
            return report
        
        # Cache the complete report
        storage_manager.cache_report(ticker, report)
        
        # Store the complete report in vector database
        if storage_manager.enable_vector_storage:
            await storage_manager.store_report_data(ticker, report)
            logger.info(f"Complete report stored in vector database for {ticker}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating report with storage: {e}")
        return {"error": str(e), "ticker": ticker}


async def main():
    """Main entry point."""
    print("Financial Intelligence System - Report Generation")
    print("=" * 50)
    
    # Parse command line arguments
    force_refresh = False
    ticker = "AAPL"  # Default to Apple
    
    if len(sys.argv) > 1:
        # Check for --force flag
        if "--force" in sys.argv:
            force_refresh = True
            sys.argv.remove("--force")
        
        # Get ticker from remaining arguments
        if len(sys.argv) > 1:
            ticker = sys.argv[1].upper()
    
    # Initialize storage manager
    storage_manager = StorageManager()
    await storage_manager.initialize()
    
    # Display storage status
    storage_stats = storage_manager.get_storage_stats()
    print(f"\nSTORAGE STATUS")
    print("-" * 20)
    print(f"Cache: {storage_stats['cache']['llm']['count']} LLM, {storage_stats['cache']['api']['count']} API, {storage_stats['cache']['reports']['count']} Reports")
    print(f"Temp Storage: {storage_stats['temp_storage']['api_responses']['count']} API, {storage_stats['temp_storage']['reports']['count']} Reports")
    print(f"Vector DB: {'Enabled' if storage_stats['vector_storage_enabled'] else 'Disabled'}")
    if storage_stats['vector_storage_enabled']:
        print(f"  URL: {storage_stats['vector_db']['url']}")
    
    print(f"\nGenerating report for ticker: {ticker}")
    if force_refresh:
        print("Force refresh mode - ignoring cache")
    print("=" * 50)
    
    try:
        report = await generate_comprehensive_report_with_storage(ticker, storage_manager, force_refresh)
        
        if "error" not in report:
            print("Report generated successfully!")
            print("\nCOMPREHENSIVE FINANCIAL REPORT")
            print("=" * 50)
            
            # Pretty print the JSON report
            print(json.dumps(report, indent=2, default=str))
            
            # Save report to reports directory
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            filename = reports_dir / f"financial_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nReport saved to: {filename}")
            
        else:
            print(f"Report generation failed: {report['error']}")
            
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        print(f"Report generation error: {e}")
        sys.exit(1)
    
    finally:
        # Clean up any resources
        logger.info("Report generation completed")
        
        # Display final storage stats
        final_stats = storage_manager.get_storage_stats()
        print(f"\nFINAL STORAGE STATS")
        print("-" * 20)
        print(f"Cache: {final_stats['cache']['llm']['count']} LLM, {final_stats['cache']['api']['count']} API, {final_stats['cache']['reports']['count']} Reports")
        print(f"Temp Storage: {final_stats['temp_storage']['api_responses']['count']} API, {final_stats['temp_storage']['reports']['count']} Reports")
        
        # Cleanup expired data
        cleanup_stats = await storage_manager.cleanup_expired_data()
        if cleanup_stats['cache_files_removed'] > 0 or cleanup_stats['temp_files_removed'] > 0:
            print(f"Cleanup: {cleanup_stats['cache_files_removed']} cache, {cleanup_stats['temp_files_removed']} temp files removed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
