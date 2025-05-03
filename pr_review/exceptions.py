"""Custom exceptions for PR Review CLI."""

class PrReviewError(Exception):
    """Base exception for PR Review errors with exit code support."""
    
    def __init__(self, message: str, exit_code: int = 1):
        """
        Initialize PrReviewError.
        
        Args:
            message: The error message
            exit_code: The exit code to use when exiting the program
        """
        self.message = message
        self.exit_code = exit_code
        super().__init__(message) 