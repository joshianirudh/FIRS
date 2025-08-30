#!/usr/bin/env python3
"""
Simple Configuration Management Script for FIRS
Allows you to easily modify config.json file.
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class SimpleConfigManager:
    """Simple configuration manager that works with config.json."""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / "config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json file."""
        if not self.config_path.exists():
            print(f"⚠️  config.json not found at {self.config_path}")
            print("   Creating default config.json...")
            self.create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config.json: {e}")
            return self.get_default_config()
    
    def save_config(self):
        """Save current configuration to config.json file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"❌ Error saving config.json: {e}")
    
    def show_current_config(self):
        """Display current configuration."""
        print("\n🔧 CURRENT CONFIGURATION")
        print("=" * 50)
        
        # LLM Configuration
        print("\n🧠 LLM Configuration:")
        print(f"   Provider: {self.config['llm']['provider']}")
        print(f"   Model: {self.config['llm']['model']}")
        print(f"   Temperature: {self.config['llm']['temperature']}")
        print(f"   Max Tokens: {self.config['llm']['max_tokens']}")
        
        # API Configuration
        print("\n🌐 API Configuration:")
        print(f"   Enabled APIs: {', '.join(self.config['api']['enabled_apis'])}")
        print(f"   Rate Limit: {self.config['api']['rate_limit_per_minute']} req/min")
        print(f"   Concurrent Requests: {self.config['api']['concurrent_requests']}")
        
        # Web Search Configuration
        print("\n🔍 Web Search Configuration:")
        print(f"   Search Depth: {self.config['web_search']['search_depth']}")
        print(f"   Max News Articles: {self.config['web_search']['max_news_articles']}")
        print(f"   Max Expert Reports: {self.config['web_search']['max_expert_reports']}")
        
        # Report Configuration
        print("\n📊 Report Configuration:")
        print(f"   Detail Level: {self.config['report']['detail_level']}")
        print(f"   Include Executive Summary: {self.config['report']['include_executive_summary']}")
        print(f"   Save to File: {self.config['report']['save_to_file']}")
        
        # System Configuration
        print("\n⚙️  System Configuration:")
        print(f"   Log Level: {self.config['system']['log_level']}")
        print(f"   Debug Mode: {self.config['system']['debug_mode']}")
        print(f"   Mock Data Fallback: {self.config['system']['mock_data_fallback']}")
    
    def update_llm_config(self, provider: str = None, model: str = None, 
                          temperature: float = None, max_tokens: int = None):
        """Update LLM configuration."""
        if provider:
            self.config['llm']['provider'] = provider
            print(f"✅ LLM Provider updated to: {provider}")
        
        if model:
            self.config['llm']['model'] = model
            print(f"✅ LLM Model updated to: {model}")
        
        if temperature is not None:
            self.config['llm']['temperature'] = temperature
            print(f"✅ Temperature updated to: {temperature}")
        
        if max_tokens:
            self.config['llm']['max_tokens'] = max_tokens
            print(f"✅ Max Tokens updated to: {max_tokens}")
    
    def update_api_config(self, enabled_apis: list = None, rate_limit: int = None,
                         concurrent_requests: int = None):
        """Update API configuration."""
        if enabled_apis:
            self.config['api']['enabled_apis'] = enabled_apis
            print(f"✅ Enabled APIs updated to: {enabled_apis}")
        
        if rate_limit:
            self.config['api']['rate_limit_per_minute'] = rate_limit
            print(f"✅ Rate limit updated to: {rate_limit} req/min")
        
        if concurrent_requests:
            self.config['api']['concurrent_requests'] = concurrent_requests
            print(f"✅ Concurrent requests updated to: {concurrent_requests}")
    
    def update_web_search_config(self, search_depth: str = None, 
                                max_news: int = None, max_expert: int = None):
        """Update web search configuration."""
        if search_depth:
            self.config['web_search']['search_depth'] = search_depth
            print(f"✅ Search depth updated to: {search_depth}")
        
        if max_news:
            self.config['web_search']['max_news_articles'] = max_news
            print(f"✅ Max news articles updated to: {max_news}")
        
        if max_expert:
            self.config['web_search']['max_expert_reports'] = max_expert
            print(f"✅ Max expert reports updated to: {max_expert}")
    
    def update_report_config(self, detail_level: str = None, 
                           include_summary: bool = None, save_file: bool = None):
        """Update report configuration."""
        if detail_level:
            self.config['report']['detail_level'] = detail_level
            print(f"✅ Detail level updated to: {detail_level}")
        
        if include_summary is not None:
            self.config['report']['include_executive_summary'] = include_summary
            print(f"✅ Include executive summary: {include_summary}")
        
        if save_file is not None:
            self.config['report']['save_to_file'] = save_file
            print(f"✅ Save to file: {save_file}")
    
    def update_system_config(self, log_level: str = None, debug_mode: bool = None,
                           mock_fallback: bool = None):
        """Update system configuration."""
        if log_level:
            self.config['system']['log_level'] = log_level
            print(f"✅ Log level updated to: {log_level}")
        
        if debug_mode is not None:
            self.config['system']['debug_mode'] = debug_mode
            print(f"✅ Debug mode: {debug_mode}")
        
        if mock_fallback is not None:
            self.config['system']['mock_data_fallback'] = mock_fallback
            print(f"✅ Mock data fallback: {mock_fallback}")
    
    def toggle_api(self, api_name: str):
        """Toggle an API on/off."""
        if api_name in self.config['api']['enabled_apis']:
            self.config['api']['enabled_apis'].remove(api_name)
            print(f"✅ Disabled API: {api_name}")
        else:
            self.config['api']['enabled_apis'].append(api_name)
            print(f"✅ Enabled API: {api_name}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.get_default_config()
        print("✅ Configuration reset to defaults")
    
    def export_json(self, filename: str = "config_export.json"):
        """Export configuration to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting configuration: {e}")
    
    def import_json(self, filename: str):
        """Import configuration from JSON file."""
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return
        
        try:
            with open(filename, 'r') as f:
                imported_config = json.load(f)
            
            # Merge with current config
            self.config.update(imported_config)
            print(f"✅ Configuration imported from {filename}")
        
        except Exception as e:
            print(f"❌ Error importing configuration: {e}")
    
    def create_default_config(self):
        """Create a default config.json file."""
        default_config = self.get_default_config()
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Created default config.json at {self.config_path}")
        except Exception as e:
            print(f"❌ Error creating default config: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
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


def main():
    """Main configuration management interface."""
    manager = SimpleConfigManager()
    
    while True:
        print("\n" + "="*60)
        print("🔧 FIRS SIMPLE CONFIGURATION MANAGER")
        print("="*60)
        print("1. Show current configuration")
        print("2. Update LLM configuration")
        print("3. Update API configuration")
        print("4. Update Web Search configuration")
        print("5. Update Report configuration")
        print("6. Update System configuration")
        print("7. Toggle API on/off")
        print("8. Export to JSON")
        print("9. Import from JSON")
        print("10. Reset to defaults")
        print("11. Save changes")
        print("0. Exit")
        
        choice = input("\nSelect an option (0-11): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        
        elif choice == "1":
            manager.show_current_config()
        
        elif choice == "2":
            print("\n🧠 LLM Configuration Update")
            provider = input("Provider (ollama/openai) [Enter to skip]: ").strip() or None
            model = input("Model [Enter to skip]: ").strip() or None
            temp = input("Temperature (0.0-2.0) [Enter to skip]: ").strip() or None
            tokens = input("Max Tokens [Enter to skip]: ").strip() or None
            
            if temp:
                try:
                    temp = float(temp)
                except ValueError:
                    print("❌ Invalid temperature value")
                    continue
            
            if tokens:
                try:
                    tokens = int(tokens)
                except ValueError:
                    print("❌ Invalid max tokens value")
                    continue
            
            manager.update_llm_config(provider, model, temp, tokens)
        
        elif choice == "3":
            print("\n🌐 API Configuration Update")
            apis = input("Enabled APIs (comma-separated) [Enter to skip]: ").strip() or None
            rate_limit = input("Rate Limit (req/min) [Enter to skip]: ").strip() or None
            concurrent = input("Concurrent Requests [Enter to skip]: ").strip() or None
            
            if apis:
                apis = [api.strip() for api in apis.split(',')]
            
            if rate_limit:
                try:
                    rate_limit = int(rate_limit)
                except ValueError:
                    print("❌ Invalid rate limit value")
                    continue
            
            if concurrent:
                try:
                    concurrent = int(concurrent)
                except ValueError:
                    print("❌ Invalid concurrent requests value")
                    continue
            
            manager.update_api_config(apis, rate_limit, concurrent)
        
        elif choice == "4":
            print("\n🔍 Web Search Configuration Update")
            depth = input("Search Depth (basic/standard/comprehensive) [Enter to skip]: ").strip() or None
            max_news = input("Max News Articles [Enter to skip]: ").strip() or None
            max_expert = input("Max Expert Reports [Enter to skip]: ").strip() or None
            
            if max_news:
                try:
                    max_news = int(max_news)
                except ValueError:
                    print("❌ Invalid max news value")
                    continue
            
            if max_expert:
                try:
                    max_expert = int(max_expert)
                except ValueError:
                    print("❌ Invalid max expert value")
                    continue
            
            manager.update_web_search_config(depth, max_news, max_expert)
        
        elif choice == "5":
            print("\n📊 Report Configuration Update")
            detail = input("Detail Level (summary/standard/detailed) [Enter to skip]: ").strip() or None
            summary = input("Include Executive Summary (y/n) [Enter to skip]: ").strip() or None
            save = input("Save to File (y/n) [Enter to skip]: ").strip() or None
            
            if summary:
                summary = summary.lower() in ['y', 'yes', 'true']
            
            if save:
                save = save.lower() in ['y', 'yes', 'true']
            
            manager.update_report_config(detail, summary, save)
        
        elif choice == "6":
            print("\n⚙️  System Configuration Update")
            log_level = input("Log Level (DEBUG/INFO/WARNING/ERROR) [Enter to skip]: ").strip() or None
            debug = input("Debug Mode (y/n) [Enter to skip]: ").strip() or None
            mock = input("Mock Data Fallback (y/n) [Enter to skip]: ").strip() or None
            
            if debug:
                debug = debug.lower() in ['y', 'yes', 'true']
            
            if mock:
                mock = mock.lower() in ['y', 'yes', 'true']
            
            manager.update_system_config(log_level, debug, mock)
        
        elif choice == "7":
            print("\n🔌 Toggle API On/Off")
            print("Available APIs:", ", ".join(manager.config['api']['enabled_apis']))
            api_name = input("Enter API name to toggle: ").strip()
            if api_name:
                manager.toggle_api(api_name)
        
        elif choice == "8":
            filename = input("Export filename [config_export.json]: ").strip() or "config_export.json"
            manager.export_json(filename)
        
        elif choice == "9":
            filename = input("Import filename: ").strip()
            if filename:
                manager.import_json(filename)
        
        elif choice == "10":
            confirm = input("Are you sure you want to reset to defaults? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                manager.reset_to_defaults()
        
        elif choice == "11":
            manager.save_config()
        
        else:
            print("❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
