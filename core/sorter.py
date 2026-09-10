"""Directional sorting engine for Common FWD Data Model."""

from typing import List, Tuple
from core.data_model import FWDRecord


class DirectionalSorter:
    """Sorts LHS records in increasing order and RHS records in decreasing order."""

    @staticmethod
    def sort(records: List[FWDRecord]) -> List[FWDRecord]:
        """Sorts FWD records according to directional highway chainage:
        
        1. LHS records: Sorted by station / chainage in ASCENDING (increasing) order.
        2. RHS records: Sorted by station / chainage in DESCENDING (decreasing) order.
        3. UNKNOWN records: Preserved at the end.
        4. Returns LHS + RHS + UNKNOWN.
        """
        lhs = [r for r in records if r.side.upper() == "LHS"]
        rhs = [r for r in records if r.side.upper() == "RHS"]
        unknown = [r for r in records if r.side.upper() not in ("LHS", "RHS")]

        lhs_sorted = sorted(lhs, key=lambda x: (x.station, x.station_id, x.source_file))
        rhs_sorted = sorted(rhs, key=lambda x: (-x.station, x.station_id, x.source_file))

        return lhs_sorted + rhs_sorted + unknown

    @classmethod
    def split_and_sort(cls, records: List[FWDRecord]) -> Tuple[List[FWDRecord], List[FWDRecord], List[FWDRecord]]:
        """Returns sorted tuples: (lhs_sorted, rhs_sorted, unknown_records)."""
        lhs = [r for r in records if r.side.upper() == "LHS"]
        rhs = [r for r in records if r.side.upper() == "RHS"]
        unknown = [r for r in records if r.side.upper() not in ("LHS", "RHS")]

        lhs_sorted = sorted(lhs, key=lambda x: (x.station, x.station_id, x.source_file))
        rhs_sorted = sorted(rhs, key=lambda x: (-x.station, x.station_id, x.source_file))

        return lhs_sorted, rhs_sorted, unknown
