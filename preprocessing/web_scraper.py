"""Web scraping utilities for fetching real content from websites."""
import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper for fetching real content from financial websites."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """Initialize web scraper."""
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        
        # Financial news sources to prioritize
        self.financial_sources = [
            "reuters.com", "bloomberg.com", "cnbc.com", "marketwatch.com",
            "yahoo.com", "seekingalpha.com", "motleyfool.com", "fool.com",
            "investopedia.com", "wsj.com", "ft.com", "barrons.com"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    async def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo for free web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                # Format results consistently
                formatted_results = []
                for result in results:
                    # Extract URL from the result
                    url = result.get("link", "")
                    if not url and "href" in result:
                        url = result["href"]
                    
                    # Skip results without valid URLs
                    if not url or not url.startswith(('http://', 'https://')):
                        continue
                    
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": url,
                        "snippet": result.get("body", ""),
                        "source": self._extract_domain(url)
                    })
                
                logger.info(f"DuckDuckGo search returned {len(formatted_results)} results for: {query}")
                return formatted_results
                
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def fetch_article_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch full article content from a URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Dictionary with article content, metadata, and text
        """
        if not self.session:
            raise RuntimeError("WebScraper not initialized as async context manager")
        
        try:
            # Use BeautifulSoup for content extraction
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content (try different selectors)
            content_selectors = [
                'article', '[role="main"]', '.content', '.article-content',
                '.post-content', '.entry-content', 'main', '.main-content'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                # Fallback to body
                main_content = soup.find('body')
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                # Clean up text
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'\n+', '\n', text)
            else:
                text = ""
            
            # Extract keywords (simple approach)
            keywords = []
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                keywords = [kw.strip() for kw in meta_keywords.get('content', '').split(',')]
            
            # Extract publish date
            publish_date = None
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publish_date"]',
                'time',
                '.date',
                '.published'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_attr = date_elem.get('datetime') or date_elem.get('content') or date_elem.get_text()
                    if date_attr:
                        publish_date = date_attr.strip()
                        break
            
            content = {
                "title": title,
                "text": text,
                "summary": text[:500] + "..." if len(text) > 500 else text,
                "keywords": keywords,
                "publish_date": publish_date,
                "authors": [],
                "url": url,
                "source": self._extract_domain(url),
                "word_count": len(text.split()) if text else 0,
                "extraction_method": "beautifulsoup"
            }
            
            logger.info(f"Successfully extracted article content using BeautifulSoup: {url}")
            return content
                
        except Exception as e:
            logger.error(f"Failed to fetch article content from {url}: {e}")
            return {
                "title": "",
                "text": "",
                "summary": "",
                "keywords": [],
                "publish_date": None,
                "authors": [],
                "url": url,
                "source": self._extract_domain(url),
                "word_count": 0,
                "extraction_method": "failed",
                "error": str(e)
            }
    
    async def search_and_fetch_articles(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for articles and fetch their full content.
        
        Args:
            query: Search query
            max_results: Maximum number of articles to fetch
            
        Returns:
            List of articles with full content
        """
        # First, search for relevant URLs
        search_results = await self.search_duckduckgo(query, max_results=max_results)
        
        if not search_results:
            return []
        
        # Fetch content for each URL
        articles = []
        for result in search_results:
            try:
                article_content = await self.fetch_article_content(result["url"])
                
                # Merge search result with article content
                full_article = {
                    **result,
                    **article_content
                }
                
                articles.append(full_article)
                
                # Add small delay to be respectful
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to fetch article from {result['url']}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(articles)} articles for query: {query}")
        return articles
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url
    
    def _is_financial_source(self, url: str) -> bool:
        """Check if URL is from a preferred financial source."""
        domain = self._extract_domain(url)
        return any(source in domain for source in self.financial_sources)
    
    async def search_financial_news(self, ticker: str, company_name: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Search for financial news about a specific company.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            days_back: Number of days to look back
            
        Returns:
            List of financial news articles
        """
        # Create search queries
        queries = [
            f'"{company_name}" stock news {days_back} days',
            f'"{ticker}" earnings news {days_back} days',
            f'"{company_name}" financial performance {days_back} days',
            f'"{ticker}" analyst ratings {days_back} days'
        ]
        
        all_articles = []
        
        for query in queries:
            try:
                articles = await self.search_and_fetch_articles(query, max_results=5)
                all_articles.extend(articles)
                
                # Add delay between queries
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to search for query '{query}': {e}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        # Sort by word count (more content = better quality)
        unique_articles.sort(key=lambda x: x.get("word_count", 0), reverse=True)
        
        logger.info(f"Found {len(unique_articles)} unique financial news articles for {ticker}")
        return unique_articles[:10]


# Convenience function
async def create_web_scraper(timeout: int = 30, max_retries: int = 3) -> WebScraper:
    """Create a web scraper instance."""
    return WebScraper(timeout=timeout, max_retries=max_retries)
