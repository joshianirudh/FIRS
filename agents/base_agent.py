"""Base agent abstract class for financial data sources."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Standardized response from agents."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: str = ""
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Abstract base class for all financial data agents."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            api_key: API key for the data source
        """
        self.api_key = api_key
        self.name = self.__class__.__name__
        self.base_url = ""
        self.rate_limit = 5  # requests per second
        self._session = None

    @abstractmethod
    async def fetch_stock_data(self, ticker: str, **kwargs) -> AgentResponse:
        """
        Fetch stock data for a given ticker.

        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters specific to the data source

        Returns:
            AgentResponse containing the fetched data
        """
        pass

    @abstractmethod
    async def fetch_historical_data(
            self,
            ticker: str,
            start_date: str,
            end_date: str,
            **kwargs
    ) -> AgentResponse:
        """
        Fetch historical data for a given ticker and date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            **kwargs: Additional parameters

        Returns:
            AgentResponse containing historical data
        """
        pass

    @abstractmethod
    async def fetch_company_info(self, ticker: str) -> AgentResponse:
        """
        Fetch company information for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AgentResponse containing company information
        """
        pass

    def validate_ticker(self, ticker: str) -> bool:
        """Validate ticker format."""
        if not ticker or not isinstance(ticker, str):
            return False
        return len(ticker) <= 5 and ticker.isalpha()

    def handle_error(self, error: Exception, context: str = "") -> AgentResponse:
        """
        Standard error handling for agents.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred

        Returns:
            AgentResponse with error information
        """
        error_msg = f"Error in {self.name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"

        logger.error(error_msg)
        return AgentResponse(
            success=False,
            error=error_msg,
            source=self.name
        )

    async def close(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()