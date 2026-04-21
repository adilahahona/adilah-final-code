"""
Validators for ingestion data.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import pandas as pd


class IndicatorRow(BaseModel):
    """Single indicator row from uploaded file."""
    org_name: str = Field(..., min_length=1)
    period_start: str  # Will be parsed to datetime
    period_end: str  # Will be parsed to datetime
    indicator_code: str = Field(..., min_length=1)
    value: str  # Can be numeric or text
    unit: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('period_start', 'period_end')
    @classmethod
    def validate_date(cls, v):
        """Validate date string can be parsed."""
        if not v:
            raise ValueError("Date cannot be empty")
        # Will be parsed during ingestion
        return v


class ValidationError(BaseModel):
    """Validation error for a single row."""
    row_number: int
    field: Optional[str] = None
    error: str
    value: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of validation."""
    valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[ValidationError] = []


class IndicatorRowValidator:
    """Validator for indicator rows."""
    
    REQUIRED_COLUMNS = [
        "org_name",
        "period_start",
        "period_end",
        "indicator_code",
        "value"
    ]
    
    OPTIONAL_COLUMNS = ["unit", "source", "notes"]
    
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        strict: bool = True
    ) -> ValidationResult:
        """
        Validate a pandas DataFrame.
        
        Args:
            df: DataFrame to validate
            strict: If True, reject rows with any errors
            
        Returns:
            ValidationResult
        """
        errors = []
        valid_count = 0
        invalid_count = 0
        
        # Check required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            return ValidationResult(
                valid=False,
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                errors=[ValidationError(
                    row_number=0,
                    field="columns",
                    error=f"Missing required columns: {', '.join(missing_cols)}"
                )]
            )
        
        # Validate each row
        for idx, row in df.iterrows():
            row_errors = []
            row_num = idx + 2  # Account for header and 0-indexing
            
            # Check required fields
            for col in self.REQUIRED_COLUMNS:
                if pd.isna(row[col]) or str(row[col]).strip() == "":
                    row_errors.append(ValidationError(
                        row_number=row_num,
                        field=col,
                        error=f"Required field '{col}' is empty",
                        value=str(row[col])
                    ))
            
            # Validate dates
            for date_col in ["period_start", "period_end"]:
                if not pd.isna(row[date_col]):
                    try:
                        pd.to_datetime(row[date_col])
                    except Exception as e:
                        row_errors.append(ValidationError(
                            row_number=row_num,
                            field=date_col,
                            error=f"Invalid date format: {str(e)}",
                            value=str(row[date_col])
                        ))
            
            # Validate value can be parsed (try numeric first)
            if not pd.isna(row["value"]):
                value_str = str(row["value"]).strip()
                if value_str:
                    # Try to parse as numeric
                    try:
                        float(value_str)
                    except ValueError:
                        # Non-numeric is OK, just note it
                        pass
            
            if row_errors:
                errors.extend(row_errors)
                invalid_count += 1
            else:
                valid_count += 1
        
        return ValidationResult(
            valid=invalid_count == 0,
            total_rows=len(df),
            valid_rows=valid_count,
            invalid_rows=invalid_count,
            errors=errors
        )
