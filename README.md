# Financial Intelligence System (FIRS)

A comprehensive financial analysis platform that generates detailed investment reports by aggregating data from multiple financial APIs, processing it through AI analysis, and storing insights in a vector database for semantic search and retrieval.

## Project Overview

FIRS is designed to provide institutional-grade financial intelligence by combining real-time market data, AI-powered analysis, and intelligent caching to deliver comprehensive investment reports with minimal latency.

## System Architecture

### High-Level Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  AI Processing  │    │   Storage &     │
│                 │    │                 │    │   Retrieval     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Alpha Vantage │    │ • LLM Analysis  │    │ • Cache Layer   │
│ • Yahoo Finance │    │ • Sentiment     │    │ • Temp Storage  │
│ • Finnhub       │    │ • Risk Assessment│   │ • Vector DB     │
│ • Web Search    │    │ • Insights      │    │ • Qdrant        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Fetch    │    │ Report Generation│    │ Report Storage  │
│   & Validation  │    │ & Compilation   │    │ & Retrieval     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Data Layer**: Multiple financial API integrations with fallback mechanisms
2. **Processing Layer**: AI-powered analysis using Ollama LLM integration
3. **Storage Layer**: Multi-tier storage system with caching and vector search
4. **API Layer**: Unified interface for data access and report generation

## Data Flow

1. **Data Collection**: Concurrent fetching from multiple financial APIs
2. **Data Processing**: AI analysis of financial metrics, news, and market sentiment
3. **Report Generation**: Compilation of insights into comprehensive investment reports
4. **Storage**: Multi-tier storage with intelligent caching and vector embeddings
5. **Retrieval**: Semantic search across stored reports and financial data

## Key Features

- **Multi-Source Data Integration**: Alpha Vantage, Yahoo Finance, Finnhub, Web Search
- **AI-Powered Analysis**: LLM-driven financial insights and risk assessment
- **Intelligent Caching**: Multi-layer caching system with configurable TTL
- **Vector Database Storage**: Semantic search across financial documents
- **Real-time Processing**: Concurrent data fetching and analysis
- **Configurable Architecture**: Flexible configuration for different deployment scenarios

## Technology Stack

- **Backend**: Python 3.10+, asyncio for concurrent operations
- **AI/ML**: Ollama integration with local LLM models
- **Vector Database**: Qdrant for semantic search and storage
- **Data Processing**: Custom financial data aggregation and analysis
- **Storage**: Multi-tier caching with pickle and JSON persistence

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Docker (for Qdrant)
- Ollama (for local LLM processing)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd FIRS

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Ollama Setup

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest
```

### 3. Qdrant Setup

```bash
# Start Qdrant using Docker
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Verify Qdrant is running
curl http://localhost:6333/collections
```

### 4. Configuration

Edit `config.json` to customize system behavior:

```json
{
  "system": {
    "log_level": "INFO",
    "max_concurrent_requests": 10
  },
  "llm": {
    "provider": "ollama",
    "model": "llama3.1:8b",
    "timeout": 120,
    "temperature": 0.3
  },
  "api": {
    "enabled_apis": ["alpha_vantage", "yahoo_finance", "finnhub", "web_search"],
    "alpha_vantage_key": "YOUR_API_KEY",
    "finnhub_key": "YOUR_API_KEY"
  },
  "storage": {
    "cache_ttl": 600,
    "temp_storage_ttl": 600,
    "qdrant_url": "http://localhost:6333"
  },
  "report": {
    "detail_level": "standard",
    "save_to_file": true
  }
}
```

## Usage

### Basic Report Generation

```bash
# Generate report for default ticker (AAPL)
python main.py

# Generate report for specific ticker
python main.py TSLA

# Force refresh (ignore cache)
python main.py --force AAPL
```

### Command Line Options

- **No arguments**: Generate report for AAPL using cache
- **Ticker symbol**: Generate report for specified ticker
- **--force**: Bypass cache and regenerate report

### Output

Reports are automatically:
1. Displayed in the console
2. Saved to the `reports/` directory
3. Stored in the vector database
4. Cached for future retrieval

## Configuration Options

### LLM Configuration

- **provider**: AI service provider (ollama, openai)
- **model**: Specific model to use
- **timeout**: Request timeout in seconds
- **temperature**: AI response creativity (0.0-1.0)

### API Configuration

- **enabled_apis**: List of APIs to use
- **api_keys**: Authentication keys for paid services
- **rate_limits**: Request throttling settings

### Storage Configuration

- **cache_ttl**: Cache expiration time in seconds
- **temp_storage_ttl**: Temporary file retention period
- **qdrant_url**: Vector database connection URL

### Report Configuration

- **detail_level**: Analysis depth (basic, standard, comprehensive)
- **save_to_file**: Whether to persist reports locally

## Project Structure

```
FIRS/
├── agents/                 # Financial API integrations
│   ├── alpha_vantage_agent.py
│   ├── yahoo_finance_agent.py
│   ├── finnhub_agent.py
│   └── web_search_agent.py
├── preprocessing/          # Data processing and analysis
│   ├── create_report.py
│   ├── llm_adapter.py
│   └── utils.py
├── storage/               # Multi-tier storage system
│   ├── cache_manager.py
│   ├── temp_storage.py
│   ├── vector_db.py
│   └── storage_manager.py
├── config.json            # System configuration
├── main.py               # Main application entry point
├── requirements.txt       # Python dependencies
└── reports/              # Generated report storage
```

## Development

### Adding New Data Sources

1. Create new agent in `agents/` directory
2. Implement required interface methods
3. Add configuration in `config.json`
4. Update storage integration if needed

### Extending Analysis

1. Modify LLM prompts in `preprocessing/create_report.py`
2. Add new analysis functions
3. Update report structure and storage

### Customizing Storage

1. Modify TTL settings in configuration
2. Add new storage backends in `storage/` directory
3. Implement custom caching strategies

## Performance Considerations

- **Concurrent Processing**: Uses asyncio for parallel API calls
- **Intelligent Caching**: Reduces redundant API calls and processing
- **Vector Search**: Fast semantic retrieval of financial insights
- **Configurable TTL**: Balance between freshness and performance

## Monitoring and Logging

- **Structured Logging**: JSON-formatted logs with configurable levels
- **Performance Metrics**: Storage statistics and cache hit rates
- **Error Handling**: Comprehensive error logging and fallback mechanisms

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Verify Ollama service is running
   - Check model availability with `ollama list`

2. **Qdrant Connection Failed**
   - Ensure Docker container is running
   - Verify port 6333 is accessible

3. **API Rate Limits**
   - Check API key configuration
   - Adjust rate limiting in configuration

### Debug Mode

Enable detailed logging by setting log level to DEBUG in `config.json`:

```json
{
  "system": {
    "log_level": "DEBUG"
  }
}
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## License

This project is licensed under the Apache-2.0 License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review configuration options
3. Enable debug logging
4. Create GitHub issue with detailed information
