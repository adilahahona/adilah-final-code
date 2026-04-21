"""
PDF Document Parser for ESG Reports

Extracts text content from PDF files using PyPDF2.
"""
from typing import Dict, List, Optional
from pathlib import Path
import re
from PyPDF2 import PdfReader


class PDFParser:
    """Extracts text and metadata from PDF documents."""

    def parse(self, file_path: Path) -> Dict:
        """
        Parse a PDF file and extract text content.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing extracted content and metadata
        """
        reader = PdfReader(str(file_path))
        
        # Extract metadata
        metadata = self._extract_metadata(reader)
        
        # Extract text from all pages
        pages = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            pages.append({
                'page_number': page_num,
                'text': text,
                'word_count': len(text.split())
            })
        
        # Combine all text
        full_text = '\n\n'.join([p['text'] for p in pages])
        
        return {
            'metadata': metadata,
            'pages': pages,
            'full_text': full_text,
            'total_pages': len(pages),
            'total_words': sum(p['word_count'] for p in pages)
        }

    def _extract_metadata(self, reader: PdfReader) -> Dict:
        """Extract PDF metadata."""
        metadata = {}
        if reader.metadata:
            metadata = {
                'title': reader.metadata.get('/Title', ''),
                'author': reader.metadata.get('/Author', ''),
                'subject': reader.metadata.get('/Subject', ''),
                'creator': reader.metadata.get('/Creator', ''),
                'producer': reader.metadata.get('/Producer', ''),
                'creation_date': str(reader.metadata.get('/CreationDate', '')),
                'modification_date': str(reader.metadata.get('/ModDate', ''))
            }
        return metadata

    def search_text(self, file_path: Path, pattern: str) -> List[Dict]:
        """
        Search for text patterns in the PDF.

        Args:
            file_path: Path to the PDF file
            pattern: Regex pattern to search for

        Returns:
            List of matches with page numbers and context
        """
        reader = PdfReader(str(file_path))
        matches = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get context around match (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                matches.append({
                    'page': page_num,
                    'match': match.group(),
                    'context': context,
                    'position': match.start()
                })
        
        return matches

    def extract_tables(self, file_path: Path) -> List[Dict]:
        """
        Attempt to extract table-like structures from the PDF.

        Note: This is a basic implementation. For better table extraction,
        consider using libraries like tabula-py or camelot-py.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of potential table structures
        """
        reader = PdfReader(str(file_path))
        tables = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            
            # Simple heuristic: lines with multiple tab or pipe separators
            lines = text.split('\n')
            potential_table = []
            
            for line in lines:
                # Check if line has multiple separators (tabs, pipes, or multiple spaces)
                if '\t' in line or '|' in line or re.search(r' {3,}', line):
                    potential_table.append(line)
                elif potential_table:
                    # End of table
                    if len(potential_table) >= 3:  # At least header + 2 rows
                        tables.append({
                            'page': page_num,
                            'rows': potential_table,
                            'row_count': len(potential_table)
                        })
                    potential_table = []
            
            # Check if table extends to end of page
            if len(potential_table) >= 3:
                tables.append({
                    'page': page_num,
                    'rows': potential_table,
                    'row_count': len(potential_table)
                })
        
        return tables
