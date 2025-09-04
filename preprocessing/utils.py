"""Utility functions for LLM-based data processing and summarization."""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .llm_adapter import LLMAdapter, LLMProvider

logger = logging.getLogger(__name__)


# Financial Data Summarization Prompts
ALPHA_VANTAGE_SUMMARY_PROMPT = """
Analyze the following Alpha Vantage financial data for {ticker} and provide a concise summary.

Data: {data}

Please provide a JSON response with the following structure:
{{
    "summary": "Brief overview of key financial metrics",
    "key_metrics": {{
        "price": "Current price analysis",
        "volume": "Volume analysis",
        "change": "Price change analysis"
    }},
    "insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
    "risk_factors": ["Risk factor 1", "Risk factor 2"],
    "recommendation": "Buy/Hold/Sell recommendation with brief reasoning"
}}
"""

FINNHUB_SUMMARY_PROMPT = """
Analyze the following Finnhub financial data for {ticker} and provide a concise summary.

Data: {data}

Please provide a JSON response with the following structure:
{{
    "summary": "Brief overview of key financial metrics",
    "key_metrics": {{
        "current_price": "Current price analysis",
        "day_range": "Day high/low analysis",
        "volume": "Volume analysis"
    }},
    "insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
    "risk_factors": ["Risk factor 1", "Risk factor 2"],
    "recommendation": "Buy/Hold/Sell recommendation with brief reasoning"
}}
"""

YAHOO_FINANCE_SUMMARY_PROMPT = """
Analyze the following Yahoo Finance data for {ticker} and provide a concise summary.

Data: {data}

Please provide a JSON response with the following structure:
{{
    "summary": "Brief overview of key financial metrics",
    "key_metrics": {{
        "price": "Current price analysis",
        "market_cap": "Market cap analysis",
        "pe_ratios": "P/E ratio analysis",
        "beta": "Beta analysis"
    }},
    "insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
    "risk_factors": ["Risk factor 1", "Risk factor 2"],
    "recommendation": "Buy/Hold/Sell recommendation with brief reasoning"
}}
"""

# News Summarization Prompts
NEWS_SUMMARY_PROMPT = """
Analyze the following news articles about {ticker} and provide a comprehensive summary.

News Data: {data}

Please provide a JSON response with the following structure:
{{
    "overall_sentiment": "positive/negative/neutral",
    "key_themes": ["Theme 1", "Theme 2", "Theme 3"],
    "major_events": [
        {{
            "event": "Description of major event",
            "impact": "positive/negative/neutral",
            "date": "Event date if available"
        }}
    ],
    "market_impact": "How these news items might affect the stock",
    "trending_topics": ["Topic 1", "Topic 2", "Topic 3"],
    "summary": "Overall news summary in 2-3 sentences"
}}
"""

# Expert Analysis Summarization Prompts
EXPERT_ANALYSIS_PROMPT = """
Analyze the following expert analysis and research reports for {ticker} and provide a summary.

Expert Analysis Data: {data}

Please provide a JSON response with the following structure:
{{
    "consensus_rating": "Overall analyst consensus",
    "price_targets": {{
        "average": "Average price target analysis",
        "range": "Price target range analysis",
        "upside_potential": "Upside potential percentage"
    }},
    "key_analyst_opinions": [
        {{
            "firm": "Analyst firm name",
            "rating": "Rating given",
            "key_points": ["Point 1", "Point 2"]
        }}
    ],
    "investment_thesis": "Main investment argument",
    "risks_mentioned": ["Risk 1", "Risk 2", "Risk 3"],
    "summary": "Overall expert analysis summary"
}}
"""

# Company Research Summarization Prompts
COMPANY_RESEARCH_PROMPT = """
Analyze the following company research data for {ticker} and provide a comprehensive summary.

Company Research Data: {data}

Please provide a JSON response with the following structure:
{{
    "business_model": "Summary of business model",
    "competitive_position": "Market position and competitive advantages",
    "growth_strategy": "Key growth initiatives and strategy",
    "risk_factors": ["Risk 1", "Risk 2", "Risk 3"],
    "industry_outlook": "Industry trends and outlook",
    "financial_strength": "Assessment of financial health",
    "summary": "Overall company assessment"
}}
"""

# Social Media Sentiment Prompts
SOCIAL_SENTIMENT_PROMPT = """
Analyze the following social media discussions about {ticker} and provide sentiment analysis.

Social Media Data: {data}

Please provide a JSON response with the following structure:
{{
    "overall_sentiment": "positive/negative/neutral",
    "sentiment_score": "0.0 to 1.0 score",
    "key_topics": ["Topic 1", "Topic 2", "Topic 3"],
    "influencer_impact": "Assessment of influential posts",
    "community_mood": "Overall community sentiment",
    "trending_discussions": ["Discussion 1", "Discussion 2"],
    "summary": "Social media sentiment summary"
}}
"""


