"""Configuration management for PR Review CLI."""

import tomli
import tomli_w
from pathlib import Path
from typing import Dict, Any

from ..exceptions import PrReviewError

# Global constants
DEFAULT_CONFIG = {
    "provider": "gemini",
    "model": "gemini-2.5-flash-preview-04-17",
    "api_keys": {
        "gemini": "",
        "openai": "",
        "anthropic": ""
    }
}

CONFIG_PATH = Path.home() / ".pr-review.toml"


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or create default if not exists.
    
    Returns:
        Dict[str, Any]: The configuration dictionary
        
    Raises:
        PrReviewError: If there is an error loading the configuration
    """
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomli.load(f)
    except Exception as e:
        raise PrReviewError(f"Error loading config: {e}", exit_code=2)


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.
    
    Args:
        config: The configuration dictionary to save
        
    Raises:
        PrReviewError: If there is an error saving the configuration
    """
    try:
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(config, f)
    except Exception as e:
        raise PrReviewError(f"Error saving config: {e}", exit_code=2) 