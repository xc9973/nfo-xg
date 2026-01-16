"""Exception classes for NFO Editor."""
from typing import Optional


class NfoEditorError(Exception):
    """Base exception for NFO Editor."""
    pass


class ParseError(NfoEditorError):
    """XML parsing error.
    
    Raised when XML content is invalid or malformed.
    """
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        """Initialize ParseError.
        
        Args:
            message: Error description
            line: Line number where error occurred (optional)
            column: Column number where error occurred (optional)
        """
        self.line = line
        self.column = column
        
        if line is not None and column is not None:
            full_message = f"{message} (line {line}, column {column})"
        elif line is not None:
            full_message = f"{message} (line {line})"
        else:
            full_message = message
        
        super().__init__(full_message)


class ValidationError(NfoEditorError):
    """Data validation error.
    
    Raised when NFO data fails validation.
    """
    
    def __init__(self, field: str, message: str):
        """Initialize ValidationError.
        
        Args:
            field: Name of the field that failed validation
            message: Error description
        """
        self.field = field
        super().__init__(f"{field}: {message}")


class FileError(NfoEditorError):
    """File operation error.
    
    Raised when file operations fail (read, write, not found, etc.).
    """
    pass
