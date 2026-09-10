"""FWD instrument survey data parser (.fwd) for FWD Data Converter Pro."""

import os
import re
from typing import List
from core.data_model import FWDRecord
from parsers.base_parser import BaseParser


class FWDParser(BaseParser):
    """Parses raw FWD equipment data files (.fwd) including KUAB, Dynatest, Carl Bro."""

    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        records: List[FWDRecord] = []
        filename = os.path.basename(file_path)

        text = self.read_text_file(file_path)
        if not text:
            return records

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            # Skip comments and header lines starting with 'I', 'H', 'J', 'C'
            if line.startswith(("I", "H", "J", "C", "*", "#")):
                continue

            # Skip header description lines containing column titles
            line_lower = line.lower()
            if any(k in line_lower for k in ["station", "force", "load", "chainage"]) and any(k in line_lower for k in ["d0", "d1", "sensor", "deflection"]):
                continue

            tokens = [t.strip() for t in re.split(r",|\t|\s+", line) if t.strip()]
            if not tokens:
                continue

            # Standard KUAB line check: starts with 'D' followed by numeric distance
            # e.g.: D   15050   2  43.5   326   263   224   171   128    89    58 26.5 30.0    424   2545.56166  07639.58785 13:16:18
            if tokens[0].upper() == "D" and len(tokens) >= 5:
                # tokens[1] is Distance/Chainage
                dist_val = self.parse_chainage_number(tokens[1])
                if dist_val is not None:
                    # Valid KUAB record
                    drop_num = tokens[2] if len(tokens) > 2 else ""
                    load_val = self.parse_float(tokens[3]) if len(tokens) > 3 else None

                    rec = FWDRecord(
                        side=side,
                        station_id=f"D{int(dist_val)}",
                        station=dist_val,
                        station_str=tokens[1],
                        force=load_val,
                        source_file=filename,
                        source_format="FWD"
                    )

                    # Deflections D0 to D6 (tokens 4 to 10 in KUAB)
                    for d_i in range(7):
                        t_idx = 4 + d_i
                        if t_idx < len(tokens):
                            raw_d = self.parse_float(tokens[t_idx])
                            if raw_d is not None:
                                # Convert microns (µm) to mm if > 5.0
                                if raw_d > 5.0:
                                    raw_d = raw_d / 1000.0
                                setattr(rec, f"d{d_i}", round(raw_d, 4))

                    # Temperatures (tokens 11, 12 in KUAB)
                    if len(tokens) > 11:
                        rec.air_temp = self.parse_float(tokens[11])
                    if len(tokens) > 12:
                        rec.asphalt_temp = self.parse_float(tokens[12])

                    # Emod (token 13 in KUAB)
                    emod_str = ""
                    if len(tokens) > 13:
                        emod_str = tokens[13]

                    # GPS Coordinates (tokens 14, 15)
                    if len(tokens) > 14:
                        rec.lat = self.parse_float(tokens[14])
                    if len(tokens) > 15:
                        rec.long = self.parse_float(tokens[15])

                    # Time (token 16)
                    if len(tokens) > 16:
                        rec.time = tokens[16]

                    rem_parts = []
                    if drop_num:
                        rem_parts.append(f"Drop {drop_num}")
                    if emod_str:
                        rem_parts.append(f"Emod {emod_str} MPa")
                    rec.remarks = ", ".join(rem_parts)

                    records.append(rec)
                    continue

            # Fallback for generic/Dynatest lines where token itself is D... e.g. D100, D105
            stn_id = ""
            d_idx = -1
            for idx, t in enumerate(tokens):
                if self.is_d_identifier(t):
                    stn_id = t
                    d_idx = idx
                    break

            if not stn_id and tokens and self.parse_chainage_number(tokens[0]) is not None:
                stn_val = self.parse_chainage_number(tokens[0])
                stn_id = f"D{int(stn_val)}"
                d_idx = 0

            if not stn_id:
                continue

            chainage = self.parse_chainage_number(stn_id)
            if chainage is None and d_idx != -1 and d_idx < len(tokens):
                chainage = self.parse_chainage_number(tokens[d_idx])

            rec = FWDRecord(
                side=side,
                station_id=stn_id,
                station=chainage if chainage is not None else 0.0,
                station_str=str(chainage if chainage is not None else "0"),
                source_file=filename,
                source_format="FWD"
            )

            numeric_vals = []
            for idx, t in enumerate(tokens):
                if idx != d_idx:
                    f_val = self.parse_float(t)
                    if f_val is not None:
                        numeric_vals.append(f_val)

            if numeric_vals:
                start_d = 0
                if 15.0 <= numeric_vals[0] <= 150.0 and len(numeric_vals) > 1:
                    rec.force = numeric_vals[0]
                    start_d = 1

                for d_i, n_val in enumerate(numeric_vals[start_d:start_d + 7]):
                    if n_val > 5.0:
                        n_val = n_val / 1000.0
                    setattr(rec, f"d{d_i}", round(n_val, 4))

            rec.extra_data = [t for idx, t in enumerate(tokens) if idx != d_idx]
            records.append(rec)

        return records
