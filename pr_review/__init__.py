"""PR Review CLI - AI-powered code review tool."""

__version__ = "2.0.0"

from .exceptions import PrReviewError
from .output import console
from .cli import main

__all__ = ['PrReviewError', 'console', 'main'] 