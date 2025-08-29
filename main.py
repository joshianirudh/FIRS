#!/usr/bin/env python3
"""
Main entry point for the Financial Intelligence System.
Demonstrates API testing and data fetching capabilities.

Usage:
    python main.py                    # Test APIs and generate report for AAPL
    python main.py TSLA              # Test APIs and generate report for TSLA
    python main.py --report-only     # Generate report only for AAPL
    python main.py --report-only MSFT # Generate report only for MSFT
"""
import asyncio
import json
import logging
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta

from agents.alpha_vantage_agent import AlphaVantageAgent
from agents.yahoo_finance_agent import YahooFinanceAgent
from agents.finhub_agent import FinnhubAgent
from agents.web_search_agent import WebSearchAgent
from preprocessing.create_report import FinancialReportGenerator
from config import config


# Configure logging
logging.basicConfig(
    level=getattr(logging, config["system"]["log_level"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_agent(agent, ticker: str, test_name: str) -> Dict[str, Any]:
    """Test a single agent with various data fetching methods."""
    logger.info(f"Testing {test_name} with ticker: {ticker}")
    
    results = {
        "agent": test_name,
        "ticker": ticker,
        "tests": {},
        "errors": []
    }
    
    try:
        # Test stock data
        logger.info(f"  Fetching stock data...")
        stock_response = await agent.fetch_stock_data(ticker)
        if stock_response.success:
            results["tests"]["stock_data"] = {
                "success": True,
                "data": stock_response.data,
                "source": stock_response.source
            }
        else:
            results["tests"]["stock_data"] = {
                "success": False,
                "error": stock_response.error
            }
            results["errors"].append(f"Stock data: {stock_response.error}")
    
    except Exception as e:
        logger.error(f"  Error testing stock data: {e}")
        results["tests"]["stock_data"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Stock data exception: {e}")
    
    try:
        # Test company info
        logger.info(f"  Fetching company info...")
        company_response = await agent.fetch_company_info(ticker)
        if company_response.success:
            results["tests"]["company_info"] = {
                "success": True,
                "data": company_response.data,
                "source": company_response.source
            }
        else:
            results["tests"]["company_info"] = {
                "success": False,
                "error": company_response.error
            }
            results["errors"].append(f"Company info: {company_response.error}")
    
    except Exception as e:
        logger.error(f"  Error testing company info: {e}")
        results["tests"]["company_info"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Company info exception: {e}")
    
    try:
        # Test historical data
        logger.info(f"  Fetching historical data...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        historical_response = await agent.fetch_historical_data(ticker, start_date, end_date)
        if historical_response.success:
            results["tests"]["historical_data"] = {
                "success": True,
                "data": historical_response.data,
                "source": historical_response.source
            }
        else:
            results["tests"]["historical_data"] = {
                "success": False,
                "error": historical_response.error
            }
            results["errors"].append(f"Historical data: {historical_response.error}")
    
    except Exception as e:
        logger.error(f"  Error testing historical data: {e}")
        results["tests"]["historical_data"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Historical data exception: {e}")
    
    # Test agent-specific methods
    if hasattr(agent, 'fetch_earnings'):
        try:
            logger.info(f"  Fetching earnings data...")
            earnings_response = await agent.fetch_earnings(ticker)
            if earnings_response.success:
                results["tests"]["earnings"] = {
                    "success": True,
                    "data": earnings_response.data,
                    "source": earnings_response.source
                }
            else:
                results["tests"]["earnings"] = {
                    "success": False,
                    "error": earnings_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing earnings: {e}")
            results["tests"]["earnings"] = {"success": False, "error": str(e)}
    
    if hasattr(agent, 'fetch_news'):
        try:
            logger.info(f"  Fetching news data...")
            news_response = await agent.fetch_news(ticker, days_back=7)
            if news_response.success:
                results["tests"]["news"] = {
                    "success": True,
                    "data": news_response.data,
                    "source": news_response.source
                }
            else:
                results["tests"]["news"] = {
                    "success": False,
                    "error": news_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing news: {e}")
            results["tests"]["news"] = {"success": False, "error": str(e)}
    
    if hasattr(agent, 'fetch_options_chain'):
        try:
            logger.info(f"  Fetching options chain...")
            options_response = await agent.fetch_options_chain(ticker)
            if options_response.success:
                results["tests"]["options"] = {
                    "success": True,
                    "data": options_response.data,
                    "source": options_response.source
                }
            else:
                results["tests"]["options"] = {
                    "success": False,
                    "error": options_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing options: {e}")
            results["tests"]["options"] = {"success": False, "error": str(e)}
    
    # Test WebSearchAgent specific methods
    if hasattr(agent, 'fetch_expert_analysis'):
        try:
            logger.info(f"  Fetching expert analysis...")
            analysis_response = await agent.fetch_expert_analysis(ticker)
            if analysis_response.success:
                results["tests"]["expert_analysis"] = {
                    "success": True,
                    "data": analysis_response.data,
                    "source": analysis_response.source
                }
            else:
                results["tests"]["expert_analysis"] = {
                    "success": False,
                    "error": analysis_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing expert analysis: {e}")
            results["tests"]["expert_analysis"] = {"success": False, "error": str(e)}
    
    if hasattr(agent, 'fetch_latest_news'):
        try:
            logger.info(f"  Fetching latest news...")
            news_response = await agent.fetch_latest_news(ticker, days_back=7)
            if news_response.success:
                results["tests"]["latest_news"] = {
                    "success": True,
                    "data": news_response.data,
                    "source": news_response.source
                }
            else:
                results["tests"]["news"] = {
                    "success": False,
                    "error": news_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing latest news: {e}")
            results["tests"]["latest_news"] = {"success": False, "error": str(e)}
    
    if hasattr(agent, 'fetch_company_research'):
        try:
            logger.info(f"  Fetching company research...")
            research_response = await agent.fetch_company_research(ticker)
            if research_response.success:
                results["tests"]["company_research"] = {
                    "success": True,
                    "data": research_response.data,
                    "source": research_response.source
                }
            else:
                results["tests"]["company_research"] = {
                    "success": False,
                    "error": research_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing company research: {e}")
            results["tests"]["company_research"] = {"success": False, "error": str(e)}
    
    if hasattr(agent, 'fetch_social_discussions'):
        try:
            logger.info(f"  Fetching social discussions...")
            social_response = await agent.fetch_social_discussions(ticker)
            if social_response.success:
                results["tests"]["social_discussions"] = {
                    "success": True,
                    "data": social_response.data,
                    "source": social_response.source
                }
            else:
                results["tests"]["social_discussions"] = {
                    "success": False,
                    "error": social_response.error
                }
        except Exception as e:
            logger.error(f"  Error testing social discussions: {e}")
            results["tests"]["social_discussions"] = {"success": False, "error": str(e)}
    
    return results


async def test_all_agents(ticker: str) -> List[Dict[str, Any]]:
    """Test all available agents concurrently."""
    logger.info(f"Starting comprehensive API testing for ticker: {ticker}")
    
    # Initialize agents based on configuration
    agents = []
    
    if config["api"]["enabled_apis"]:
        if "alpha_vantage" in config["api"]["enabled_apis"]:
            agents.append((AlphaVantageAgent(), "Alpha Vantage"))
        
        if "yahoo_finance" in config["api"]["enabled_apis"]:
            agents.append((YahooFinanceAgent(), "Yahoo Finance"))
        
        if "finnhub" in config["api"]["enabled_apis"]:
            agents.append((FinnhubAgent(), "Finnhub"))
        
        if "web_search" in config["api"]["enabled_apis"]:
            agents.append((WebSearchAgent(), "Web Search"))
    
    if not agents:
        logger.warning("No APIs enabled in configuration. Using all agents.")
        agents = [
            (AlphaVantageAgent(), "Alpha Vantage"),
            (YahooFinanceAgent(), "Yahoo Finance"),
            (FinnhubAgent(), "Finnhub"),
            (WebSearchAgent(), "Web Search")
        ]
    
    # Test all agents concurrently
    tasks = [test_single_agent(agent, ticker, name) for agent, name in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions from gather
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Agent {agents[i][1]} failed with exception: {result}")
            processed_results.append({
                "agent": agents[i][1],
                "ticker": ticker,
                "error": f"Agent initialization failed: {result}",
                "tests": {},
                "errors": [str(result)]
            })
        else:
            processed_results.append(result)
    
    return processed_results


def print_results(results: List[Dict[str, Any]]):
    """Print test results in a formatted way."""
    print("\n" + "="*80)
    print("FINANCIAL API TESTING RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\n{result['agent']} - {result['ticker']}")
        print("-" * 50)
        
        if "error" in result:
            print(f"❌ Agent Error: {result['error']}")
            continue
        
        success_count = 0
        total_tests = len(result["tests"])
        
        for test_name, test_result in result["tests"].items():
            if test_result["success"]:
                print(f"✅ {test_name}: Success")
                success_count += 1
            else:
                print(f"❌ {test_name}: {test_result.get('error', 'Unknown error')}")
        
        print(f"\n📊 Summary: {success_count}/{total_tests} tests passed")
        
        if result["errors"]:
            print(f"⚠️  Errors encountered: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"   - {error}")


def check_api_keys():
    """Check which API keys are configured."""
    print("\n🔑 API KEY STATUS")
    print("-" * 30)
    
    # Show enabled APIs
    enabled_apis = config["api"]["enabled_apis"]
    print(f"📋 Enabled APIs: {', '.join(enabled_apis)}")
    print()
    
    keys_status = {
        "Alpha Vantage": config["api"]["alpha_vantage_key"] is not None,
        "Yahoo Finance": "No API key needed (yfinance library)",
        "Finnhub": config["api"]["finnhub_key"] is not None,
        "Web Search": "Optional - uses web scraping"
    }
    
    for service, status in keys_status.items():
        if isinstance(status, bool):
            display_status = "✅ Configured" if status else "❌ Not configured"
        else:
            display_status = f"ℹ️  {status}"
        print(f"{service}: {display_status}")
    
    # Check if we have at least one real API key
    has_real_api = (config["api"]["alpha_vantage_key"] is not None or 
                    config["api"]["finnhub_key"] is not None)
    
    if not has_real_api:
        print("\n⚠️  No real API keys configured. Using mock data for all tests.")
        print("   Set environment variables to test real APIs:")
        print("   - ALPHA_VANTAGE_API_KEY")
        print("   - FINNHUB_API_KEY")
        print("   - YAHOO_FINANCE_API_KEY (optional - not needed for yfinance)")
    else:
        print("\n✅ Some real APIs configured. Mix of real and mock data will be used.")
    
    # Show configuration details
    print(f"\n⚙️  Configuration:")
    print(f"   LLM Provider: {config['llm']['provider']}")
    print(f"   LLM Model: {config['llm']['model']}")
    print(f"   Web Search Depth: {config['web_search']['search_depth']}")
    print(f"   Report Detail: {config['report']['detail_level']}")


async def generate_comprehensive_report(ticker: str) -> Dict[str, Any]:
    """Generate a comprehensive financial report using the preprocessing package."""
    logger.info(f"Generating comprehensive report for {ticker}")
    
    try:
        # Initialize the report generator
        report_generator = FinancialReportGenerator()
        
        # Generate the comprehensive report
        report = await report_generator.generate_financial_report(ticker)
        
        logger.info(f"✅ Report generated successfully for {ticker}")
        return report
        
    except Exception as e:
        logger.error(f"❌ Error generating report for {ticker}: {e}")
        return {
            "error": f"Failed to generate report: {str(e)}",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """Main entry point."""
    print("🚀 Financial Intelligence System - API Testing & Report Generation")
    print("=" * 60)
    
    # Check API key configuration
    check_api_keys()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--report-only":
            # Report-only mode
            if len(sys.argv) > 2:
                ticker = sys.argv[2].upper()
            else:
                ticker = "AAPL"  # Default to Apple
            
            print(f"\n📊 REPORT-ONLY MODE for ticker: {ticker}")
            print("=" * 50)
            
            try:
                report = await generate_comprehensive_report(ticker)
                
                if "error" not in report:
                    print("✅ Report generated successfully!")
                    print("\n📋 COMPREHENSIVE FINANCIAL REPORT")
                    print("=" * 50)
                    
                    # Pretty print the JSON report
                    print(json.dumps(report, indent=2, default=str))
                    
                    # Save report to file if configured
                    if config["report"]["save_to_file"]:
                        filename = f"financial_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(filename, 'w') as f:
                            json.dump(report, f, indent=2, default=str)
                        print(f"\n💾 Report saved to: {filename}")
                    
                else:
                    print(f"❌ Report generation failed: {report['error']}")
                    
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                print(f"❌ Report generation error: {e}")
                sys.exit(1)
            
            return
        
        else:
            # Normal API testing mode
            ticker = sys.argv[1].upper()
    else:
        ticker = "AAPL"  # Default to Apple
    
    print(f"\n📈 Testing APIs with ticker: {ticker}")
    
    try:
        # Test all agents
        results = await test_all_agents(ticker)
        
        # Print results
        print_results(results)
        
        # Summary
        total_agents = len(results)
        successful_agents = sum(1 for r in results if "error" not in r)
        print(f"\n🎯 FINAL SUMMARY: {successful_agents}/{total_agents} agents working")
        
        if successful_agents == total_agents:
            print("🎉 All agents are working correctly!")
        else:
            print("⚠️  Some agents encountered issues. Check the logs above.")
        
        # Generate comprehensive report
        print(f"\n📊 GENERATING COMPREHENSIVE REPORT FOR {ticker}")
        print("=" * 60)
        
        try:
            report = await generate_comprehensive_report(ticker)
            
            if "error" not in report:
                print("✅ Report generated successfully!")
                print("\n📋 COMPREHENSIVE FINANCIAL REPORT")
                print("=" * 50)
                
                # Pretty print the JSON report
                print(json.dumps(report, indent=2, default=str))
                
                # Save report to file if configured
                if config["report"]["save_to_file"]:
                    filename = f"financial_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w') as f:
                        json.dump(report, f, indent=2, default=str)
                    print(f"\n💾 Report saved to: {filename}")
                
            else:
                print(f"❌ Report generation failed: {report['error']}")
                
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            print(f"❌ Report generation error: {e}")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ System error: {e}")
        sys.exit(1)
    
    finally:
        # Clean up any resources
        logger.info("API testing completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
