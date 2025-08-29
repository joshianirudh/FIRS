#!/usr/bin/env python3
"""
Simple configuration management for FIRS.
Reads all settings from config.json file.
"""
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file."""
    config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        print(f"⚠️  config.json not found at {config_path}")
        print("   Creating default config.json...")
        create_default_config(config_path)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Override with environment variables if they exist
        config = override_with_env_vars(config)
        
        return config
    
    except Exception as e:
        print(f"❌ Error loading config.json: {e}")
        print("   Using default configuration...")
        return get_default_config()


def override_with_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Override config values with environment variables."""
    # API Keys
    if os.getenv("ALPHA_VANTAGE_API_KEY"):
        config["api"]["alpha_vantage_key"] = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    if os.getenv("FINNHUB_API_KEY"):
        config["api"]["finnhub_key"] = os.getenv("FINNHUB_API_KEY")
    
    if os.getenv("YAHOO_FINANCE_API_KEY"):
        config["api"]["yahoo_finance_key"] = os.getenv("YAHOO_FINANCE_API_KEY")
    
    if os.getenv("WEB_SEARCH_API_KEY"):
        config["api"]["web_search_key"] = os.getenv("WEB_SEARCH_API_KEY")
    
    # LLM Settings
    if os.getenv("LLM_PROVIDER"):
        config["llm"]["provider"] = os.getenv("LLM_PROVIDER")
    
    if os.getenv("LLM_MODEL"):
        config["llm"]["model"] = os.getenv("LLM_MODEL")
    
    if os.getenv("LLM_TEMPERATURE"):
        try:
            config["llm"]["temperature"] = float(os.getenv("LLM_TEMPERATURE"))
        except ValueError:
            pass
    
    # System Settings
    if os.getenv("LOG_LEVEL"):
        config["system"]["log_level"] = os.getenv("LOG_LEVEL")
    
    if os.getenv("DEBUG_MODE"):
        config["system"]["debug_mode"] = os.getenv("DEBUG_MODE").lower() in ['true', '1', 'yes']
    
    return config


def create_default_config(config_path: Path):
    """Create a default config.json file."""
    default_config = {
        "llm": {
            "provider": "ollama",
            "model": "llama2",
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 30
        },
        "api": {
            "enabled_apis": ["alpha_vantage", "yahoo_finance", "finnhub", "web_search"],
            "alpha_vantage_key": None,
            "finnhub_key": None,
            "yahoo_finance_key": None,
            "web_search_key": None,
            "rate_limit_per_minute": 60,
            "concurrent_requests": 5,
            "request_timeout": 30,
            "connection_timeout": 10
        },
        "web_search": {
            "search_depth": "standard",
            "max_news_articles": 10,
            "max_expert_reports": 5,
            "news_days_back": 7,
            "preferred_news_sources": ["reuters", "bloomberg", "cnbc", "yahoo_finance"],
            "max_social_posts": 20
        },
        "report": {
            "include_executive_summary": True,
            "detail_level": "standard",
            "save_to_file": True,
            "output_format": "json",
            "include_charts": False,
            "max_report_length": 5000
        },
        "database": {
            "enable_vector_storage": False,
            "vector_dimension": 1536,
            "similarity_threshold": 0.8,
            "qdrant_url": "http://localhost:6333",
            "qdrant_api_key": None
        },
        "system": {
            "log_level": "INFO",
            "max_concurrent_requests": 10,
            "cache_enabled": True,
            "max_retries": 3,
            "debug_mode": False,
            "mock_data_fallback": True
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"✅ Created default config.json at {config_path}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "llm": {
            "provider": "ollama",
            "model": "llama2",
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 30
        },
        "api": {
            "enabled_apis": ["alpha_vantage", "yahoo_finance", "finnhub", "web_search"],
            "alpha_vantage_key": None,
            "finnhub_key": None,
            "yahoo_finance_key": None,
            "web_search_key": None,
            "rate_limit_per_minute": 60,
            "concurrent_requests": 5,
            "request_timeout": 30,
            "connection_timeout": 10
        },
        "web_search": {
            "search_depth": "standard",
            "max_news_articles": 10,
            "max_expert_reports": 5,
            "news_days_back": 7,
            "preferred_news_sources": ["reuters", "bloomberg", "cnbc", "yahoo_finance"],
            "max_social_posts": 20
        },
        "report": {
            "include_executive_summary": True,
            "detail_level": "standard",
            "save_to_file": True,
            "output_format": "json",
            "include_charts": False,
            "max_report_length": 5000
        },
        "database": {
            "enable_vector_storage": False,
            "vector_dimension": 1536,
            "similarity_threshold": 0.8,
            "qdrant_url": "http://localhost:6333",
            "qdrant_api_key": None
        },
        "system": {
            "log_level": "INFO",
            "max_concurrent_requests": 10,
            "cache_enabled": True,
            "max_retries": 3,
            "debug_mode": False,
            "mock_data_fallback": True
        }
    }


def is_api_enabled(config: Dict[str, Any], api_name: str) -> bool:
    """Check if a specific API is enabled."""
    return api_name in config.get("api", {}).get("enabled_apis", [])


def get_enabled_apis(config: Dict[str, Any]) -> List[str]:
    """Get list of enabled APIs."""
    return config.get("api", {}).get("enabled_apis", [])


def get_llm_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get LLM settings from config."""
    return config.get("llm", {})


def get_api_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get API settings from config."""
    return config.get("api", {})


def get_web_search_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get web search settings from config."""
    return config.get("web_search", {})


def get_report_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get report settings from config."""
    return config.get("report", {})


def get_database_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get database settings from config."""
    return config.get("database", {})


def get_system_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get system settings from config."""
    return config.get("system", {})


# Load configuration when module is imported
config = load_config()

# Convenience functions
def is_api_enabled_simple(api_name: str) -> bool:
    """Simple function to check if API is enabled."""
    return is_api_enabled(config, api_name)


def get_enabled_apis_simple() -> List[str]:
    """Simple function to get enabled APIs."""
    return get_enabled_apis(config)
