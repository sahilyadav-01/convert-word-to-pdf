"""Word document parser (.docx / .doc) for FWD Data Converter Pro."""

import os
from typing import List
import docx
from core.data_model import FWDRecord
from parsers.base_parser import BaseParser


class WordParser(BaseParser):
    """Parses Microsoft Word files (.docx / .doc)."""

    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        records: List[FWDRecord] = []
        filename = os.path.basename(file_path)

        try:
            doc = docx.Document(file_path)
        except Exception:
            return records

        for table in doc.tables:
            if not table.rows:
                continue

            # Header detection
            header_row = [cell.text.strip() for cell in table.rows[0].cells]
            mapping = self.match_header_columns(header_row)
            start_idx = 1 if len(mapping) >= 2 else 0

            for row in table.rows[start_idx:]:
                cells = [c.text.strip() for c in row.cells]
                if not any(cells):
                    continue

                # Identify if any cell is a D record or matches header map
                stn_id = ""
                d_idx = -1
                for idx, c in enumerate(cells):
                    if self.is_d_identifier(c):
                        stn_id = c
                        d_idx = idx
                        break

                # If no direct D identifier, check if station column has D...
                if not stn_id and "station" in mapping and mapping["station"] < len(cells):
                    cand = cells[mapping["station"]]
                    if self.is_d_identifier(cand):
                        stn_id = cand

                if not stn_id:
                    continue

                # Determine chainage
                chainage = None
                chain_str = ""
                if "station" in mapping and mapping["station"] < len(cells) and mapping["station"] != d_idx:
                    chain_str = cells[mapping["station"]]
                    chainage = self.parse_chainage_number(chain_str)

                if chainage is None:
                    chainage = self.parse_chainage_number(stn_id)
                    chain_str = str(chainage if chainage is not None else "0")

                rec = FWDRecord(
                    side=side,
                    station_id=stn_id,
                    station=chainage if chainage is not None else 0.0,
                    station_str=chain_str,
                    source_file=filename,
                    source_format="WORD"
                )

                # Populate mapped attributes if available
                if "force" in mapping and mapping["force"] < len(cells):
                    rec.force = self.parse_float(cells[mapping["force"]])
                for d_i in range(7):
                    key = f"d{d_i}"
                    if key in mapping and mapping[key] < len(cells):
                        setattr(rec, key, self.parse_float(cells[mapping[key]]))

                if "air_temp" in mapping and mapping["air_temp"] < len(cells):
                    rec.air_temp = self.parse_float(cells[mapping["air_temp"]])
                if "asphalt_temp" in mapping and mapping["asphalt_temp"] < len(cells):
                    rec.asphalt_temp = self.parse_float(cells[mapping["asphalt_temp"]])
                if "lat" in mapping and mapping["lat"] < len(cells):
                    rec.lat = self.parse_float(cells[mapping["lat"]])
                if "long" in mapping and mapping["long"] < len(cells):
                    rec.long = self.parse_float(cells[mapping["long"]])
                if "time" in mapping and mapping["time"] < len(cells):
                    rec.time = cells[mapping["time"]]
                if "remarks" in mapping and mapping["remarks"] < len(cells):
                    rec.remarks = cells[mapping["remarks"]]

                # If no sensor mappings were found, collect remaining cells as extra data
                if not any(getattr(rec, f"d{i}") for i in range(7)):
                    rec.extra_data = [c for idx, c in enumerate(cells) if idx != d_idx]

                records.append(rec)

        return records
