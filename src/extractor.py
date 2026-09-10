"""Data extraction engine for identifying and parsing D-records."""

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional
from src.word_reader import DocumentData


@dataclass
class ExtractedRecord:
    """Represents a single extracted D record."""
    side: str  # 'LHS' or 'RHS' or 'UNKNOWN'
    source_file: str
    d_value: str  # e.g. 'D100'
    chainage: float  # Numeric value used for ordering
    chainage_str: str  # Original string representation
    data_values: List[str] = field(default_factory=list)  # Associated data fields/columns


class Extractor:
    """Extracts records whose identifier/initial value begins with 'D'."""

    def __init__(self, prefix: str = "D"):
        self.prefix = prefix.upper().strip()

    @staticmethod
    def parse_chainage_number(text: str) -> Optional[float]:
        """Parses numeric chainage/station from text.
        
        Handles:
        - '100', '125.5'
        - '10+250' -> 10250 or 10.250
        - 'Km 125' -> 125.0
        - 'D125' -> 125.0
        """
        if not text:
            return None

        clean = text.strip()
        
        # Check for chainage with '+' (e.g. 12+500 -> 12.500 km or 12500 m)
        plus_match = re.search(r"(\d+)\s*\+\s*(\d+(?:\.\d+)?)", clean)
        if plus_match:
            try:
                km = float(plus_match.group(1))
                m = float(plus_match.group(2))
                return km * 1000.0 + m
            except ValueError:
                pass

        # Match standard integer or decimal number
        num_match = re.search(r"[-+]?\d+(?:\.\d+)?", clean)
        if num_match:
            try:
                return float(num_match.group(0))
            except ValueError:
                pass

        return None

    HEADER_KEYWORDS = {"station", "chainage", "deflection", "unit", "remark", "location", "layer", "distance", "ch.", "temp"}

    @classmethod
    def is_header_row(cls, row: List[str]) -> bool:
        """Determines if a table row is a header row rather than a data record."""
        if not row:
            return False
        # Count how many cells contain known header keywords or units like (mm), (kn), etc.
        header_matches = 0
        for cell in row:
            txt_lower = cell.strip().lower()
            if any(k in txt_lower for k in cls.HEADER_KEYWORDS) or "(" in txt_lower:
                header_matches += 1
        return header_matches >= 2 or (len(row) <= 2 and header_matches >= 1)

    def is_d_identifier(self, text: str) -> bool:
        """Check if cell/text is a valid D data record identifier (e.g., 'D100', 'D 125', 'D-500')."""
        if not text:
            return False
        clean = text.strip()
        # Reject column headers that have units like 'D0 (mm)', 'D300 (kN)', 'Depth (m)'
        if "(" in clean or ")" in clean:
            return False
        # Reject common words starting with D like 'Date', 'Deflection', 'Distance', 'Direction'
        if clean.lower() in {"date", "deflection", "deflections", "distance", "direction", "depth", "data"}:
            return False

        # Must start with prefix (e.g. 'D' or 'd') followed by digits (e.g., 'D100', 'D-100', 'D 100')
        pattern = rf"^{re.escape(self.prefix)}[\s\-_.:]*\d+(?:\.\d+)?$"
        return bool(re.match(pattern, clean, re.IGNORECASE))

    def extract_from_tables(self, doc_data: DocumentData, side: str) -> List[ExtractedRecord]:
        """Extract D records from Word tables."""
        records: List[ExtractedRecord] = []

        for table in doc_data.tables:
            if not table:
                continue

            # Detect if there is a header row with chainage/station
            header_chainage_idx = -1
            start_row_idx = 0

            # Check if row 0 is a header row
            if len(table) > 0 and self.is_header_row(table[0]):
                first_row = [str(c).lower() for c in table[0]]
                for idx, col_name in enumerate(first_row):
                    if any(k in col_name for k in ["chain", "ch.", "ch ", "km", "station", "location"]):
                        header_chainage_idx = idx
                        break
                start_row_idx = 1

            for row in table[start_row_idx:]:
                if not row or not any(row):
                    continue

                # Skip secondary header rows if repeated across pages
                if self.is_header_row(row):
                    continue

                # Find which cell contains the D-identifier
                d_cell_idx = -1
                d_val_str = ""
                for idx, cell in enumerate(row):
                    if self.is_d_identifier(cell):
                        d_cell_idx = idx
                        d_val_str = cell.strip()
                        break

                if d_cell_idx != -1:
                    # Determine chainage value
                    chainage = None
                    chain_str = ""

                    # First check if explicit chainage column was identified
                    if header_chainage_idx != -1 and header_chainage_idx < len(row) and header_chainage_idx != d_cell_idx:
                        candidate_txt = row[header_chainage_idx].strip()
                        parsed = self.parse_chainage_number(candidate_txt)
                        if parsed is not None:
                            chainage = parsed
                            chain_str = candidate_txt

                    # If not found yet, check adjacent cell (e.g., next column)
                    if chainage is None and d_cell_idx + 1 < len(row):
                        candidate_txt = row[d_cell_idx + 1].strip()
                        parsed = self.parse_chainage_number(candidate_txt)
                        if parsed is not None:
                            chainage = parsed
                            chain_str = candidate_txt

                    # If still not found, extract numeric part directly from D value (e.g., 'D125' -> 125)
                    if chainage is None:
                        parsed = self.parse_chainage_number(d_val_str)
                        if parsed is not None:
                            chainage = parsed
                            chain_str = str(parsed)
                        else:
                            chainage = 0.0
                            chain_str = "0"

                    # Collect remaining columns as data values
                    remaining_data = [cell for idx, cell in enumerate(row) if idx != d_cell_idx]

                    record = ExtractedRecord(
                        side=side,
                        source_file=doc_data.filename,
                        d_value=d_val_str,
                        chainage=chainage,
                        chainage_str=chain_str,
                        data_values=remaining_data
                    )
                    records.append(record)

        return records

    def extract_from_paragraphs(self, doc_data: DocumentData, side: str) -> List[ExtractedRecord]:
        """Extract D records from text paragraphs if no tables or additional records exist."""
        records: List[ExtractedRecord] = []

        for p in doc_data.paragraphs:
            clean = p.strip()
            # Split by whitespace, comma, or tab
            tokens = re.split(r"[\t,;]+", clean)
            for token in tokens:
                token_strip = token.strip()
                if self.is_d_identifier(token_strip):
                    parsed = self.parse_chainage_number(token_strip)
                    chainage = parsed if parsed is not None else 0.0
                    
                    # Remaining line text
                    records.append(ExtractedRecord(
                        side=side,
                        source_file=doc_data.filename,
                        d_value=token_strip,
                        chainage=chainage,
                        chainage_str=str(chainage),
                        data_values=[clean]
                    ))

        return records

    def extract(self, doc_data: DocumentData, side: str) -> List[ExtractedRecord]:
        """Extract all D records from a document (prioritizing tables, then paragraphs)."""
        table_records = self.extract_from_tables(doc_data, side)
        if table_records:
            return table_records

        # Fallback to paragraphs if no table records were found
        return self.extract_from_paragraphs(doc_data, side)
