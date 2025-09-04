"""Financial Report Generator using LLM processing."""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .llm_adapter import LLMAdapter, LLMProvider
from .utils import (
    summarize_financial_data,
    summarize_news_data,
    analyze_market_sentiment,
    extract_key_insights,
    generate_executive_summary
)

logger = logging.getLogger(__name__)


class FinancialReportGenerator:
    """Main class for generating comprehensive financial reports."""
    
    def __init__(self, llm_provider: str = "ollama", **llm_kwargs):
        """
        Initialize the report generator.
        
        Args:
            llm_provider: LLM provider to use ("ollama" or "openai")
            **llm_kwargs: Additional LLM configuration
        """
        self.llm_adapter = None
        self.llm_provider = llm_provider
        self.llm_kwargs = llm_kwargs
        self.report_data = {}
        
        # Import config here to avoid circular imports
        from config import config
        self.config = config
    
    async def initialize(self):
        """Initialize the LLM adapter."""
        try:
            self.llm_adapter = await self._create_llm_adapter()
            logger.info(f"Initialized LLM adapter with {self.llm_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM adapter: {e}")
            raise
    
    async def _create_llm_adapter(self) -> LLMAdapter:
        """Create the LLM adapter."""
        try:
            provider_enum = LLMProvider(self.llm_provider.lower())
            
            # Get model name from config
            model_name = self.config["llm"]["model"]
            logger.info(f"Creating LLM adapter with provider {self.llm_provider} and model {model_name}")
            
            # Create adapter with model name
            return LLMAdapter(provider_enum, model=model_name, **self.llm_kwargs)
        except ValueError:
            raise ValueError(f"Unsupported provider: {self.llm_provider}. Supported: {[p.value for p in LLMProvider]}")
    
    async def generate_comprehensive_report(
        self,
        ticker: str,
        alpha_vantage_data: Dict[str, Any],
        finnhub_data: Dict[str, Any],
        yahoo_finance_data: Dict[str, Any],
        web_search_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive financial report for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            alpha_vantage_data: Data from Alpha Vantage API
            finnhub_data: Data from Finnhub API
            yahoo_finance_data: Data from Yahoo Finance API
            web_search_data: Optional data from web search agent
            
        Returns:
            Comprehensive financial report in JSON format
        """
        if not self.llm_adapter:
            await self.initialize()
        
        try:
            logger.info(f"Generating comprehensive report for {ticker}")
            
            # Step 1: Summarize financial data from all APIs
            logger.info("Step 1: Summarizing financial data...")
            financial_summary = await summarize_financial_data(
                ticker, alpha_vantage_data, finnhub_data, yahoo_finance_data, self.llm_adapter
            )
            
            # Step 2: Process web search data if available
            web_summaries = {}
            if web_search_data:
                print(f"Web search data: {web_search_data}")
                logger.info("Step 2: Processing web search data...")
                web_summaries = await self._process_web_search_data(ticker, web_search_data)
            
            # Step 3: Generate executive summary
            logger.info("Step 3: Generating executive summary...")
            all_summaries = {
                "financial": financial_summary,
                "web_data": web_summaries
            }
            executive_summary = await generate_executive_summary(ticker, all_summaries, self.llm_adapter)
            
            # Step 4: Compile final report
            logger.info("Step 4: Compiling final report...")
            final_report = self._compile_final_report(
                ticker, financial_summary, web_summaries, executive_summary
            )
            
            logger.info(f"Successfully generated comprehensive report for {ticker}")
            return final_report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {
                "error": f"Failed to generate report: {str(e)}",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_web_search_data(self, ticker: str, web_search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process web search data using LLM."""
        try:
            web_summaries = {}
            
            # Process news data
            if "latest_news" in web_search_data:
                logger.info("Processing news data...")
                news_summary = await summarize_news_data(
                    ticker, web_search_data["latest_news"], self.llm_adapter
                )
                web_summaries["news"] = news_summary
            
            # Process expert analysis
            if "expert_analysis" in web_search_data:
                logger.info("Processing expert analysis...")
                expert_summary = await extract_key_insights(
                    ticker, web_search_data["expert_analysis"], 
                    web_search_data.get("company_research", {}), self.llm_adapter
                )
                web_summaries["expert_insights"] = expert_summary
            
            # Process social media data
            if "social_discussions" in web_search_data:
                logger.info("Processing social media data...")
                social_sentiment = await analyze_market_sentiment(
                    ticker, web_search_data["social_discussions"], self.llm_adapter
                )
                web_summaries["social_sentiment"] = social_sentiment
            
            return web_summaries
            
        except Exception as e:
            logger.error(f"Error processing web search data: {e}")
            return {"error": str(e)}
    
    def _compile_final_report(
        self,
        ticker: str,
        financial_summary: Dict[str, Any],
        web_summaries: Dict[str, Any],
        executive_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile the final comprehensive report."""
        try:
            # Extract company info from financial data
            company_info = self._extract_company_info(financial_summary)
            
            # Compile financial section
            financial_section = self._compile_financial_section(financial_summary)
            
            # Compile news section
            news_section = self._compile_news_section(web_summaries)
            
            # Compile market sentiment section
            sentiment_section = self._compile_sentiment_section(web_summaries)
            
            # Create final report structure
            final_report = {
                "timestamp": datetime.now().isoformat(),
                "company": company_info,
                "ticker": ticker,
                "sector": company_info.get("sector", "Unknown"),
                "financial": financial_section,
                "latest_news": news_section,
                "market_sentiment": sentiment_section,
                "expert_analysis": web_summaries.get("expert_insights", {}),
                "executive_summary": executive_summary,
                "report_metadata": {
                    "generated_by": "Financial Intelligence System",
                    "llm_provider": self.llm_provider,
                    "data_sources": ["Alpha Vantage", "Finnhub", "Yahoo Finance", "Web Search"],
                    "processing_time": datetime.now().isoformat()
                }
            }
            
            return final_report
            
        except Exception as e:
            logger.error(f"Error compiling final report: {e}")
            return {"error": f"Failed to compile report: {str(e)}"}
    
    def _extract_company_info(self, financial_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Extract company information from financial summary."""
        company_info = {
            "name": "Unknown",
            "sector": "Unknown",
            "industry": "Unknown"
        }
        
        # Try to extract from different API summaries
        for api_name in ["alpha_vantage", "finnhub", "yahoo_finance"]:
            if api_name in financial_summary:
                api_data = financial_summary[api_name]
                if isinstance(api_data, dict) and "error" not in api_data:
                    # Extract company name if available
                    if "company_name" in api_data:
                        company_info["name"] = api_data["company_name"]
                    elif "name" in api_data:
                        company_info["name"] = api_data["name"]
                    
                    # Extract sector/industry if available
                    if "sector" in api_data:
                        company_info["sector"] = api_data["sector"]
                    if "industry" in api_data:
                        company_info["industry"] = api_data["industry"]
        
        return company_info
    
    def _compile_financial_section(self, financial_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Compile the financial section of the report."""
        financial_section = {
            "overview": financial_summary.get("combined_insights", []),
            "recommendation": financial_summary.get("overall_recommendation", "No recommendation"),
            "api_summaries": {
                "alpha_vantage": financial_summary.get("alpha_vantage", {}),
                "finnhub": financial_summary.get("finnhub", {}),
                "yahoo_finance": financial_summary.get("yahoo_finance", {})
            },
            "key_metrics": self._extract_key_metrics(financial_summary)
        }
        
        return financial_section
    
    def _extract_key_metrics(self, financial_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key financial metrics from all APIs."""
        key_metrics = {}
        
        # Extract price information
        for api_name in ["alpha_vantage", "finnhub", "yahoo_finance"]:
            if api_name in financial_summary:
                api_data = financial_summary[api_name]
                if isinstance(api_data, dict) and "error" not in api_data:
                    if "key_metrics" in api_data:
                        key_metrics[api_name] = api_data["key_metrics"]
        
        return key_metrics
    
    def _compile_news_section(self, web_summaries: Dict[str, Any]) -> Dict[str, Any]:
        """Compile the news section of the report."""
        if "news" in web_summaries:
            news_data = web_summaries["news"]
            if "error" not in news_data:
                return {
                    "summary": news_data.get("summary", "No news summary available"),
                    "sentiment": news_data.get("overall_sentiment", "neutral"),
                    "key_themes": news_data.get("key_themes", []),
                    "major_events": news_data.get("major_events", []),
                    "trending_topics": news_data.get("trending_topics", [])
                }
        
        return {
            "summary": "No news data available",
            "sentiment": "neutral",
            "key_themes": [],
            "major_events": [],
            "trending_topics": []
        }
    
    def _compile_sentiment_section(self, web_summaries: Dict[str, Any]) -> Dict[str, Any]:
        """Compile the market sentiment section of the report."""
        if "social_sentiment" in web_summaries:
            sentiment_data = web_summaries["social_sentiment"]
            if "error" not in sentiment_data:
                return {
                    "overall_sentiment": sentiment_data.get("overall_sentiment", "neutral"),
                    "sentiment_score": sentiment_data.get("sentiment_score", 0.5),
                    "key_topics": sentiment_data.get("key_topics", []),
                    "community_mood": sentiment_data.get("community_mood", "neutral"),
                    "trending_discussions": sentiment_data.get("trending_discussions", [])
                }
        
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.5,
            "key_topics": [],
            "community_mood": "neutral",
            "trending_discussions": []
        }
    
    async def test_llm_connection(self) -> bool:
        """Test if the LLM provider is accessible."""
        if not self.llm_adapter:
            await self.initialize()
        
        try:
            return await self.llm_adapter.test_connection()
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save the report to a JSON file."""
        try:
            if not filename:
                ticker = report.get("ticker", "unknown")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"financial_report_{ticker}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise
    
    async def generate_financial_report(self, ticker: str) -> Dict[str, Any]:
        """
        Generate a financial report by fetching data from all available sources.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Comprehensive financial report
        """
        try:
            if not self.llm_adapter:
                await self.initialize()
            
            logger.info(f"Fetching data for {ticker} from all sources...")
            
            # Import agents here to avoid circular imports
            from agents.alpha_vantage_agent import AlphaVantageAgent
            from agents.yahoo_finance_agent import YahooFinanceAgent
            from agents.finhub_agent import FinnhubAgent
            from agents.web_search_agent import WebSearchAgent
            
            # Fetch data from all sources concurrently
            tasks = [
                AlphaVantageAgent().fetch_stock_data(ticker),
                YahooFinanceAgent().fetch_stock_data(ticker),
                FinnhubAgent().fetch_stock_data(ticker),
                WebSearchAgent().fetch_latest_news(ticker)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract data from results
            alpha_vantage_data = results[0].data if not isinstance(results[0], Exception) and results[0].success else {}
            yahoo_finance_data = results[1].data if not isinstance(results[1], Exception) and results[1].success else {}
            finnhub_data = results[2].data if not isinstance(results[2], Exception) and results[2].success else {}
            web_search_data = results[3].data if not isinstance(results[3], Exception) and results[3].success else {}
            
            # Generate the comprehensive report
            report = await self.generate_comprehensive_report(
                ticker, alpha_vantage_data, finnhub_data, yahoo_finance_data, web_search_data
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating financial report for {ticker}: {e}")
            return {
                "error": f"Failed to generate report: {str(e)}",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }


# Convenience function for easy usage
async def generate_financial_report(
    ticker: str,
    alpha_vantage_data: Dict[str, Any],
    finnhub_data: Dict[str, Any],
    yahoo_finance_data: Dict[str, Any],
    web_search_data: Optional[Dict[str, Any]] = None,
    llm_provider: str = "ollama",
    save_to_file: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to generate a financial report.
    
    Args:
        ticker: Stock ticker symbol
        alpha_vantage_data: Data from Alpha Vantage API
        finnhub_data: Data from Finnhub API
        yahoo_finance_data: Data from Yahoo Finance API
        web_search_data: Optional data from web search agent
        llm_provider: LLM provider to use
        save_to_file: Whether to save the report to a file
        
    Returns:
        Comprehensive financial report
    """
    try:
        generator = FinancialReportGenerator(llm_provider=llm_provider)
        await generator.initialize()
        
        report = await generator.generate_comprehensive_report(
            ticker, alpha_vantage_data, finnhub_data, yahoo_finance_data, web_search_data
        )
        
        if save_to_file and "error" not in report:
            generator.save_report(report)
        
        return report
        
    except Exception as e:
        logger.error(f"Error in generate_financial_report: {e}")
        return {"error": str(e)}
