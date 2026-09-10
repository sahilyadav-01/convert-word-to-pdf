"""Data validation engine for FWD records."""

from typing import Dict, List, Tuple
from core.data_model import FWDRecord


class Validator:
    """Validates extracted FWD records for common data anomalies."""

    @staticmethod
    def validate(records: List[FWDRecord]) -> Tuple[List[FWDRecord], List[Dict[str, str]]]:
        """Validates a list of FWD records.
        
        Returns:
            (valid_records, logs)
        """
        valid_records: List[FWDRecord] = []
        logs: List[Dict[str, str]] = []
        seen_stations = set()

        for idx, r in enumerate(records):
            key = (r.side.upper(), r.station)

            # Check for duplicate station on same side
            if key in seen_stations and r.station > 0:
                logs.append({
                    "file": r.source_file,
                    "level": "WARNING",
                    "message": f"Duplicate test station detected at Ch: {r.station} on {r.side}.",
                    "action": "Preserved duplicate in output."
                })
            seen_stations.add(key)

            # Validate deflection bounds
            if r.d0 is not None and (r.d0 < 0 or r.d0 > 5.0):
                # If deflection is in microns (e.g. 550 microns), normalize to mm if needed or flag
                if r.d0 > 50.0:
                    r.d0 = r.d0 / 1000.0  # converted from microns to mm

            valid_records.append(r)

        return valid_records, logs
