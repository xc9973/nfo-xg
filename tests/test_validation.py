"""Property-based tests for data validation.

Feature: nfo-editor
Property 5: 数据验证一致性
Validates: Requirements 2.6
"""
import pytest
from hypothesis import given, strategies as st, settings

from nfo_editor.utils.validation import (
    validate_year,
    validate_rating,
    validate_runtime,
    validate_nfo_data,
    ValidationResult,
)
from nfo_editor.models.nfo_model import NfoData
from nfo_editor.models.nfo_types import NfoType


class TestValidationConsistency:
    """Property 5: 数据验证一致性
    
    Feature: nfo-editor, Property 5: Data Validation Consistency
    Validates: Requirements 2.6
    
    For any invalid tag value (non-numeric year, out-of-range rating, etc.),
    the validation function should return False with an error message.
    """

    # --- Year Validation Property Tests ---
    
    @given(year=st.integers(min_value=1900, max_value=2100))
    @settings(max_examples=100)
    def test_valid_year_range_accepted(self, year: int):
        """For any year in range 1900-2100, validation should pass."""
        result = validate_year(str(year))
        assert result.is_valid is True
        assert result.field == "year"

    @given(year=st.integers(max_value=1899))
    @settings(max_examples=100)
    def test_year_below_range_rejected(self, year: int):
        """For any year below 1900, validation should fail with error message."""
        result = validate_year(str(year))
        assert result.is_valid is False
        assert result.field == "year"
        assert result.message != ""
        assert "1900" in result.message or "between" in result.message.lower()

    @given(year=st.integers(min_value=2101))
    @settings(max_examples=100)
    def test_year_above_range_rejected(self, year: int):
        """For any year above 2100, validation should fail with error message."""
        result = validate_year(str(year))
        assert result.is_valid is False
        assert result.field == "year"
        assert result.message != ""
        assert "2100" in result.message or "between" in result.message.lower()

    @given(text=st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L',))))
    @settings(max_examples=100)
    def test_non_numeric_year_rejected(self, text: str):
        """For any non-numeric year string, validation should fail."""
        result = validate_year(text)
        assert result.is_valid is False
        assert result.field == "year"
        assert result.message != ""

    # --- Rating Validation Property Tests ---

    @given(rating=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_valid_rating_range_accepted(self, rating: float):
        """For any rating in range 0-10, validation should pass."""
        result = validate_rating(str(rating))
        assert result.is_valid is True
        assert result.field == "rating"

    @given(rating=st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_rating_below_range_rejected(self, rating: float):
        """For any rating below 0, validation should fail with error message."""
        result = validate_rating(str(rating))
        assert result.is_valid is False
        assert result.field == "rating"
        assert result.message != ""

    @given(rating=st.floats(min_value=10.01, max_value=1000, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_rating_above_range_rejected(self, rating: float):
        """For any rating above 10, validation should fail with error message."""
        result = validate_rating(str(rating))
        assert result.is_valid is False
        assert result.field == "rating"
        assert result.message != ""

    @given(text=st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L',))))
    @settings(max_examples=100)
    def test_non_numeric_rating_rejected(self, text: str):
        """For any non-numeric rating string, validation should fail."""
        result = validate_rating(text)
        assert result.is_valid is False
        assert result.field == "rating"
        assert result.message != ""

    # --- Runtime Validation Property Tests ---

    @given(runtime=st.integers(min_value=1, max_value=10000))
    @settings(max_examples=100)
    def test_valid_runtime_accepted(self, runtime: int):
        """For any positive runtime, validation should pass."""
        result = validate_runtime(str(runtime))
        assert result.is_valid is True
        assert result.field == "runtime"

    @given(runtime=st.integers(max_value=0))
    @settings(max_examples=100)
    def test_non_positive_runtime_rejected(self, runtime: int):
        """For any non-positive runtime, validation should fail with error message."""
        result = validate_runtime(str(runtime))
        assert result.is_valid is False
        assert result.field == "runtime"
        assert result.message != ""

    @given(text=st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L',))))
    @settings(max_examples=100)
    def test_non_numeric_runtime_rejected(self, text: str):
        """For any non-numeric runtime string, validation should fail."""
        result = validate_runtime(text)
        assert result.is_valid is False
        assert result.field == "runtime"
        assert result.message != ""

    # --- Empty Value Tests ---

    @given(whitespace=st.text(alphabet=' \t\n', max_size=10))
    @settings(max_examples=100)
    def test_empty_or_whitespace_year_accepted(self, whitespace: str):
        """Empty or whitespace-only year should be accepted (optional field)."""
        result = validate_year(whitespace)
        assert result.is_valid is True

    @given(whitespace=st.text(alphabet=' \t\n', max_size=10))
    @settings(max_examples=100)
    def test_empty_or_whitespace_rating_accepted(self, whitespace: str):
        """Empty or whitespace-only rating should be accepted (optional field)."""
        result = validate_rating(whitespace)
        assert result.is_valid is True

    @given(whitespace=st.text(alphabet=' \t\n', max_size=10))
    @settings(max_examples=100)
    def test_empty_or_whitespace_runtime_accepted(self, whitespace: str):
        """Empty or whitespace-only runtime should be accepted (optional field)."""
        result = validate_runtime(whitespace)
        assert result.is_valid is True

    # --- Full NfoData Validation Property Tests ---

    @given(
        year=st.integers(min_value=1900, max_value=2100).map(str),
        rating=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False).map(lambda x: f"{x:.1f}"),
        runtime=st.integers(min_value=1, max_value=1000).map(str)
    )
    @settings(max_examples=100)
    def test_valid_nfo_data_passes_validation(self, year: str, rating: str, runtime: str):
        """For any NfoData with valid field values, validation should pass."""
        data = NfoData(
            nfo_type=NfoType.MOVIE,
            year=year,
            rating=rating,
            runtime=runtime
        )
        is_valid, errors = validate_nfo_data(data)
        assert is_valid is True
        assert len(errors) == 0

    @given(
        year=st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L',))),
        rating=st.floats(min_value=10.01, max_value=100, allow_nan=False, allow_infinity=False).map(str),
        runtime=st.integers(max_value=0).map(str)
    )
    @settings(max_examples=100)
    def test_invalid_nfo_data_fails_validation(self, year: str, rating: str, runtime: str):
        """For any NfoData with all invalid field values, validation should fail
        and return error messages for each invalid field.
        """
        data = NfoData(
            nfo_type=NfoType.MOVIE,
            year=year,
            rating=rating,
            runtime=runtime
        )
        is_valid, errors = validate_nfo_data(data)
        assert is_valid is False
        assert len(errors) == 3
        
        # Verify each error has proper field and message
        error_fields = {e.field for e in errors}
        assert "year" in error_fields
        assert "rating" in error_fields
        assert "runtime" in error_fields
        
        for error in errors:
            assert error.message != ""
