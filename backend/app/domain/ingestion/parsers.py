"""
Parsers for CSV and XLSX files.
"""
import pandas as pd
from typing import List, Dict, Any
from io import BytesIO
import hashlib


class FileParser:
    """Parser for CSV and XLSX files."""
    
    @staticmethod
    def parse_csv(content: bytes) -> pd.DataFrame:
        """
        Parse CSV file content.
        
        Args:
            content: CSV file bytes
            
        Returns:
            pandas DataFrame
        """
        return pd.read_csv(BytesIO(content))
    
    @staticmethod
    def parse_xlsx(content: bytes) -> pd.DataFrame:
        """
        Parse XLSX file content.
        
        Args:
            content: XLSX file bytes
            
        Returns:
            pandas DataFrame (from first sheet)
        """
        return pd.read_excel(BytesIO(content), engine='openpyxl')
    
    @staticmethod
    def parse_file(content: bytes, filename: str) -> pd.DataFrame:
        """
        Parse file based on extension.
        
        Args:
            content: File bytes
            filename: Original filename
            
        Returns:
            pandas DataFrame
        """
        if filename.lower().endswith('.csv'):
            return FileParser.parse_csv(content)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            return FileParser.parse_xlsx(content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    
    @staticmethod
    def compute_checksum(content: bytes) -> str:
        """
        Compute SHA256 checksum of file content.
        
        Args:
            content: File bytes
            
        Returns:
            SHA256 hex digest
        """
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def dataframe_to_dict_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to list of dictionaries.
        
        Args:
            df: pandas DataFrame
            
        Returns:
            List of row dictionaries
        """
        # Replace NaN with None
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
