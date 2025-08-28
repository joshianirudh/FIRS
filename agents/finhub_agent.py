"""Finnhub API agent for fetching financial data."""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentResponse
from config import config


class FinnhubAgent(BaseAgent):
    """Agent for fetching data from Finnhub API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Finnhub agent."""
        super().__init__(api_key or config.api.finnhub_key)
        self.base_url = "https://finnhub.io/api/v1"

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

        # Mock implementation
        mock_data = {
            "symbol": ticker,
            "c": 150.25,  # Current price
            "h": 152.00,  # High price of the day
            "l": 148.50,  # Low price of the day
            "o": 149.00,  # Open price of the day
            "pc": 148.00,  # Previous close price
            "t": datetime.now().timestamp()
        }

        # Real implementation would be:
        # params = {"symbol": ticker, "token": self.api_key}
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(f"{self.base_url}/quote", params=params)
        #     data = response.json()

        return AgentResponse(
            success=True,
            data=mock_data,
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

        # Mock implementation
        mock_data = {
            "symbol": ticker,
            "s": "ok",  # Status
            "c": [149.0, 151.0, 150.5],  # Close prices
            "h": [150.0, 152.0, 151.5],  # High prices
            "l": [148.0, 149.5, 149.0],  # Low prices
            "o": [148.5, 149.0, 150.0],  # Open prices
            "t": [1704067200, 1704153600, 1704240000],  # Timestamps
            "v": [50000000, 48000000, 51000000]  # Volume
        }

        # Real implementation would convert dates to timestamps
        # and use the candles endpoint

        return AgentResponse(
            success=True,
            data=mock_data,
            source=self.name,
            metadata={
                "ticker": ticker,
                "resolution": kwargs.get("resolution", "D"),
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

        # Mock implementation
        mock_data = {
            "country": "US",
            "currency": "USD",
            "exchange": "NASDAQ",
            "finnhubIndustry": "Technology",
            "ipo": "1980-12-12",
            "logo": "https://static.finnhub.io/logo/example.png",
            "marketCapitalization": 2450000,
            "name": "Example Corporation",
            "phone": "14089961010",
            "shareOutstanding": 15728.7,
            "ticker": ticker,
            "weburl": "https://www.example.com"
        }

        # Real implementation would use company-profile2 endpoint

        return AgentResponse(
            success=True,
            data=mock_data,
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
        # Additional method specific to Finnhub
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        mock_data = {
            "symbol": ticker,
            "articles": [
                {
                    "category": "technology",
                    "datetime": 1704240000,
                    "headline": "Example Corp Reports Strong Q4 Earnings",
                    "id": 123456,
                    "image": "https://example.com/image.jpg",
                    "related": ticker,
                    "source": "Reuters",
                    "summary": "Example Corporation reported better than expected...",
                    "url": "https://example.com/article"
                }
            ],
            "from": from_date,
            "to": to_date
        }

        return AgentResponse(
            success=True,
            data=mock_data,
            source=self.name,
            metadata={
                "ticker": ticker,
                "endpoint": "company-news",
                "period": f"{from_date} to {to_date}"
            }
        )