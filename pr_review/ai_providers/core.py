"""Core AI provider functionality for PR Review CLI."""

from typing import Any
from ..exceptions import PrReviewError
from .gemini import send_to_gemini, make_prompt

def send_to_provider(prompt: str, provider: str, model: str, api_key: str) -> Any:
    """
    Send prompt to the selected AI provider and return response stream.
    
    Args:
        prompt: The prompt to send to the API
        provider: The AI provider to use (gemini, openai, anthropic)
        model: The model to use
        api_key: The API key for the provider
        
    Returns:
        Any: The response stream from the API
        
    Raises:
        PrReviewError: If the provider is not supported or there is an API error
    """
    try:
        if provider == "gemini":
            return send_to_gemini(prompt, api_key, model)
        elif provider == "openai":
            # Placeholder for OpenAI implementation
            # This will be implemented in future versions
            raise PrReviewError("OpenAI provider not yet implemented", exit_code=4)
        elif provider == "anthropic":
            # Placeholder for Anthropic implementation
            # This will be implemented in future versions
            raise PrReviewError("Anthropic provider not yet implemented", exit_code=4)
        else:
            raise PrReviewError(f"Unknown provider: {provider}", exit_code=4)
    except Exception as e:
        if isinstance(e, PrReviewError):
            raise
        raise PrReviewError(f"Error with AI provider {provider}: {str(e)}", exit_code=4) 