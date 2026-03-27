class BIAgentError(Exception):
    """Base exception for the BI Agent application."""
    pass


class DatabaseError(BIAgentError):
    """Raised when database operations fail."""
    pass


class QueryExecutionError(BIAgentError):
    """Raised when SQL agent query execution fails."""
    pass


class ChartGenerationError(BIAgentError):
    """Raised when chart generation fails."""
    pass


class SessionNotFoundError(BIAgentError):
    """Raised when a chat session is not found."""
    pass
