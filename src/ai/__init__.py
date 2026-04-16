# src/ai/__init__.py - AI Module Exports
# Unified AI client interfaces

from .gemini_client import GeminiClient, create_gemini_client
from .openrouter_client import OpenRouterClient, create_openrouter_client
from .ollama_client import OllamaClient, create_ollama_client

__all__ = [
    'GeminiClient',
    'create_gemini_client',
    'OpenRouterClient', 
    'create_openrouter_client',
    'OllamaClient',
    'create_ollama_client',
]
