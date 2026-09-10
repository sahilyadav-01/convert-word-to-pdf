"""Sorting engine for directional chainage ordering."""

from typing import List, Tuple
from src.extractor import ExtractedRecord


class Sorter:
    """Sorts LHS records in increasing order and RHS records in decreasing order."""

    @staticmethod
    def sort_records(records: List[ExtractedRecord]) -> List[ExtractedRecord]:
        """Sorts records according to the project specification:
        
        1. Separate records into LHS, RHS, and UNKNOWN.
        2. LHS records: Sorted by chainage in ASCENDING (increasing) order.
        3. RHS records: Sorted by chainage in DESCENDING (decreasing) order.
        4. UNKNOWN records: Preserved in stable order at the end.
        5. Combine: LHS (increasing) + RHS (decreasing) + UNKNOWN.
        """
        lhs: List[ExtractedRecord] = []
        rhs: List[ExtractedRecord] = []
        unknown: List[ExtractedRecord] = []

        for r in records:
            side_norm = r.side.upper().strip()
            if side_norm == "LHS":
                lhs.append(r)
            elif side_norm == "RHS":
                rhs.append(r)
            else:
                unknown.append(r)

        # LHS: Increasing chainage / change (Ascending)
        lhs_sorted = sorted(lhs, key=lambda x: (x.chainage, x.d_value, x.source_file))

        # RHS: Decreasing chainage / change (Descending)
        rhs_sorted = sorted(rhs, key=lambda x: (-x.chainage, x.d_value, x.source_file))

        return lhs_sorted + rhs_sorted + unknown

    @classmethod
    def split_and_sort(cls, records: List[ExtractedRecord]) -> Tuple[List[ExtractedRecord], List[ExtractedRecord], List[ExtractedRecord]]:
        """Returns sorted (lhs_sorted, rhs_sorted, unknown_records)."""
        lhs = [r for r in records if r.side.upper() == "LHS"]
        rhs = [r for r in records if r.side.upper() == "RHS"]
        unknown = [r for r in records if r.side.upper() not in ("LHS", "RHS")]

        lhs_sorted = sorted(lhs, key=lambda x: (x.chainage, x.d_value, x.source_file))
        rhs_sorted = sorted(rhs, key=lambda x: (-x.chainage, x.d_value, x.source_file))

        return lhs_sorted, rhs_sorted, unknown
