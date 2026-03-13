"""AI provider implementations for search query generation"""

import os
import re
from abc import ABC, abstractmethod
from typing import Optional

from .config import logger

# Conditional imports
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.genai as genai
except ImportError:
    genai = None

try:
    import requests
except ImportError:
    requests = None


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def generate_query(self, prompt: str) -> Optional[str]:
        """Generate Gmail search query from prompt"""
        pass

    @staticmethod
    def clean_query(query: str) -> Optional[str]:
        """Clean and validate generated query"""
        query = re.sub(r"```\w*\n?", "", query)
        query = re.sub(r"```", "", query)
        query = query.strip().strip("\"'")
        if re.search(r"[;|&]", query):
            logger.warning("⚠️  Query contains potentially unsafe characters")
            return None
        return query


class OpenAIProvider(AIProvider):
    """OpenAI implementation"""

    def generate_query(self, prompt: str) -> Optional[str]:
        if not OpenAI:
            logger.error("OpenAI library not installed")
            return None
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Convert to Gmail search operators. Return ONLY the query.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.1,
            )
            return self.clean_query(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None


class GeminiProvider(AIProvider):
    """Google Gemini implementation"""

    def generate_query(self, prompt: str) -> Optional[str]:
        if not genai:
            logger.error("Google GenAI library not installed")
            return None
        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Convert this to Gmail search operators. Return ONLY the query: {prompt}",
            )
            return self.clean_query(response.text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None


class DeepSeekProvider(AIProvider):
    """DeepSeek implementation"""

    def generate_query(self, prompt: str) -> Optional[str]:
        if not requests:
            logger.error("Requests library not installed")
            return None
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Convert to Gmail search operators. Return ONLY the query.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 100,
                "temperature": 0.1,
            }
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return self.clean_query(result["choices"][0]["message"]["content"])
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return None


class AISearchFactory:
    """Factory for creating AI providers"""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "deepseek": DeepSeekProvider,
    }

    @classmethod
    def create(cls, provider_name: str) -> Optional[AIProvider]:
        """Create AI provider instance"""
        provider_class = cls.PROVIDERS.get(provider_name)
        if not provider_class:
            logger.error(f"Unknown provider: {provider_name}")
            return None

        env_var = f"{provider_name.upper()}_API_KEY"
        api_key = os.getenv(env_var)

        if not api_key:
            logger.error(f"\n⚠️  {env_var} environment variable not set!")
            logger.error(f"\nTo get a {provider_name.title()} API key:")

            urls = {
                "openai": "https://platform.openai.com/api-keys",
                "gemini": "https://makersuite.google.com/app/apikey",
                "deepseek": "https://platform.deepseek.com/api_keys",
            }
            logger.error(f"1. Go to: {urls.get(provider_name, '')}")
            logger.error("2. Create a new API key")
            logger.error(f"3. Set it: export {env_var}='your-key-here'")
            return None

        return provider_class(api_key)
