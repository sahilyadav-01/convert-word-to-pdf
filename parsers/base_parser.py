"""Base Parser with shared utilities for all file formats."""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.data_model import FWDRecord


class BaseParser(ABC):
    """Abstract base parser defining interface and shared extraction helpers."""

    def __init__(self, prefix: str = "D"):
        self.prefix = prefix.upper().strip()

    @abstractmethod
    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        """Parse file and return list of standard FWDRecord items."""
        pass

    @staticmethod
    def parse_chainage_number(text: str) -> Optional[float]:
        """Parse numeric chainage from string like '10+250', '125.5', 'Km 10'."""
        if not text:
            return None
        clean = str(text).strip()

        # Handle '+' notation (e.g. 10+250 -> 10250.0 m)
        plus_match = re.search(r"(\d+)\s*\+\s*(\d+(?:\.\d+)?)", clean)
        if plus_match:
            try:
                km = float(plus_match.group(1))
                m = float(plus_match.group(2))
                return km * 1000.0 + m
            except ValueError:
                pass

        # Match standard number
        num_match = re.search(r"[-+]?\d+(?:\.\d+)?", clean)
        if num_match:
            try:
                return float(num_match.group(0))
            except ValueError:
                pass

        return None

    @staticmethod
    def parse_float(val: any) -> Optional[float]:
        """Converts string/numeric cell to float safely."""
        if val is None:
            return None
        s = str(val).strip()
        if not s:
            return None
        match = re.search(r"[-+]?\d+(?:\.\d+)?", s)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                pass
        return None

    def is_d_identifier(self, text: str) -> bool:
        """Checks if text begins with the required prefix (e.g. 'D100', 'D 125', 'D-500')."""
        if not text:
            return False
        clean = str(text).strip()
        # Exclude column headers like 'D0 (mm)'
        if "(" in clean or ")" in clean:
            return False
        if clean.lower() in {"date", "deflection", "distance", "direction", "depth", "data"}:
            return False

        pattern = rf"^{re.escape(self.prefix)}[\s\-_.:]*\d+(?:\.\d+)?$"
        return bool(re.match(pattern, clean, re.IGNORECASE))

    @classmethod
    def match_header_columns(cls, header_row: List[str]) -> Dict[str, int]:
        """Maps standard FWD fields to column indices based on header names."""
        mapping: Dict[str, int] = {}
        for idx, col in enumerate(header_row):
            txt = str(col).strip().lower()

            if any(k in txt for k in ["station id", "stn id", "point", "stn_id"]):
                mapping.setdefault("station_id", idx)
            elif any(k in txt for k in ["chainage", "station", "location", "ch.", "ch "]):
                mapping.setdefault("station", idx)
            elif any(k in txt for k in ["force", "load", "target load"]):
                mapping.setdefault("force", idx)
            elif txt in ["d0", "d 0", "d0 (mm)", "d0(mm)", "sensor 1", "d(0)"]:
                mapping.setdefault("d0", idx)
            elif txt in ["d1", "d 1", "d1 (mm)", "d1(mm)", "sensor 2", "d(1)", "d200", "d300"]:
                mapping.setdefault("d1", idx)
            elif txt in ["d2", "d 2", "d2 (mm)", "sensor 3", "d(2)", "d600"]:
                mapping.setdefault("d2", idx)
            elif txt in ["d3", "d 3", "d3 (mm)", "sensor 4", "d(3)", "d900"]:
                mapping.setdefault("d3", idx)
            elif txt in ["d4", "d 4", "d4 (mm)", "sensor 5", "d(4)", "d1200"]:
                mapping.setdefault("d4", idx)
            elif txt in ["d5", "d 5", "d5 (mm)", "sensor 6", "d(5)", "d1500"]:
                mapping.setdefault("d5", idx)
            elif txt in ["d6", "d 6", "d6 (mm)", "sensor 7", "d(6)", "d1800"]:
                mapping.setdefault("d6", idx)
            elif any(k in txt for k in ["air temp", "ta"]):
                mapping.setdefault("air_temp", idx)
            elif any(k in txt for k in ["asphalt temp", "pavement temp", "surface temp", "tp"]):
                mapping.setdefault("asphalt_temp", idx)
            elif "lat" in txt:
                mapping.setdefault("lat", idx)
            elif any(k in txt for k in ["long", "lon"]):
                mapping.setdefault("long", idx)
            elif "time" in txt:
                mapping.setdefault("time", idx)
            elif any(k in txt for k in ["remark", "note"]):
                mapping.setdefault("remarks", idx)

        return mapping
