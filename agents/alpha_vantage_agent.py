"""Alpha Vantage API agent for fetching financial data."""
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
import json
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse
from config import config

logger = logging.getLogger(__name__)


class AlphaVantageAgent(BaseAgent):
    """Agent for fetching data from Alpha Vantage API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage agent."""
        super().__init__(api_key or config["api"]["alpha_vantage_key"])
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit = 5  # 5 API requests per minute for free tier
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided. Some functions may fail.")
        
        self.name = "AlphaVantageAgent"

    async def _make_api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to Alpha Vantage with error handling."""
        if not self.api_key:
            return {"Error Message": "API key not provided"}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return data
                
                if "Note" in data:
                    logger.warning(f"Alpha Vantage API note: {data['Note']}")
                
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return {"Error Message": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"Error Message": f"Request failed: {str(e)}"}

    async def fetch_stock_data(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch real-time stock data from Alpha Vantage.

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
                error="Alpha Vantage API key not provided",
                source=self.name
            )

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": self.api_key
        }
        
        data = await self._make_api_request(params)
        
        if "Error Message" in data:
            return AgentResponse(
                success=False,
                error=data["Error Message"],
                source=self.name
            )
        
        if "Global Quote" not in data or not data["Global Quote"]:
            return AgentResponse(
                success=False,
                error="No data returned from Alpha Vantage",
                source=self.name
            )
        
        quote = data["Global Quote"]
        
        response_data = {
            "symbol": quote.get("01. symbol", ticker),
            "price": float(quote.get("05. price", 0)),
            "volume": int(quote.get("06. volume", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%"),
            "last_updated": datetime.now().isoformat(),
            "open": float(quote.get("02. open", 0)),
            "high": float(quote.get("03. high", 0)),
            "low": float(quote.get("04. low", 0)),
            "previous_close": float(quote.get("08. previous close", 0))
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={"function": "GLOBAL_QUOTE", "ticker": ticker}
        )

    async def fetch_historical_data(
            self,
            ticker: str,
            start_date: str,
            end_date: str,
            **kwargs
    ) -> AgentResponse:
        """
        Fetch historical data from Alpha Vantage.

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
                error="Alpha Vantage API key not provided",
                source=self.name
            )

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": ticker,
            "apikey": self.api_key,
            "outputsize": "full"
        }
        
        data = await self._make_api_request(params)
        
        if "Error Message" in data:
            return AgentResponse(
                success=False,
                error=data["Error Message"],
                source=self.name
            )
        
        if "Time Series (Daily)" not in data:
            return AgentResponse(
                success=False,
                error="No historical data returned from Alpha Vantage",
                source=self.name
            )
        
        time_series = data["Time Series (Daily)"]
        
        # Filter data by date range
        filtered_data = []
        for date, values in time_series.items():
            if start_date <= date <= end_date:
                filtered_data.append({
                    "date": date,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "adjusted_close": float(values.get("5. adjusted close", 0)),
                    "volume": int(values.get("6. volume", 0)),
                    "dividend_amount": float(values.get("7. dividend amount", 0)),
                    "split_coefficient": float(values.get("8. split coefficient", 1))
                })
        
        # Sort by date
        filtered_data.sort(key=lambda x: x["date"])
        
        response_data = {
            "symbol": ticker,
            "time_series": filtered_data,
            "start_date": start_date,
            "end_date": end_date,
            "data_points": len(filtered_data)
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "ticker": ticker,
                "period": f"{start_date} to {end_date}"
            }
        )

    async def fetch_company_info(self, ticker: str) -> AgentResponse:
        """
        Fetch company overview from Alpha Vantage.

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
                error="Alpha Vantage API key not provided",
                source=self.name
            )

        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": self.api_key
        }
        
        data = await self._make_api_request(params)
        
        if "Error Message" in data:
            return AgentResponse(
                success=False,
                error=data["Error Message"],
                source=self.name
            )
        
        if not data or len(data) <= 1:  # Only metadata or empty
            return AgentResponse(
                success=False,
                error="No company information returned from Alpha Vantage",
                source=self.name
            )
        
        response_data = {
            "symbol": data.get("Symbol", ticker),
            "name": data.get("Name", ""),
            "description": data.get("Description", ""),
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "market_cap": data.get("MarketCapitalization", ""),
            "pe_ratio": data.get("PERatio", ""),
            "dividend_yield": data.get("DividendYield", ""),
            "eps": data.get("EPS", ""),
            "price_to_book": data.get("PriceToBookRatio", ""),
            "roe": data.get("ReturnOnEquityTTM", ""),
            "revenue_ttm": data.get("RevenueTTM", ""),
            "profit_margin": data.get("ProfitMargin", ""),
            "fifty_two_week_high": data.get("52WeekHigh", ""),
            "fifty_two_week_low": data.get("52WeekLow", ""),
            "exchange": data.get("Exchange", ""),
            "currency": data.get("Currency", ""),
            "country": data.get("Country", ""),
            "fiscal_year_end": data.get("FiscalYearEnd", "")
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={"function": "OVERVIEW", "ticker": ticker}
        )

    async def fetch_earnings(self, ticker: str) -> AgentResponse:
        """
        Fetch earnings data from Alpha Vantage.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AgentResponse with earnings data
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
                error="Alpha Vantage API key not provided",
                source=self.name
            )

        params = {
            "function": "EARNINGS",
            "symbol": ticker,
            "apikey": self.api_key
        }
        
        data = await self._make_api_request(params)
        
        if "Error Message" in data:
            return AgentResponse(
                success=False,
                error=data["Error Message"],
                source=self.name
            )
        
        if "annualEarnings" not in data:
            return AgentResponse(
                success=False,
                error="No earnings data returned from Alpha Vantage",
                source=self.name
            )
        
        annual_earnings = data.get("annualEarnings", [])
        quarterly_earnings = data.get("quarterlyEarnings", [])
        
        response_data = {
            "symbol": ticker,
            "annual_earnings": [
                {
                    "fiscal_year": earning.get("fiscalDateEnding", ""),
                    "eps": earning.get("reportedEPS", ""),
                    "reported_date": earning.get("reportedDate", ""),
                    "estimated_eps": earning.get("estimatedEPS", ""),
                    "surprise": earning.get("surprise", ""),
                    "surprise_percentage": earning.get("surprisePercentage", "")
                }
                for earning in annual_earnings
            ],
            "quarterly_earnings": [
                {
                    "fiscal_quarter": earning.get("fiscalDateEnding", ""),
                    "eps": earning.get("reportedEPS", ""),
                    "reported_date": earning.get("reportedDate", ""),
                    "estimated_eps": earning.get("estimatedEPS", ""),
                    "surprise": earning.get("surprise", ""),
                    "surprise_percentage": earning.get("surprisePercentage", "")
                }
                for earning in quarterly_earnings
            ]
        }

        return AgentResponse(
            success=True,
            data=response_data,
            source=self.name,
            metadata={"function": "EARNINGS", "ticker": ticker}
        )