async def summarize_financial_data(
    ticker: str, 
    alpha_vantage_data: Dict[str, Any],
    finnhub_data: Dict[str, Any], 
    yahoo_finance_data: Dict[str, Any],
    llm_adapter: LLMAdapter
) -> Dict[str, Any]:
    """
    Summarize financial data from multiple APIs using LLM.
    
    Args:
        ticker: Stock ticker symbol
        alpha_vantage_data: Data from Alpha Vantage API
        finnhub_data: Data from Finnhub API
        yahoo_finance_data: Data from Yahoo Finance API
        llm_adapter: LLM adapter instance
        
    Returns:
        Dictionary with summarized financial information
    """
    try:
        # Summarize each API's data separately
        tasks = [
            _summarize_alpha_vantage(ticker, alpha_vantage_data, llm_adapter),
            _summarize_finnhub(ticker, finnhub_data, llm_adapter),
            _summarize_yahoo_finance(ticker, yahoo_finance_data, llm_adapter)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        summaries = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error summarizing data from API {i}: {result}")
                summaries[f"api_{i}"] = {"error": str(result)}
            else:
                summaries[f"api_{i}"] = result
        
        # Combine summaries
        combined_summary = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "alpha_vantage": summaries.get("api_0", {}),
            "finnhub": summaries.get("api_1", {}),
            "yahoo_finance": summaries.get("api_2", {}),
            "combined_insights": _extract_common_insights(summaries),
            "overall_recommendation": _generate_overall_recommendation(summaries)
        }
        
        return combined_summary
        
    except Exception as e:
        logger.error(f"Error in summarize_financial_data: {e}")
        return {"error": str(e)}


async def _summarize_alpha_vantage(ticker: str, data: Dict[str, Any], llm_adapter: LLMAdapter) -> Dict[str, Any]:
    """Summarize Alpha Vantage data."""
    try:
        prompt = ALPHA_VANTAGE_SUMMARY_PROMPT.format(ticker=ticker, data=json.dumps(data, indent=2))
        return await llm_adapter.generate_json(prompt, temperature=0.3, timeout=120)
    except Exception as e:
        logger.error(f"Error summarizing Alpha Vantage data: {e}")
        return {"error": str(e)}


async def _summarize_finnhub(ticker: str, data: Dict[str, Any], llm_adapter: LLMAdapter) -> Dict[str, Any]:
    """Summarize Finnhub data."""
    try:
        prompt = FINNHUB_SUMMARY_PROMPT.format(ticker=ticker, data=json.dumps(data, indent=2))
        return await llm_adapter.generate_json(prompt, temperature=0.3, timeout=120)
    except Exception as e:
        logger.error(f"Error summarizing Finnhub data: {e}")
        return {"error": str(e)}


async def _summarize_yahoo_finance(ticker: str, data: Dict[str, Any], llm_adapter: LLMAdapter) -> Dict[str, Any]:
    """Summarize Yahoo Finance data."""
    try:
        prompt = YAHOO_FINANCE_SUMMARY_PROMPT.format(ticker=ticker, data=json.dumps(data, indent=2))
        return await llm_adapter.generate_json(prompt, temperature=0.3, timeout=120)
    except Exception as e:
        logger.error(f"Error summarizing Yahoo Finance data: {e}")
        return {"error": str(e)}


async def summarize_news_data(ticker: str, news_data: Dict[str, Any], llm_adapter: LLMAdapter) -> Dict[str, Any]:
    """
    Summarize news data using LLM.
    
    Args:
        ticker: Stock ticker symbol
        news_data: News data from web search agent
        llm_adapter: LLM adapter instance
        
    Returns:
        Dictionary with summarized news information
    """
    try:
        prompt = NEWS_SUMMARY_PROMPT.format(ticker=ticker, data=json.dumps(news_data, indent=2))
        return await llm_adapter.generate_json(prompt, temperature=0.4, timeout=120)
    except Exception as e:
        logger.error(f"Error summarizing news data: {e}")
        return {"error": str(e)}


async def analyze_market_sentiment(
    ticker: str, 
    social_data: Dict[str, Any], 
    llm_adapter: LLMAdapter
) -> Dict[str, Any]:
    """
    Analyze market sentiment from social media data.
    
    Args:
        ticker: Stock ticker symbol
        social_data: Social media data from web search agent
        llm_adapter: LLM adapter instance
        
    Returns:
        Dictionary with sentiment analysis
    """
    try:
        prompt = SOCIAL_SENTIMENT_PROMPT.format(ticker=ticker, data=json.dumps(social_data, indent=2))
        return await llm_adapter.generate_json(prompt, temperature=0.4, timeout=120)
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {e}")
        return {"error": str(e)}


