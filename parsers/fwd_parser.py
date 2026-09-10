"""FWD instrument survey data parser (.fwd) for FWD Data Converter Pro."""

import os
import re
from typing import List
from core.data_model import FWDRecord
from parsers.base_parser import BaseParser


class FWDParser(BaseParser):
    """Parses raw FWD equipment data files (.fwd) (Dynatest / KUAB / Carl Bro / FastFWD)."""

    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        records: List[FWDRecord] = []
        filename = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception:
            return records

        header_mapping = {}

        for line_idx, line in enumerate(lines):
            # Check for standard header line
            tokens = [t.strip() for t in re.split(r",|\t|\s{2,}", line) if t.strip()]
            if not tokens:
                tokens = line.split()

            if len(tokens) >= 4 and not header_mapping:
                cand_map = self.match_header_columns(tokens)
                if len(cand_map) >= 2:
                    header_mapping = cand_map
                    continue

            # Look for explicit D station or numeric test drop
            stn_id = ""
            d_idx = -1
            for idx, t in enumerate(tokens):
                if self.is_d_identifier(t):
                    stn_id = t
                    d_idx = idx
                    break

            # If no D tag, check if line is a standard FWD data drop line (e.g. Station, Force, D0..D6)
            if not stn_id:
                # If first token is numeric station or chainage like '100', '105.0', '10+250'
                if tokens and self.parse_chainage_number(tokens[0]) is not None:
                    # Synthesize D-id: e.g. D100
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

            # Extract numeric tokens
            numeric_vals = []
            for idx, t in enumerate(tokens):
                if idx != d_idx:
                    f_val = self.parse_float(t)
                    if f_val is not None:
                        numeric_vals.append(f_val)

            if numeric_vals:
                # If values > 50, deflections are likely in microns, normalize to mm
                # Check if first is load around 20-60 kN
                start_d = 0
                if 15.0 <= numeric_vals[0] <= 150.0 and len(numeric_vals) > 1:
                    rec.force = numeric_vals[0]
                    start_d = 1

                for d_i, n_val in enumerate(numeric_vals[start_d:start_d + 7]):
                    # If microns (>50), convert to mm
                    if n_val > 50.0:
                        n_val = n_val / 1000.0
                    setattr(rec, f"d{d_i}", n_val)

            rec.extra_data = [t for idx, t in enumerate(tokens) if idx != d_idx]
            records.append(rec)

        return records
