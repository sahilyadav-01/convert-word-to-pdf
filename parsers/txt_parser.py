"""Text document parser (.txt) for FWD Data Converter Pro."""

import os
import re
from typing import List
from core.data_model import FWDRecord
from parsers.base_parser import BaseParser


class TXTParser(BaseParser):
    """Parses plain text and formatted report exports (.txt)."""

    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        records: List[FWDRecord] = []
        filename = os.path.basename(file_path)

        text = self.read_text_file(file_path)
        if not text:
            return records

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        header_mapping = {}

        for line in lines:
            # Tokenize by comma, tab, or multi-space
            tokens = [t.strip() for t in re.split(r",|\t|\s{2,}", line) if t.strip()]
            if not tokens:
                tokens = line.split()

            # Header detection
            if len(tokens) >= 3 and not header_mapping:
                cand_map = self.match_header_columns(tokens)
                if len(cand_map) >= 2:
                    header_mapping = cand_map
                    continue

            # Identify D identifier
            stn_id = ""
            d_idx = -1
            for idx, t in enumerate(tokens):
                if self.is_d_identifier(t):
                    stn_id = t
                    d_idx = idx
                    break

            if not stn_id:
                continue

            chainage = self.parse_chainage_number(stn_id)
            if chainage is None and d_idx + 1 < len(tokens):
                chainage = self.parse_chainage_number(tokens[d_idx + 1])

            rec = FWDRecord(
                side=side,
                station_id=stn_id,
                station=chainage if chainage is not None else 0.0,
                station_str=str(chainage if chainage is not None else "0"),
                source_file=filename,
                source_format="TXT"
            )

            numeric_tokens = []
            for idx, t in enumerate(tokens):
                if idx != d_idx:
                    val = self.parse_float(t)
                    if val is not None:
                        numeric_tokens.append(val)

            if numeric_tokens:
                start_d = 0
                if 10.0 <= numeric_tokens[0] <= 150.0 and len(numeric_tokens) > 1:
                    rec.force = numeric_tokens[0]
                    start_d = 1
                for d_i, num in enumerate(numeric_tokens[start_d:start_d + 7]):
                    setattr(rec, f"d{d_i}", num)

            rec.extra_data = [t for idx, t in enumerate(tokens) if idx != d_idx]
            records.append(rec)

        return records
