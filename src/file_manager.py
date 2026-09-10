"""File manager module for batch file selection and LHS/RHS detection."""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WordFileInfo:
    """Stores metadata for a detected Word file."""
    path: str
    filename: str
    side: str  # 'LHS', 'RHS', or 'UNKNOWN'
    size_bytes: int
    status: str = "Ready"  # Ready, Processing, Completed, Error
    error_message: Optional[str] = None


class FileManager:
    """Manages file queue, folder scanning, and side detection."""

    VALID_EXTENSIONS = {".docx", ".doc"}

    def __init__(self):
        self.files: List[WordFileInfo] = []

    @staticmethod
    def detect_side(filename: str) -> str:
        """Detect LHS or RHS from filename in a case-insensitive manner.

        Args:
            filename: The name of the file (e.g. '01_LHS.docx').

        Returns:
            'LHS', 'RHS', or 'UNKNOWN'.
        """
        fn_upper = os.path.splitext(filename)[0].upper()
        
        # Word boundary or token check to prevent false substring collisions
        # Handles patterns like '01_LHS', 'LHS-01', 'Test_lhs.docx', 'LHS_km10', etc.
        has_lhs = "LHS" in fn_upper
        has_rhs = "RHS" in fn_upper

        if has_lhs and not has_rhs:
            return "LHS"
        elif has_rhs and not has_lhs:
            return "RHS"
        elif has_lhs and has_rhs:
            # Both mentioned; check which is more prominent or return UNKNOWN for review
            return "UNKNOWN"
        else:
            return "UNKNOWN"

    def add_file(self, file_path: str) -> Optional[WordFileInfo]:
        """Add a single file if valid and not already in list."""
        if not os.path.exists(file_path):
            return None

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        # Skip temporary Office lock files (e.g., ~$document.docx)
        if filename.startswith("~$") or ext not in self.VALID_EXTENSIONS:
            return None

        # Check duplicate by normalized absolute path
        abs_path = os.path.abspath(file_path)
        if any(os.path.abspath(f.path) == abs_path for f in self.files):
            return None

        side = self.detect_side(filename)
        size_bytes = os.path.getsize(file_path)

        info = WordFileInfo(
            path=abs_path,
            filename=filename,
            side=side,
            size_bytes=size_bytes
        )
        self.files.append(info)
        return info

    def add_files(self, file_paths: List[str]) -> int:
        """Add multiple files. Returns number of newly added files."""
        count = 0
        for p in file_paths:
            if self.add_file(p) is not None:
                count += 1
        return count

    def add_folder(self, folder_path: str, recursive: bool = False) -> int:
        """Scan a folder for all Word files. Returns count of added files."""
        if not os.path.isdir(folder_path):
            return 0

        added = 0
        if recursive:
            for root, _, filenames in os.walk(folder_path):
                for fn in sorted(filenames):
                    full = os.path.join(root, fn)
                    if self.add_file(full) is not None:
                        added += 1
        else:
            for fn in sorted(os.listdir(folder_path)):
                full = os.path.join(folder_path, fn)
                if os.path.isfile(full):
                    if self.add_file(full) is not None:
                        added += 1

        return added

    def remove_file(self, index: int) -> bool:
        """Remove file at specified index."""
        if 0 <= index < len(self.files):
            self.files.pop(index)
            return True
        return False

    def clear(self):
        """Clear all files."""
        self.files.clear()

    @property
    def total_count(self) -> int:
        return len(self.files)

    @property
    def lhs_files(self) -> List[WordFileInfo]:
        return [f for f in self.files if f.side == "LHS"]

    @property
    def rhs_files(self) -> List[WordFileInfo]:
        return [f for f in self.files if f.side == "RHS"]

    @property
    def unknown_files(self) -> List[WordFileInfo]:
        return [f for f in self.files if f.side == "UNKNOWN"]
