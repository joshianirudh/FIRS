#!/usr/bin/env python3
"""
Vector Database Integration for FIRS - handles Qdrant operations with nomic-embed-text embeddings.
"""
import json
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Manages vector database operations with Qdrant."""
    
    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "firs_financial_data"):
        """
        Initialize vector database connection.
        
        Args:
            qdrant_url: Qdrant server URL
            collection_name: Name of the collection to use
        """
        self.qdrant_url = qdrant_url.rstrip('/')
        self.collection_name = collection_name
        self.api_url = f"{self.qdrant_url}/collections/{collection_name}"
        
        logger.info(f"Vector database initialized with Qdrant at {self.qdrant_url}")
    
    async def test_connection(self) -> bool:
        """Test connection to Qdrant server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.qdrant_url}/collections")
                if response.status_code == 200:
                    logger.info("Qdrant connection successful")
                    return True
                else:
                    logger.error(f"❌ Qdrant connection failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Qdrant connection error: {e}")
            return False
    
    async def create_collection(self, vector_size: int = 768) -> bool:
        """
        Create the collection if it doesn't exist.
        
        Args:
            vector_size: Size of the embedding vectors (nomic-embed-text:latest = 768)
        """
        try:
            # Check if collection exists
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.qdrant_url}/collections/{self.collection_name}")
                if response.status_code == 200:
                    logger.info(f"Collection {self.collection_name} already exists")
                    return True
                
                # Create collection
                collection_config = {
                    "vectors": {
                        "size": vector_size,
                        "distance": "Cosine"
                    }
                }
                
                response = await client.put(
                    f"{self.qdrant_url}/collections/{self.collection_name}",
                    json=collection_config
                )
                
                if response.status_code == 200:
                    logger.info(f"Created collection {self.collection_name}")
                    return True
                else:
                    logger.error(f"❌ Failed to create collection: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            return False
    
    async def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings using nomic-embed-text model via Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            # Prepare text for embedding (clean and truncate if needed)
            clean_text = text.strip()
            if len(clean_text) > 8192:  # Limit text length
                clean_text = clean_text[:8192]
            
            # Call Ollama embedding API
            payload = {
                "model": "nomic-embed-text:latest",
                "prompt": clean_text
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embeddings = result.get("embedding", [])
                    
                    if embeddings and len(embeddings) > 0:
                        logger.info(f"Generated embeddings for text (length: {len(embeddings)})")
                        return embeddings
                    else:
                        logger.error("❌ No embeddings returned from Ollama")
                        return None
                else:
                    logger.error(f"❌ Ollama embedding API failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            return None
    
    async def store_document(self, 
                           ticker: str, 
                           document_type: str, 
                           content: Dict[str, Any], 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a document in the vector database.
        
        Args:
            ticker: Stock ticker symbol
            document_type: Type of document (e.g., 'financial_data', 'news', 'report')
            content: Document content
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate text representation for embedding
            text_for_embedding = self._prepare_text_for_embedding(content, document_type)
            
            # Generate embeddings
            embeddings = await self.generate_embeddings(text_for_embedding)
            if not embeddings:
                logger.error("❌ Failed to generate embeddings")
                return False
            
            # Prepare payload for Qdrant
            payload = {
                "points": [{
                    "id": str(uuid.uuid4()),
                    "vector": embeddings,
                    "payload": {
                        "ticker": ticker,
                        "document_type": document_type,
                        "content": content,
                        "metadata": metadata or {},
                        "timestamp": datetime.now().isoformat(),
                        "text_for_embedding": text_for_embedding
                    }
                }]
            }
            
            # Store in Qdrant
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/points",
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Stored document for {ticker} ({document_type}) in vector database")
                    return True
                else:
                    logger.error(f"❌ Failed to store document: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error storing document: {e}")
            return False
    
    def _prepare_text_for_embedding(self, content: Dict[str, Any], document_type: str) -> str:
        """Prepare text content for embedding generation."""
        if document_type == "financial_data":
            # Extract key financial metrics
            text_parts = []
            if "symbol" in content:
                text_parts.append(f"Symbol: {content['symbol']}")
            if "price" in content:
                text_parts.append(f"Price: {content['price']}")
            if "volume" in content:
                text_parts.append(f"Volume: {content['volume']}")
            if "market_cap" in content:
                text_parts.append(f"Market Cap: {content['market_cap']}")
            if "pe_ratio" in content:
                text_parts.append(f"P/E Ratio: {content['pe_ratio']}")
            
            return " | ".join(text_parts)
            
        elif document_type == "news":
            # Extract news content
            text_parts = []
            if "title" in content:
                text_parts.append(f"Title: {content['title']}")
            if "summary" in content:
                text_parts.append(f"Summary: {content['summary']}")
            if "sentiment" in content:
                text_parts.append(f"Sentiment: {content['sentiment']}")
            
            return " | ".join(text_parts)
            
        elif document_type == "report":
            # Extract comprehensive insights from report
            text_parts = []
            
            # Core report sections
            if "executive_summary" in content:
                text_parts.append(f"Executive Summary: {content['executive_summary']}")
            if "key_investment_points" in content:
                points = content['key_investment_points']
                if isinstance(points, list):
                    text_parts.append(f"Key Points: {'; '.join(points)}")
            if "investment_recommendation" in content:
                text_parts.append(f"Recommendation: {content['investment_recommendation']}")
            if "risk_assessment" in content:
                text_parts.append(f"Risk Assessment: {content['risk_assessment']}")
            if "time_horizon" in content:
                text_parts.append(f"Time Horizon: {content['time_horizon']}")
            if "confidence_level" in content:
                text_parts.append(f"Confidence Level: {content['confidence_level']}")
            
            # Financial data sections
            if "financial_summary" in content:
                financial = content['financial_summary']
                if isinstance(financial, dict):
                    if "alpha_vantage" in financial:
                        text_parts.append(f"Alpha Vantage: {financial['alpha_vantage']}")
                    if "finnhub" in financial:
                        text_parts.append(f"Finnhub: {financial['finnhub']}")
                    if "yahoo_finance" in financial:
                        text_parts.append(f"Yahoo Finance: {financial['yahoo_finance']}")
            
            # Web search insights
            if "web_data" in content:
                web_data = content['web_data']
                if isinstance(web_data, dict):
                    if "news_summary" in web_data:
                        text_parts.append(f"News Summary: {web_data['news_summary']}")
                    if "market_sentiment" in web_data:
                        text_parts.append(f"Market Sentiment: {web_data['market_sentiment']}")
            
            # If no structured data found, use the raw content
            if not text_parts:
                text_parts.append(f"Report Content: {json.dumps(content, default=str)}")
            
            return " | ".join(text_parts)
            
        else:
            # Generic text preparation
            return json.dumps(content, default=str)
    
    async def search_similar(self, 
                           query: str, 
                           ticker: Optional[str] = None, 
                           document_type: Optional[str] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            ticker: Filter by specific ticker
            document_type: Filter by document type
            limit: Maximum number of results
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate embeddings for query
            query_embeddings = await self.generate_embeddings(query)
            if not query_embeddings:
                logger.error("❌ Failed to generate embeddings for query")
                return []
            
            # Prepare search payload
            search_payload = {
                "vector": query_embeddings,
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }
            
            # Add filters if specified
            if ticker or document_type:
                search_payload["filter"] = {
                    "must": []
                }
                
                if ticker:
                    search_payload["filter"]["must"].append({
                        "key": "ticker",
                        "match": {"value": ticker}
                    })
                
                if document_type:
                    search_payload["filter"]["must"].append({
                        "key": "document_type",
                        "match": {"value": document_type}
                    })
            
            # Search in Qdrant
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/points/search",
                    json=search_payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    documents = []
                    
                    for point in result.get("result", []):
                        documents.append({
                            "id": point["id"],
                            "score": point["score"],
                            "payload": point["payload"]
                        })
                    
                    logger.info(f"Found {len(documents)} similar documents")
                    return documents
                else:
                    logger.error(f"❌ Search failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error searching similar documents: {e}")
            return []
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/points/{document_id}"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    logger.error(f"❌ Failed to retrieve document: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error retrieving document: {e}")
            return None
    
    async def delete_documents(self, ticker: str, document_type: Optional[str] = None) -> bool:
        """
        Delete documents for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            document_type: Optional document type filter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build filter
            filter_condition = {
                "must": [{"key": "ticker", "match": {"value": ticker}}]
            }
            
            if document_type:
                filter_condition["must"].append({
                    "key": "document_type", 
                    "match": {"value": document_type}
                })
            
            # Delete points
            payload = {"filter": filter_condition}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/points/delete",
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Deleted documents for {ticker}")
                    return True
                else:
                    logger.error(f"❌ Failed to delete documents: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error deleting documents: {e}")
            return False
    
    async def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the collection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"❌ Failed to get collection info: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting collection info: {e}")
            return None
