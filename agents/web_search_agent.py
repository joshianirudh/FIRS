"""Web Search Agent for fetching expert analysis, news, and company information."""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
from urllib.parse import quote_plus

from .base_agent import BaseAgent, AgentResponse
from preprocessing.utils import ticker_to_company_name
from preprocessing.web_scraper import WebScraper
from storage.article_storage import ArticleStorage
from config import config

logger = logging.getLogger(__name__)


class WebSearchAgent(BaseAgent):
    """Agent for fetching web-based financial information and analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Web Search agent."""
        super().__init__(api_key or config["api"]["web_search_key"])
        self.name = "WebSearchAgent"
        self.rate_limit = 2  # Be respectful to search engines
        
        # Initialize storage and scraper
        self.article_storage = ArticleStorage()
        self.web_scraper = None
        
        # Financial news sources to prioritize
        self.financial_sources = [
            "reuters.com", "bloomberg.com", "cnbc.com", "marketwatch.com",
            "yahoo.com", "seekingalpha.com", "motleyfool.com", "fool.com",
            "investopedia.com", "wsj.com", "ft.com", "barrons.com"
        ]

    async def _get_web_scraper(self) -> WebScraper:
        """Get or create web scraper instance."""
        if self.web_scraper is None:
            self.web_scraper = WebScraper(
                timeout=config["api"]["request_timeout"],
                max_retries=config["system"]["max_retries"]
            )
        return self.web_scraper

    async def fetch_expert_analysis(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch expert analysis and research reports for a stock.

        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters (days_back, source_filter, etc.)

        Returns:
            AgentResponse with expert analysis data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Convert ticker to company name using LLM
            company_name = await ticker_to_company_name(ticker)
            logger.info(f"Converted ticker {ticker} to company name: {company_name}")
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for expert analysis
            search_queries = [
                f'"{company_name}" analyst ratings expert analysis research reports',
                f'"{ticker}" analyst recommendations buy sell hold',
                f'"{company_name}" investment research analysis',
                f'"{ticker}" stock analysis expert opinion'
            ]
            
            all_analysis = []
            
            async with scraper:
                for query in search_queries:
                    try:
                        articles = await scraper.search_and_fetch_articles(query, max_results=3)
                        all_analysis.extend(articles)
                        
                        # Add delay between queries
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Failed to search for query '{query}': {e}")
                        continue
            
            # Remove duplicates and filter quality content
            unique_analysis = self._deduplicate_articles(all_analysis)
            quality_analysis = [a for a in unique_analysis if a.get("word_count", 0) > 100]
            
            # Store the analysis data
            if quality_analysis:
                storage_path = self.article_storage.store_expert_analysis(ticker, quality_analysis)
                logger.info(f"Stored expert analysis for {ticker} at {storage_path}")
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "search_query": f"{ticker} analyst ratings expert analysis research reports",
                "sources_searched": self.financial_sources,
                "raw_results": quality_analysis,
                "search_metadata": {
                    "total_results": len(quality_analysis),
                    "search_time": datetime.now().isoformat(),
                    "query": f"{ticker} analyst ratings expert analysis",
                    "storage_path": storage_path if quality_analysis else None
                }
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={
                    "ticker": ticker,
                    "search_type": "expert_analysis",
                    "data_format": "real_web_content",
                    "company_name": company_name
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch expert analysis for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch expert analysis: {str(e)}",
                source=self.name
            )

    async def fetch_latest_news(self, ticker: str, days_back: int = 7, **kwargs) -> AgentResponse:
        """
        Fetch latest news articles about a company/stock.

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to look back
            **kwargs: Additional parameters (source_filter, etc.)

        Returns:
            AgentResponse with news data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Convert ticker to company name using LLM
            company_name = await ticker_to_company_name(ticker)
            logger.info(f"Converted ticker {ticker} to company name: {company_name}")
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for latest news
            async with scraper:
                news_articles = await scraper.search_financial_news(
                    ticker, company_name, days_back=days_back
                )
            
            # Store the news articles
            storage_path = ""
            if news_articles:
                storage_path = self.article_storage.store_news_articles(ticker, news_articles)
                logger.info(f"Stored {len(news_articles)} news articles for {ticker} at {storage_path}")
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "search_query": f"{ticker} stock news latest {days_back} days",
                "sources_searched": self.financial_sources,
                "raw_articles": news_articles,
                "search_metadata": {
                    "total_articles": len(news_articles),
                    "search_time": datetime.now().isoformat(),
                    "date_range": f"Last {days_back} days",
                    "storage_path": storage_path
                }
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={
                    "ticker": ticker,
                    "search_type": "latest_news",
                    "data_format": "real_web_content",
                    "period": f"Last {days_back} days",
                    "company_name": company_name
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch latest news for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch latest news: {str(e)}",
                source=self.name
            )

    async def fetch_company_research(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch comprehensive company research and analysis.

        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters (research_type, depth, etc.)

        Returns:
            AgentResponse with company research data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Convert ticker to company name using LLM
            company_name = await ticker_to_company_name(ticker)
            logger.info(f"Converted ticker {ticker} to company name: {company_name}")
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for company research
            search_queries = [
                f'"{company_name}" company profile business model',
                f'"{ticker}" competitive analysis market position',
                f'"{company_name}" business overview operations',
                f'"{ticker}" company information business description'
            ]
            
            all_research = []
            
            async with scraper:
                for query in search_queries:
                    try:
                        articles = await scraper.search_and_fetch_articles(query, max_results=3)
                        all_research.extend(articles)
                        
                        # Add delay between queries
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Failed to search for query '{query}': {e}")
                        continue
            
            # Remove duplicates and filter quality content
            unique_research = self._deduplicate_articles(all_research)
            quality_research = [r for r in unique_research if r.get("word_count", 0) > 150]
            
            # Store the research data
            storage_path = ""
            if quality_research:
                storage_path = self.article_storage.store_company_research(ticker, quality_research)
                logger.info(f"Stored company research for {ticker} at {storage_path}")
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "search_query": f"{ticker} company profile business model competitive analysis",
                "sources_searched": self.financial_sources + ["sec.gov", "investor relations"],
                "raw_research": quality_research,
                "search_metadata": {
                    "total_sources": len(quality_research),
                    "search_time": datetime.now().isoformat(),
                    "research_depth": "comprehensive",
                    "storage_path": storage_path
                }
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={
                    "ticker": ticker,
                    "search_type": "company_research",
                    "data_format": "real_web_content",
                    "company_name": company_name
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch company research for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch company research: {str(e)}",
                source=self.name
            )

    async def fetch_social_discussions(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch social media discussions and mentions.

        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters (platforms, days_back, etc.)

        Returns:
            AgentResponse with social discussion data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Convert ticker to company name using LLM
            company_name = await ticker_to_company_name(ticker)
            logger.info(f"Converted ticker {ticker} to company name: {company_name}")
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for social discussions
            search_queries = [
                f'"{ticker}" stock discussion reddit',
                f'"{company_name}" stock forum discussion',
                f'"{ticker}" investor forum community',
                f'"{company_name}" stock analysis discussion'
            ]
            
            all_social = []
            
            async with scraper:
                for query in search_queries:
                    try:
                        articles = await scraper.search_and_fetch_articles(query, max_results=3)
                        all_social.extend(articles)
                        
                        # Add delay between queries
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Failed to search for query '{query}': {e}")
                        continue
            
            # Remove duplicates and filter quality content
            unique_social = self._deduplicate_articles(all_social)
            quality_social = [s for s in unique_social if s.get("word_count", 0) > 50]
            
            # Store the social data
            storage_path = ""
            if quality_social:
                storage_path = self.article_storage.store_social_discussions(ticker, quality_social)
                logger.info(f"Stored social discussions for {ticker} at {storage_path}")
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "search_query": f"{ticker} stock discussion social media mentions",
                "platforms_searched": ["reddit", "forums", "community sites"],
                "raw_discussions": quality_social,
                "search_metadata": {
                    "total_mentions": len(quality_social),
                    "search_time": datetime.now().isoformat(),
                    "platforms_covered": len(set(s.get("source", "") for s in quality_social)),
                    "storage_path": storage_path
                }
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={
                    "ticker": ticker,
                    "search_type": "social_discussions",
                    "data_format": "real_web_content",
                    "company_name": company_name
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch social discussions for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch social discussions: {str(e)}",
                source=self.name
            )

    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL."""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles

    # Required abstract methods from BaseAgent
    async def fetch_stock_data(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch stock data - delegates to web search for comprehensive analysis.
        
        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters
            
        Returns:
            AgentResponse with stock data from web sources
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Get company name
            company_name = await ticker_to_company_name(ticker)
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for general stock information
            search_query = f'"{company_name}" stock price market cap financial data'
            
            async with scraper:
                articles = await scraper.search_and_fetch_articles(search_query, max_results=5)
            
            # Store the stock data articles
            storage_path = ""
            if articles:
                storage_path = self.article_storage.store_news_articles(ticker, articles)
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "web_sources": {
                    "expert_analysis": "Available via fetch_expert_analysis()",
                    "latest_news": "Available via fetch_latest_news()",
                    "social_discussions": "Available via fetch_social_discussions()",
                    "company_research": "Available via fetch_company_research()"
                },
                "recent_articles": len(articles),
                "storage_path": storage_path,
                "data_source": "Web Search Agent - Real Web Content"
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={"ticker": ticker, "method": "web_search_stock_data", "company_name": company_name}
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch stock data for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch stock data: {str(e)}",
                source=self.name
            )

    async def fetch_historical_data(self, ticker: str, start_date: str, end_date: str, **kwargs) -> AgentResponse:
        """
        Fetch historical data - provides web-based historical analysis.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional parameters
            
        Returns:
            AgentResponse with historical analysis data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Get company name
            company_name = await ticker_to_company_name(ticker)
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for historical analysis
            search_query = f'"{company_name}" historical performance {start_date} to {end_date}'
            
            async with scraper:
                articles = await scraper.search_and_fetch_articles(search_query, max_results=5)
            
            # Store the historical data articles
            storage_path = ""
            if articles:
                storage_path = self.article_storage.store_news_articles(ticker, articles)
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "period": f"{start_date} to {end_date}",
                "web_analysis": {
                    "key_events": "Available in stored articles",
                    "analyst_coverage": "Available in stored articles",
                    "news_coverage": "Available in stored articles",
                    "sentiment_trends": "Available in stored articles"
                },
                "recent_articles": len(articles),
                "storage_path": storage_path,
                "data_source": "Web Search Agent - Real Historical Analysis"
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={
                    "ticker": ticker,
                    "period": f"{start_date} to {end_date}",
                    "method": "web_search_historical",
                    "company_name": company_name
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch historical data: {str(e)}",
                source=self.name
            )

    async def fetch_company_info(self, ticker: str) -> AgentResponse:
        """
        Fetch company information - provides comprehensive web-based company research.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            AgentResponse with company information from web sources
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        try:
            # Get company name
            company_name = await ticker_to_company_name(ticker)
            
            # Get web scraper
            scraper = await self._get_web_scraper()
            
            # Search for company information
            search_query = f'"{company_name}" company overview business description'
            
            async with scraper:
                articles = await scraper.search_and_fetch_articles(search_query, max_results=5)
            
            # Store the company info articles
            storage_path = ""
            if articles:
                storage_path = self.article_storage.store_company_research(ticker, articles)
            
            # Prepare response data
            response_data = {
                "symbol": ticker,
                "company_name": company_name,
                "web_research_summary": {
                    "business_model": "Available in stored articles",
                    "competitive_position": "Available in stored articles",
                    "growth_strategy": "Available in stored articles",
                    "risk_factors": "Available in stored articles"
                },
                "recent_articles": len(articles),
                "storage_path": storage_path,
                "data_sources": [
                    "Financial news websites",
                    "Company research sites",
                    "Business directories",
                    "Industry analysis"
                ],
                "data_source": "Web Search Agent - Real Company Research"
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={"ticker": ticker, "method": "web_search_company_info", "company_name": company_name}
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch company info for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch company info: {str(e)}",
                source=self.name
            )

    def _clean_search_query(self, query: str) -> str:
        """Clean and format search queries."""
        # Remove special characters and format for search
        cleaned = re.sub(r'[^\w\s]', '', query)
        return quote_plus(cleaned.strip())

    def _extract_key_entities(self, text: str) -> List[str]:
        """Extract key entities from text (placeholder for NLP implementation)."""
        # Mock implementation - replace with real NLP entity extraction
        common_entities = ["earnings", "revenue", "growth", "innovation", "competition", 
                          "regulation", "market", "product", "service", "financial"]
        return [entity for entity in common_entities if entity.lower() in text.lower()]
