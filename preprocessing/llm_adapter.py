"""LLM Adapter for unified interface to different LLM providers."""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import httpx

from config import config

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON from prompt."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation."""
    
    def __init__(self, model: str = None, base_url: Optional[str] = None):
        super().__init__(base_url=base_url or config["llm"].get("ollama_base_url", "http://localhost:11434"))
        # Use model from config if not specified, fallback to llama2
        self.model = model or config["llm"].get("model", "llama2")
        self.api_url = f"{self.base_url}/api/generate"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama API."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            async with httpx.AsyncClient() as client:
                # Use config timeout or default to 120 seconds for Ollama
                timeout = kwargs.get("timeout", 120)
                logger.info(f"Making Ollama request to {self.api_url} with model {self.model}, timeout: {timeout}s")
                
                response = await client.post(self.api_url, json=payload, timeout=timeout)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Ollama response received successfully")
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON using Ollama."""
        # Add JSON formatting instruction to prompt
        json_prompt = f"{prompt}\n\nPlease respond with valid JSON only."
        
        try:
            text_response = await self.generate_text(json_prompt, **kwargs)
            
            # Try to extract JSON from response
            # Look for JSON between ```json and ``` markers
            if "```json" in text_response and "```" in text_response:
                start = text_response.find("```json") + 7
                end = text_response.rfind("```")
                json_str = text_response[start:end].strip()
            else:
                # Try to find JSON in the response
                json_str = text_response.strip()
            
            # Parse JSON
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, return as text
                logger.warning(f"Failed to parse JSON from Ollama response: {text_response}")
                return {"raw_response": text_response, "parse_error": True}
                
        except Exception as e:
            logger.error(f"Ollama JSON generation error: {e}")
            raise


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            api_key=api_key or config["llm"].get("openai_api_key"),
            base_url=base_url or config["llm"].get("openai_base_url", "https://api.openai.com/v1")
        )
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API."""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON using OpenAI."""
        try:
            # Add JSON formatting instruction
            json_prompt = f"{prompt}\n\nRespond with valid JSON only."
            
            # Set response format to JSON for newer models
            if "gpt-4" in self.model or "gpt-3.5-turbo" in self.model:
                kwargs["response_format"] = {"type": "json_object"}
            
            text_response = await self.generate_text(json_prompt, **kwargs)
            
            # Parse JSON response
            try:
                return json.loads(text_response)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from OpenAI response: {text_response}")
                return {"raw_response": text_response, "parse_error": True}
                
        except Exception as e:
            logger.error(f"OpenAI JSON generation error: {e}")
            raise


class LLMAdapter:
    """Main LLM adapter that provides unified interface."""
    
    def __init__(self, provider: LLMProvider = LLMProvider.OLLAMA, **kwargs):
        """
        Initialize LLM adapter.
        
        Args:
            provider: LLM provider to use
            **kwargs: Provider-specific configuration
        """
        self.provider = provider
        self.llm = self._create_provider(provider, **kwargs)
        logger.info(f"Initialized LLM adapter with {provider.value}")
    
    def _create_provider(self, provider: LLMProvider, **kwargs) -> BaseLLMProvider:
        """Create the appropriate LLM provider."""
        if provider == LLMProvider.OLLAMA:
            return OllamaProvider(**kwargs)
        elif provider == LLMProvider.OPENAI:
            return OpenAIProvider(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the configured provider."""
        return await self.llm.generate_text(prompt, **kwargs)
    
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON using the configured provider."""
        return await self.llm.generate_json(prompt, **kwargs)
    
    def switch_provider(self, provider: LLMProvider, **kwargs):
        """Switch to a different LLM provider."""
        self.provider = provider
        self.llm = self._create_provider(provider, **kwargs)
        logger.info(f"Switched LLM provider to {provider.value}")
    
    async def test_connection(self) -> bool:
        """Test if the LLM provider is accessible."""
        try:
            test_prompt = "Hello, this is a test. Please respond with 'OK'."
            response = await self.generate_text(test_prompt)
            return "OK" in response or len(response) > 0
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False


# Convenience functions for easy usage
async def create_llm_adapter(provider: str = "ollama", **kwargs) -> LLMAdapter:
    """Create an LLM adapter with the specified provider."""
    try:
        provider_enum = LLMProvider(provider.lower())
        
        # If using Ollama and no model specified, get from config
        if provider_enum == LLMProvider.OLLAMA and "model" not in kwargs:
            kwargs["model"] = config["llm"].get("model", "llama2")
        
        return LLMAdapter(provider_enum, **kwargs)
    except ValueError:
        raise ValueError(f"Unsupported provider: {provider}. Supported: {[p.value for p in LLMProvider]}")


async def test_llm_providers():
    """Test all available LLM providers."""
    results = {}
    
    # Test Ollama
    try:
        ollama_adapter = LLMAdapter(LLMProvider.OLLAMA)
        results["ollama"] = await ollama_adapter.test_connection()
    except Exception as e:
        results["ollama"] = f"Error: {e}"
    
    # Test OpenAI (if configured)
    if config["llm"].get("openai_api_key"):
        try:
            openai_adapter = LLMAdapter(LLMProvider.OPENAI)
            results["openai"] = await openai_adapter.test_connection()
        except Exception as e:
            results["openai"] = f"Error: {e}"
    else:
        results["openai"] = "Not configured"
    
    return results