async def extract_key_insights(
    ticker: str, 
    expert_analysis: Dict[str, Any], 
    company_research: Dict[str, Any],
    llm_adapter: LLMAdapter
) -> Dict[str, Any]:
    """
    Extract key insights from expert analysis and company research.
    
    Args:
        ticker: Stock ticker symbol
        expert_analysis: Expert analysis data
        company_research: Company research data
        llm_adapter: LLM adapter instance
        
    Returns:
        Dictionary with key insights
    """
    try:
        # Summarize expert analysis
        expert_prompt = EXPERT_ANALYSIS_PROMPT.format(ticker=ticker, data=json.dumps(expert_analysis, indent=2))
        expert_summary = await llm_adapter.generate_json(expert_prompt, temperature=0.3, timeout=120)
        
        # Summarize company research
        research_prompt = COMPANY_RESEARCH_PROMPT.format(ticker=ticker, data=json.dumps(company_research, indent=2))
        research_summary = await llm_adapter.generate_json(research_prompt, temperature=0.3, timeout=120)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "expert_analysis": expert_summary,
            "company_research": research_summary,
            "combined_insights": _extract_common_insights({
                "expert": expert_summary,
                "research": research_summary
            })
        }
        
    except Exception as e:
        logger.error(f"Error extracting key insights: {e}")
        return {"error": str(e)}


async def generate_executive_summary(
    ticker: str, 
    all_summaries: Dict[str, Any], 
    llm_adapter: LLMAdapter
) -> Dict[str, Any]:
    """
    Generate an executive summary from all data summaries.
    
    Args:
        ticker: Stock ticker symbol
        all_summaries: All summarized data
        llm_adapter: LLM adapter instance
        
    Returns:
        Dictionary with executive summary
    """
    try:
        executive_prompt = f"""
        Create an executive summary for {ticker} based on the following comprehensive analysis:

        {json.dumps(all_summaries, indent=2)}

        Please provide a JSON response with:
        {{
            "executive_summary": "2-3 sentence high-level overview",
            "key_investment_points": ["Point 1", "Point 2", "Point 3"],
            "risk_assessment": "Overall risk level and key risks",
            "investment_recommendation": "Clear buy/hold/sell recommendation with reasoning",
            "time_horizon": "Recommended investment time horizon",
            "confidence_level": "High/Medium/Low confidence in recommendation"
        }}
        """
        
        return await llm_adapter.generate_json(executive_prompt, temperature=0.2, timeout=120)
        
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        return {"error": str(e)}


def _extract_common_insights(summaries: Dict[str, Any]) -> List[str]:
    """Extract common insights across different summaries."""
    # This is a simple implementation - could be enhanced with LLM
    common_insights = []
    
    # Look for common themes in recommendations and insights
    all_text = json.dumps(summaries).lower()
    
    if "growth" in all_text:
        common_insights.append("Growth potential identified across multiple sources")
    if "risk" in all_text:
        common_insights.append("Risk factors mentioned consistently")
    if "positive" in all_text:
        common_insights.append("Generally positive outlook")
    if "negative" in all_text:
        common_insights.append("Some negative factors identified")
    
    return common_insights


def _generate_overall_recommendation(summaries: Dict[str, Any]) -> str:
    """Generate overall recommendation based on individual summaries."""
    # Simple logic - could be enhanced with LLM
    buy_count = 0
    hold_count = 0
    sell_count = 0
    
    all_text = json.dumps(summaries).lower()
    
    if "buy" in all_text:
        buy_count += all_text.count("buy")
    if "hold" in all_text:
        hold_count += all_text.count("hold")
    if "sell" in all_text:
        sell_count += all_text.count("sell")
    
    if buy_count > hold_count and buy_count > sell_count:
        return "BUY - Multiple sources recommend buying"
    elif sell_count > buy_count and sell_count > hold_count:
        return "SELL - Multiple sources recommend selling"
    else:
        return "HOLD - Mixed recommendations, consider holding"


async def ticker_to_company_name(ticker: str, llm_adapter=None) -> str:
    """
    Convert a stock ticker to company name using LLM.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        llm_adapter: LLM adapter instance for conversion
        
    Returns:
        Company name (e.g., 'Apple Inc.')
    """
    if not llm_adapter:
        from .llm_adapter import create_llm_adapter
        llm_adapter = await create_llm_adapter()
    
    prompt = f"""
    Convert the stock ticker '{ticker}' to its full company name.
    Respond with only the company name, nothing else.
    Examples:
    - AAPL -> Apple Inc.
    - MSFT -> Microsoft Corporation
    - TSLA -> Tesla Inc.
    - GOOGL -> Alphabet Inc.
    """
    
    try:
        company_name = await llm_adapter.generate_text(prompt, temperature=0.1)
        # Clean up the response
        company_name = company_name.strip().replace('"', '').replace("'", "")
        return company_name
    except Exception as e:
        logger.warning(f"Failed to convert ticker {ticker} to company name: {e}")
        # Fallback to ticker if LLM fails
        return ticker
