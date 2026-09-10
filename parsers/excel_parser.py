"""Excel parser (.xlsx / .xls) for FWD Data Converter Pro."""

import os
from typing import List
import openpyxl
from core.data_model import FWDRecord
from parsers.base_parser import BaseParser


class ExcelParser(BaseParser):
    """Parses Excel workbooks (.xlsx / .xls)."""

    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        records: List[FWDRecord] = []
        filename = os.path.basename(file_path)

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception:
            return records

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue

            # Check header row
            header_mapping = {}
            for r_idx in range(min(5, len(rows))):
                candidate_header = [str(c or "").strip() for c in rows[r_idx]]
                mapping = self.match_header_columns(candidate_header)
                if len(mapping) >= 2:
                    header_mapping = mapping
                    start_row = r_idx + 1
                    break
            else:
                start_row = 0

            for row in rows[start_row:]:
                cells = [str(c or "").strip() for c in row]
                if not any(cells):
                    continue

                stn_id = ""
                d_idx = -1
                for idx, c in enumerate(cells):
                    if self.is_d_identifier(c):
                        stn_id = c
                        d_idx = idx
                        break

                if not stn_id and "station" in header_mapping and header_mapping["station"] < len(cells):
                    cand = cells[header_mapping["station"]]
                    if self.is_d_identifier(cand):
                        stn_id = cand
                        d_idx = header_mapping["station"]

                if not stn_id:
                    continue

                # Parse chainage
                chainage = None
                chain_str = ""
                if "station" in header_mapping and header_mapping["station"] < len(cells) and header_mapping["station"] != d_idx:
                    chain_str = cells[header_mapping["station"]]
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
                    source_format="EXCEL"
                )

                if "force" in header_mapping and header_mapping["force"] < len(cells):
                    rec.force = self.parse_float(cells[header_mapping["force"]])
                for i in range(7):
                    k = f"d{i}"
                    if k in header_mapping and header_mapping[k] < len(cells):
                        setattr(rec, k, self.parse_float(cells[header_mapping[k]]))

                if "air_temp" in header_mapping and header_mapping["air_temp"] < len(cells):
                    rec.air_temp = self.parse_float(cells[header_mapping["air_temp"]])
                if "asphalt_temp" in header_mapping and header_mapping["asphalt_temp"] < len(cells):
                    rec.asphalt_temp = self.parse_float(cells[header_mapping["asphalt_temp"]])
                if "lat" in header_mapping and header_mapping["lat"] < len(cells):
                    rec.lat = self.parse_float(cells[header_mapping["lat"]])
                if "long" in header_mapping and header_mapping["long"] < len(cells):
                    rec.long = self.parse_float(cells[header_mapping["long"]])
                if "time" in header_mapping and header_mapping["time"] < len(cells):
                    rec.time = cells[header_mapping["time"]]
                if "remarks" in header_mapping and header_mapping["remarks"] < len(cells):
                    rec.remarks = cells[header_mapping["remarks"]]

                if not any(getattr(rec, f"d{i}") for i in range(7)):
                    rec.extra_data = [c for idx, c in enumerate(cells) if idx != d_idx]

                records.append(rec)

        return records
