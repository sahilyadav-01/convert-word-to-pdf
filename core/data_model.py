"""Common Data Model for FWD Data Converter Pro."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FWDRecord:
    """Standardized representation of an FWD test record across all formats."""
    side: str = "UNKNOWN"               # 'LHS', 'RHS', or 'UNKNOWN'
    station_id: str = ""                # e.g., 'D100', 'D105', 'D001'
    station: float = 0.0                # Numeric station / chainage value for sorting
    station_str: str = ""               # Original representation e.g. '100', '10+250', 'Km 12.5'
    force: Optional[float] = None       # Impact load in kN (e.g. 40.0)
    d0: Optional[float] = None          # Deflection sensor 0 (mm or microns)
    d1: Optional[float] = None          # Deflection sensor 1
    d2: Optional[float] = None          # Deflection sensor 2
    d3: Optional[float] = None          # Deflection sensor 3
    d4: Optional[float] = None          # Deflection sensor 4
    d5: Optional[float] = None          # Deflection sensor 5
    d6: Optional[float] = None          # Deflection sensor 6
    air_temp: Optional[float] = None    # Air temperature in °C
    asphalt_temp: Optional[float] = None# Pavement / asphalt temperature in °C
    lat: Optional[float] = None         # Latitude
    long: Optional[float] = None        # Longitude
    time: str = ""                      # Survey time / timestamp
    remarks: str = ""                   # Observations / notes
    source_file: str = ""               # Origin filename
    source_format: str = ""             # 'WORD', 'PDF', 'CSV', 'EXCEL', 'TXT', 'FWD'
    extra_data: List[str] = field(default_factory=list)  # Any additional unmapped columns

    def to_row(self) -> List[Any]:
        """Convert record to tabular row for Excel output."""
        return [
            self.side,
            self.station_id,
            self.station,
            self.force if self.force is not None else "",
            self.d0 if self.d0 is not None else "",
            self.d1 if self.d1 is not None else "",
            self.d2 if self.d2 is not None else "",
            self.d3 if self.d3 is not None else "",
            self.d4 if self.d4 is not None else "",
            self.d5 if self.d5 is not None else "",
            self.d6 if self.d6 is not None else "",
            self.air_temp if self.air_temp is not None else "",
            self.asphalt_temp if self.asphalt_temp is not None else "",
            self.lat if self.lat is not None else "",
            self.long if self.long is not None else "",
            self.time,
            self.source_file,
            self.source_format,
            self.remarks
        ] + list(self.extra_data)

    @classmethod
    def get_standard_headers(cls) -> List[str]:
        """Returns standard table headers for Sheet 1."""
        return [
            "Side",
            "Station ID",
            "Station / Chainage",
            "Force (kN)",
            "D0 (mm)",
            "D1",
            "D2",
            "D3",
            "D4",
            "D5",
            "D6",
            "Air Temp (°C)",
            "Pavement Temp (°C)",
            "Latitude",
            "Longitude",
            "Time",
            "Source File",
            "Source Format",
            "Remarks"
        ]
