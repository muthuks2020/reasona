"""
Configuration management for Reasona.

This module provides a centralized way to manage configuration
for API keys, providers, and runtime settings.
"""

from __future__ import annotations

import os
from typing import Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


# Load .env file if present
load_dotenv()


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider."""
    
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasonaConfig:
    """
    Main configuration class for Reasona.
    
    Configuration is loaded from environment variables by default,
    with fallback to explicit values.
    
    Environment Variables:
        OPENAI_API_KEY: OpenAI API key
        ANTHROPIC_API_KEY: Anthropic API key
        GOOGLE_API_KEY: Google/Gemini API key
        MISTRAL_API_KEY: Mistral API key
        GROQ_API_KEY: Groq API key
        REASONA_DEBUG: Enable debug mode
        REASONA_LOG_LEVEL: Logging level
    
    Example:
        >>> config = ReasonaConfig()
        >>> config.openai.api_key = "sk-..."
        >>> agent = Conductor(name="test", model="openai/gpt-4o", config=config)
    """
    
    # Provider configs
    openai: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        organization=os.getenv("OPENAI_ORG_ID"),
    ))
    
    anthropic: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    ))
    
    google: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
    ))
    
    mistral: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        api_key=os.getenv("MISTRAL_API_KEY"),
    ))
    
    groq: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        api_key=os.getenv("GROQ_API_KEY"),
    ))
    
    ollama: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    ))
    
    azure: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        extra={
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        }
    ))
    
    # Runtime settings
    debug: bool = field(default_factory=lambda: os.getenv("REASONA_DEBUG", "").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("REASONA_LOG_LEVEL", "INFO"))
    
    # Server settings
    server_host: str = field(default_factory=lambda: os.getenv("REASONA_HOST", "0.0.0.0"))
    server_port: int = field(default_factory=lambda: int(os.getenv("REASONA_PORT", "8000")))
    
    # Paths
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("REASONA_CACHE_DIR", ".reasona/cache")))
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("REASONA_LOG_DIR", ".reasona/logs")))
    
    def get_provider_config(self, provider: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        provider_lower = provider.lower()
        
        configs = {
            "openai": self.openai,
            "anthropic": self.anthropic,
            "google": self.google,
            "gemini": self.google,
            "mistral": self.mistral,
            "groq": self.groq,
            "ollama": self.ollama,
            "azure": self.azure,
        }
        
        return configs.get(provider_lower, ProviderConfig())
    
    def set_api_key(self, provider: str, api_key: str) -> "ReasonaConfig":
        """Set API key for a provider (fluent API)."""
        config = self.get_provider_config(provider)
        config.api_key = api_key
        return self
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasonaConfig":
        """Create config from dictionary."""
        config = cls()
        
        for provider in ["openai", "anthropic", "google", "mistral", "groq", "ollama", "azure"]:
            if provider in data:
                provider_data = data[provider]
                provider_config = getattr(config, provider)
                for key, value in provider_data.items():
                    if hasattr(provider_config, key):
                        setattr(provider_config, key, value)
        
        for key in ["debug", "log_level", "server_host", "server_port"]:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    @classmethod
    def from_file(cls, path: Path) -> "ReasonaConfig":
        """Load config from YAML or JSON file."""
        import json
        import yaml
        
        path = Path(path)
        content = path.read_text()
        
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        
        return cls.from_dict(data)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "debug": self.debug,
            "log_level": self.log_level,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "providers": {
                "openai": {"configured": self.openai.api_key is not None},
                "anthropic": {"configured": self.anthropic.api_key is not None},
                "google": {"configured": self.google.api_key is not None},
                "mistral": {"configured": self.mistral.api_key is not None},
                "groq": {"configured": self.groq.api_key is not None},
                "ollama": {"base_url": self.ollama.base_url},
                "azure": {"configured": self.azure.api_key is not None},
            }
        }


# Global default configuration
_default_config: Optional[ReasonaConfig] = None


def get_config() -> ReasonaConfig:
    """Get the global default configuration."""
    global _default_config
    if _default_config is None:
        _default_config = ReasonaConfig()
    return _default_config


def set_config(config: ReasonaConfig) -> None:
    """Set the global default configuration."""
    global _default_config
    _default_config = config
