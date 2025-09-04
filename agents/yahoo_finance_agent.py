"""Yahoo Finance API agent for fetching financial data."""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import yfinance as yf

from .base_agent import BaseAgent, AgentResponse
from config import config

logger = logging.getLogger(__name__)


class YahooFinanceAgent(BaseAgent):
    """Agent for fetching data from Yahoo Finance."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Yahoo Finance agent."""
        super().__init__(api_key or config["api"]["yahoo_finance_key"])
        self.base_url = "https://query1.finance.yahoo.com"
        # Note: yfinance library doesn't require API key
        self.name = "YahooFinanceAgent"

    async def _get_ticker_info(self, ticker: str) -> Optional[yf.Ticker]:
        """Get yfinance Ticker object with error handling."""
        try:
            ticker_obj = yf.Ticker(ticker)
            # Test if ticker is valid by trying to get info
            info = ticker_obj.info
            if not info or len(info) <= 1:  # Only metadata or empty
                logger.warning(f"No data available for ticker: {ticker}")
                return None
            return ticker_obj
        except Exception as e:
            logger.error(f"Failed to get ticker info for {ticker}: {e}")
            return None

    async def fetch_stock_data(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch real-time stock data from Yahoo Finance.

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

        ticker_obj = await self._get_ticker_info(ticker)
        if not ticker_obj:
            return AgentResponse(
                success=False,
                error=f"Failed to get data for ticker: {ticker}",
                source=self.name
            )

        try:
            info = ticker_obj.info
            
            response_data = {
                "symbol": info.get("symbol", ticker),
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "previousClose": info.get("previousClose", 0),
                "open": info.get("open", 0),
                "dayLow": info.get("dayLow", 0),
                "dayHigh": info.get("dayHigh", 0),
                "volume": info.get("volume", 0),
                "averageVolume": info.get("averageVolume", 0),
                "marketCap": info.get("marketCap", 0),
                "beta": info.get("beta", 0),
                "trailingPE": info.get("trailingPE", 0),
                "forwardPE": info.get("forwardPE", 0),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", 0),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", 0),
                "dividendYield": info.get("dividendYield", 0),
                "priceToBook": info.get("priceToBook", 0),
                "returnOnEquity": info.get("returnOnEquity", 0),
                "returnOnAssets": info.get("returnOnAssets", 0),
                "debtToEquity": info.get("debtToEquity", 0),
                "currentRatio": info.get("currentRatio", 0),
                "quickRatio": info.get("quickRatio", 0),
                "last_updated": datetime.now().isoformat()
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={"ticker": ticker, "market": "US"}
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch stock data for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch stock data: {str(e)}",
                source=self.name
            )

    async def fetch_historical_data(
            self,
            ticker: str,
            start_date: str,
            end_date: str,
            **kwargs
    ) -> AgentResponse:
        """
        Fetch historical data from Yahoo Finance.

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

        ticker_obj = await self._get_ticker_info(ticker)
        if not ticker_obj:
            return AgentResponse(
                success=False,
                error=f"Failed to get data for ticker: {ticker}",
                source=self.name
            )

        try:
            interval = kwargs.get("interval", "1d")
            hist = ticker_obj.history(start=start_date, end=end_date, interval=interval)
            
            if hist.empty:
                return AgentResponse(
                    success=False,
                    error=f"No historical data available for {ticker} from {start_date} to {end_date}",
                    source=self.name
                )
            
            # Convert DataFrame to list of dictionaries
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "adjClose": float(row.get("Adj Close", 0)),
                    "volume": int(row.get("Volume", 0))
                })
            
            response_data = {
                "symbol": ticker,
                "period": f"{start_date} to {end_date}",
                "interval": interval,
                "data": data,
                "data_points": len(data)
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={
                    "ticker": ticker,
                    "period": f"{start_date} to {end_date}",
                    "interval": interval
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
        Fetch company information from Yahoo Finance.

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

        ticker_obj = await self._get_ticker_info(ticker)
        if not ticker_obj:
            return AgentResponse(
                success=False,
                error=f"Failed to get data for ticker: {ticker}",
                source=self.name
            )

        try:
            info = ticker_obj.info
            
            response_data = {
                "symbol": info.get("symbol", ticker),
                "shortName": info.get("shortName", ""),
                "longName": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "country": info.get("country", ""),
                "currency": info.get("currency", ""),
                "exchange": info.get("exchange", ""),
                "market": info.get("market", ""),
                "quoteType": info.get("quoteType", ""),
                "marketCap": info.get("marketCap", 0),
                "enterpriseValue": info.get("enterpriseValue", 0),
                "floatShares": info.get("floatShares", 0),
                "sharesOutstanding": info.get("sharesOutstanding", 0),
                "sharesShort": info.get("sharesShort", 0),
                "sharesShortPriorMonth": info.get("sharesShortPriorMonth", 0),
                "sharesShortPreviousMonthDate": info.get("sharesShortPreviousMonthDate", ""),
                "dateShortInterest": info.get("dateShortInterest", ""),
                "sharesPercentSharesOut": info.get("sharesPercentSharesOut", 0),
                "heldPercentInsiders": info.get("heldPercentInsiders", 0),
                "heldPercentInstitutions": info.get("heldPercentInstitutions", 0),
                "shortRatio": info.get("shortRatio", 0),
                "shortPercentOfFloat": info.get("shortPercentOfFloat", 0),
                "impliedSharesOutstanding": info.get("impliedSharesOutstanding", 0),
                "bookValue": info.get("bookValue", 0),
                "priceToBook": info.get("priceToBook", 0),
                "priceToSalesTrailing12Months": info.get("priceToSalesTrailing12Months", 0),
                "enterpriseToRevenue": info.get("enterpriseToRevenue", 0),
                "enterpriseToEbitda": info.get("enterpriseToEbitda", 0),
                "fiftyTwoWeekChange": info.get("fiftyTwoWeekChange", 0),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", 0),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", 0),
                "fiftyDayAverage": info.get("fiftyDayAverage", 0),
                "twoHundredDayAverage": info.get("twoHundredDayAverage", 0),
                "trailingAnnualDividendRate": info.get("trailingAnnualDividendRate", 0),
                "trailingAnnualDividendYield": info.get("trailingAnnualDividendYield", 0),
                "payoutRatio": info.get("payoutRatio", 0),
                "fiveYearAvgDividendYield": info.get("fiveYearAvgDividendYield", 0),
                "forwardEps": info.get("forwardEps", 0),
                "forwardPE": info.get("forwardPE", 0),
                "priceToSalesTrailing12Months": info.get("priceToSalesTrailing12Months", 0),
                "pegRatio": info.get("pegRatio", 0),
                "trailingEps": info.get("trailingEps", 0),
                "trailingPE": info.get("trailingPE", 0),
                "returnOnAssets": info.get("returnOnAssets", 0),
                "returnOnEquity": info.get("returnOnEquity", 0),
                "revenue": info.get("totalRevenue", 0),
                "revenuePerShare": info.get("revenuePerShare", 0),
                "revenueGrowth": info.get("revenueGrowth", 0),
                "grossProfits": info.get("grossProfits", 0),
                "freeCashflow": info.get("freeCashflow", 0),
                "operatingCashflow": info.get("operatingCashflow", 0),
                "earningsGrowth": info.get("earningsGrowth", 0),
                "revenueGrowth": info.get("revenueGrowth", 0),
                "grossMargins": info.get("grossMargins", 0),
                "ebitdaMargins": info.get("ebitdaMargins", 0),
                "operatingMargins": info.get("operatingMargins", 0),
                "profitMargins": info.get("profitMargins", 0)
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={"ticker": ticker}
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch company info for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch company info: {str(e)}",
                source=self.name
            )

    async def fetch_options_chain(self, ticker: str) -> AgentResponse:
        """
        Fetch options chain data from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AgentResponse with options data
        """
        if not self.validate_ticker(ticker):
            return AgentResponse(
                success=False,
                error=f"Invalid ticker: {ticker}",
                source=self.name
            )

        ticker_obj = await self._get_ticker_info(ticker)
        if not ticker_obj:
            return AgentResponse(
                success=False,
                error=f"Failed to get data for ticker: {ticker}",
                source=self.name
            )

        try:
            # Get options expiration dates
            expirations = ticker_obj.options
            
            if not expirations:
                return AgentResponse(
                    success=False,
                    error=f"No options data available for {ticker}",
                    source=self.name
                )
            
            # Get options chain for the first available expiration
            first_exp = expirations[0]
            options = ticker_obj.option_chain(first_exp)
            
            calls = []
            puts = []
            
            if options.calls is not None and not options.calls.empty:
                for _, row in options.calls.iterrows():
                    calls.append({
                        "strike": float(row.get("strike", 0)),
                        "lastPrice": float(row.get("lastPrice", 0)),
                        "bid": float(row.get("bid", 0)),
                        "ask": float(row.get("ask", 0)),
                        "volume": int(row.get("volume", 0)),
                        "openInterest": int(row.get("openInterest", 0)),
                        "impliedVolatility": float(row.get("impliedVolatility", 0)),
                        "delta": float(row.get("delta", 0)),
                        "gamma": float(row.get("gamma", 0)),
                        "theta": float(row.get("theta", 0)),
                        "vega": float(row.get("vega", 0))
                    })
            
            if options.puts is not None and not options.puts.empty:
                for _, row in options.puts.iterrows():
                    puts.append({
                        "strike": float(row.get("strike", 0)),
                        "lastPrice": float(row.get("lastPrice", 0)),
                        "bid": float(row.get("bid", 0)),
                        "ask": float(row.get("ask", 0)),
                        "volume": int(row.get("volume", 0)),
                        "openInterest": int(row.get("openInterest", 0)),
                        "impliedVolatility": float(row.get("impliedVolatility", 0)),
                        "delta": float(row.get("delta", 0)),
                        "gamma": float(row.get("gamma", 0)),
                        "theta": float(row.get("theta", 0)),
                        "vega": float(row.get("vega", 0))
                    })
            
            response_data = {
                "symbol": ticker,
                "expirations": expirations,
                "current_expiration": first_exp,
                "calls": calls,
                "puts": puts,
                "call_count": len(calls),
                "put_count": len(puts)
            }

            return AgentResponse(
                success=True,
                data=response_data,
                source=self.name,
                metadata={"ticker": ticker, "type": "options", "expiration": first_exp}
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch options chain for {ticker}: {e}")
            return AgentResponse(
                success=False,
                error=f"Failed to fetch options chain: {str(e)}",
                source=self.name
            )