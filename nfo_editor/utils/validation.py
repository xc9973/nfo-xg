"""Data validation functions for NFO Editor.

Provides validation for NFO data fields with clear error messages.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

from nfo_editor.models.nfo_model import NfoData


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    field: str
    message: str = ""


def validate_year(year: str) -> ValidationResult:
    """Validate year field (1900-2100 range).
    
    Args:
        year: Year string to validate
        
    Returns:
        ValidationResult with is_valid=True if valid, False otherwise
    """
    field = "year"
    
    # Empty year is valid (optional field)
    if not year or year.strip() == "":
        return ValidationResult(is_valid=True, field=field)
    
    # Must be a valid integer
    try:
        year_int = int(year.strip())
    except ValueError:
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Year must be a valid integer, got '{year}'"
        )
    
    # Must be in range 1900-2100
    if year_int < 1900 or year_int > 2100:
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Year must be between 1900 and 2100, got {year_int}"
        )
    
    return ValidationResult(is_valid=True, field=field)


def validate_rating(rating: str) -> ValidationResult:
    """Validate rating field (0-10 range).
    
    Args:
        rating: Rating string to validate
        
    Returns:
        ValidationResult with is_valid=True if valid, False otherwise
    """
    field = "rating"
    
    # Empty rating is valid (optional field)
    if not rating or rating.strip() == "":
        return ValidationResult(is_valid=True, field=field)
    
    # Must be a valid number
    try:
        rating_float = float(rating.strip())
    except ValueError:
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Rating must be a valid number, got '{rating}'"
        )
    
    if not math.isfinite(rating_float):
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Rating must be a finite number, got '{rating}'"
        )

    # Must be in range 0-10
    if rating_float < 0 or rating_float > 10:
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Rating must be between 0 and 10, got {rating_float}"
        )

    return ValidationResult(is_valid=True, field=field)


def validate_runtime(runtime: str) -> ValidationResult:
    """Validate runtime field (positive integer).
    
    Args:
        runtime: Runtime string to validate (in minutes)
        
    Returns:
        ValidationResult with is_valid=True if valid, False otherwise
    """
    field = "runtime"
    
    # Empty runtime is valid (optional field)
    if not runtime or runtime.strip() == "":
        return ValidationResult(is_valid=True, field=field)
    
    # Must be a valid integer
    try:
        runtime_int = int(runtime.strip())
    except ValueError:
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Runtime must be a valid integer, got '{runtime}'"
        )
    
    # Must be positive
    if runtime_int <= 0:
        return ValidationResult(
            is_valid=False,
            field=field,
            message=f"Runtime must be a positive integer, got {runtime_int}"
        )
    
    return ValidationResult(is_valid=True, field=field)


def validate_nfo_data(data: NfoData) -> Tuple[bool, List[ValidationResult]]:
    """Validate all fields in NfoData.
    
    Args:
        data: NfoData object to validate
        
    Returns:
        Tuple of (all_valid, list of ValidationResults for invalid fields)
    """
    results = []
    
    # Validate year
    year_result = validate_year(data.year)
    if not year_result.is_valid:
        results.append(year_result)
    
    # Validate rating
    rating_result = validate_rating(data.rating)
    if not rating_result.is_valid:
        results.append(rating_result)
    
    # Validate runtime
    runtime_result = validate_runtime(data.runtime)
    if not runtime_result.is_valid:
        results.append(runtime_result)
    
    all_valid = len(results) == 0
    return all_valid, results
