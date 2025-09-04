"""Finnhub API agent for fetching financial data."""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

from .base_agent import BaseAgent, AgentResponse
from config import config

logger = logging.getLogger(__name__)


class FinnhubAgent(BaseAgent):
    """Agent for fetching data from Finnhub API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Finnhub agent."""
        super().__init__(api_key or config["api"]["finnhub_key"])
        self.base_url = "https://finnhub.io/api/v1"
        self.name = "FinnhubAgent"
        
        if not self.api_key:
            logger.warning("Finnhub API key not provided. Some functions may fail.")

    async def _make_api_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request to Finnhub with error handling."""
        if not self.api_key:
            return {"error": "API key not provided"}
        
        if params is None:
            params = {}
        
        params["token"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "error" in data:
                    logger.error(f"Finnhub API error: {data['error']}")
                    return data
                
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": f"Request failed: {str(e)}"}

    async def fetch_stock_data(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch real-time stock data from Finnhub.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AgentResponse with stock data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        if not self.api_key:
            return AgentResponse(
                success=False,
                error="Finnhub API key not provided",
                source=self.name
            )

        params = {"symbol": ticker}
        data = await self._make_api_request("quote", params)
        
        if "error" in data:
            return AgentResponse(
                success=False,
                error=data["error"],
                source=self.name
            )
        
        if not data or data.get("c") is None:
            return AgentResponse(
                success=False,
                error="No stock data returned from Finnhub",
                source=self.name
            )
        
        response_data = {
            "symbol": ticker,
            "current_price": data.get("c", 0),
            "high_price": data.get("h", 0),
            "low_price": data.get("l", 0),
            "open_price": data.get("o", 0),
            "previous_close": data.get("pc", 0),
            "timestamp": data.get("t", 0),
            "last_updated": datetime.now().isoformat()
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={"ticker": ticker, "endpoint": "quote"}
        )

    async def fetch_historical_data(
            self,
            ticker: str,
            start_date: str,
            end_date: str,
            **kwargs
    ) -> AgentResponse:
        """
        Fetch historical candlestick data from Finnhub.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            AgentResponse with historical data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        if not self.api_key:
            return AgentResponse(
                success=False,
                error="Finnhub API key not provided",
                source=self.name
            )

        # Convert dates to timestamps
        try:
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
        except ValueError as e:
            return AgentResponse(
                success=False,
                error=f"Invalid date format: {e}",
                source=self.name
            )

        resolution = kwargs.get("resolution", "D")
        
        params = {
            "symbol": ticker,
            "resolution": resolution,
            "from": start_timestamp,
            "to": end_timestamp
        }
        
        data = await self._make_api_request("stock/candle", params)
        
        if "error" in data:
            return AgentResponse(
                success=False,
                error=data["error"],
                source=self.name
            )
        
        if data.get("s") != "ok":
            return AgentResponse(
                success=False,
                error="No historical data returned from Finnhub",
                source=self.name
            )
        
        # Convert timestamps to dates and format data
        candles = []
        for i in range(len(data.get("t", []))):
            if i < len(data.get("c", [])) and i < len(data.get("h", [])) and i < len(data.get("l", [])) and i < len(data.get("o", [])) and i < len(data.get("v", [])):
                candles.append({
                    "timestamp": data["t"][i],
                    "date": datetime.fromtimestamp(data["t"][i]).strftime("%Y-%m-%d"),
                    "close": data["c"][i],
                    "high": data["h"][i],
                    "low": data["l"][i],
                    "open": data["o"][i],
                    "volume": data["v"][i]
                })
        
        response_data = {
            "symbol": ticker,
            "status": data.get("s", ""),
            "resolution": resolution,
            "candles": candles,
            "start_date": start_date,
            "end_date": end_date,
            "data_points": len(candles)
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={
                "ticker": ticker,
                "resolution": resolution,
                "from": start_date,
                "to": end_date
            }
        )

    async def fetch_company_info(self, ticker: str) -> AgentResponse:
        """
        Fetch company profile from Finnhub.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AgentResponse with company information
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        if not self.api_key:
            return AgentResponse(
                success=False,
                error="Finnhub API key not provided",
                source=self.name
            )

        params = {"symbol": ticker}
        data = await self._make_api_request("stock/profile2", params)
        
        if "error" in data:
            return AgentResponse(
                success=False,
                error=data["error"],
                source=self.name
            )
        
        if not data or len(data) <= 1:  # Only metadata or empty
            return AgentResponse(
                success=False,
                error="No company information returned from Finnhub",
                source=self.name
            )
        
        response_data = {
            "country": data.get("country", ""),
            "currency": data.get("currency", ""),
            "exchange": data.get("exchange", ""),
            "finnhubIndustry": data.get("finnhubIndustry", ""),
            "ipo": data.get("ipo", ""),
            "logo": data.get("logo", ""),
            "marketCapitalization": data.get("marketCapitalization", 0),
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "shareOutstanding": data.get("shareOutstanding", 0),
            "ticker": data.get("ticker", ticker),
            "weburl": data.get("weburl", ""),
            "isin": data.get("isin", ""),
            "cusip": data.get("cusip", ""),
            "outstandingShares": data.get("outstandingShares", 0),
            "freeFloat": data.get("freeFloat", 0),
            "marketCapCategory": data.get("marketCapCategory", ""),
            "employeeTotal": data.get("employeeTotal", 0),
            "primaryIndustry": data.get("primaryIndustry", ""),
            "industryGroup": data.get("industryGroup", ""),
            "sector": data.get("sector", ""),
            "finnhubSector": data.get("finnhubSector", "")
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={"ticker": ticker, "endpoint": "company-profile2"}
        )

    async def fetch_news(self, ticker: str, days_back: int = 7) -> AgentResponse:
        """
        Fetch recent news for a stock from Finnhub.

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to look back for news

        Returns:
            AgentResponse with news articles
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        if not self.api_key:
            return AgentResponse(
                success=False,
                error="Finnhub API key not provided",
                source=self.name
            )

        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        params = {
            "symbol": ticker,
            "from": from_date,
            "to": to_date
        }
        
        data = await self._make_api_request("company-news", params)
        
        if "error" in data:
            return AgentResponse(
                success=False,
                error=data["error"],
                source=self.name
            )
        
        if not data:
            return AgentResponse(
                success=False,
                error="No news data returned from Finnhub",
                source=self.name
            )
        
        # Format news articles
        articles = []
        for article in data:
            articles.append({
                "category": article.get("category", ""),
                "datetime": article.get("datetime", 0),
                "headline": article.get("headline", ""),
                "id": article.get("id", 0),
                "image": article.get("image", ""),
                "related": article.get("related", ""),
                "source": article.get("source", ""),
                "summary": article.get("summary", ""),
                "url": article.get("url", ""),
                "date": datetime.fromtimestamp(article.get("datetime", 0)).strftime("%Y-%m-%d %H:%M:%S") if article.get("datetime") else ""
            })
        
        response_data = {
            "symbol": ticker,
            "articles": articles,
            "from": from_date,
            "to": to_date,
            "article_count": len(articles)
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={
                "ticker": ticker,
                "endpoint": "company-news",
                "period": f"{from_date} to {to_date}"
            }
        )