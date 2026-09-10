"""File format and LHS/RHS side detection engine."""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InputFileInfo:
    """Stores metadata for a detected input file."""
    path: str
    filename: str
    format: str     # 'WORD', 'PDF', 'CSV', 'EXCEL', 'TXT', 'FWD', 'UNKNOWN'
    side: str       # 'LHS', 'RHS', 'UNKNOWN'
    size_bytes: int
    status: str = "Ready"  # Ready, Processing, Completed, Error
    error_message: Optional[str] = None


class Detector:
    """Detects file format and road side (LHS/RHS)."""

    FORMAT_EXTENSIONS = {
        ".docx": "WORD",
        ".doc": "WORD",
        ".pdf": "PDF",
        ".csv": "CSV",
        ".xlsx": "EXCEL",
        ".xls": "EXCEL",
        ".txt": "TXT",
        ".fwd": "FWD"
    }

    @classmethod
    def detect_format(cls, filename: str) -> str:
        """Determines format from file extension."""
        ext = os.path.splitext(filename)[1].lower()
        return cls.FORMAT_EXTENSIONS.get(ext, "UNKNOWN")

    @staticmethod
    def detect_side(filename: str) -> str:
        """Detect LHS or RHS from filename in a case-insensitive manner."""
        fn_upper = os.path.splitext(filename)[0].upper()
        has_lhs = "LHS" in fn_upper
        has_rhs = "RHS" in fn_upper

        if has_lhs and not has_rhs:
            return "LHS"
        elif has_rhs and not has_lhs:
            return "RHS"
        else:
            return "UNKNOWN"

    @classmethod
    def inspect_file(cls, file_path: str) -> Optional[InputFileInfo]:
        """Inspects and creates an InputFileInfo if valid."""
        if not os.path.exists(file_path):
            return None

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        # Skip temporary Office lock files
        if filename.startswith("~$") or ext not in cls.FORMAT_EXTENSIONS:
            return None

        fmt = cls.detect_format(filename)
        side = cls.detect_side(filename)
        size_bytes = os.path.getsize(file_path)

        return InputFileInfo(
            path=os.path.abspath(file_path),
            filename=filename,
            format=fmt,
            side=side,
            size_bytes=size_bytes
        )
