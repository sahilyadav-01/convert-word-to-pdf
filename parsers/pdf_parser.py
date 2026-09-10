"""PDF parser using pypdf for FWD Data Converter Pro."""

import os
import re
from typing import List
from pypdf import PdfReader
from core.data_model import FWDRecord
from parsers.base_parser import BaseParser


class PDFParser(BaseParser):
    """Parses PDF survey reports and tables."""

    def parse(self, file_path: str, side: str) -> List[FWDRecord]:
        records: List[FWDRecord] = []
        filename = os.path.basename(file_path)

        try:
            reader = PdfReader(file_path)
        except Exception:
            return records

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue

            lines = text.splitlines()
            header_mapping = {}

            for line in lines:
                clean = line.strip()
                if not clean:
                    continue

                # Tokenize line by multiple spaces or tabs
                tokens = [t.strip() for t in re.split(r"\s{2,}|\t", clean) if t.strip()]
                if not tokens:
                    tokens = clean.split()

                # Check if this line is a header
                if len(tokens) >= 3 and not header_mapping:
                    cand_map = self.match_header_columns(tokens)
                    if len(cand_map) >= 2:
                        header_mapping = cand_map
                        continue

                # Check if any token starts with 'D' followed by digits
                d_token = ""
                d_idx = -1
                for idx, t in enumerate(tokens):
                    if self.is_d_identifier(t):
                        d_token = t
                        d_idx = idx
                        break

                if not d_token:
                    continue

                chainage = self.parse_chainage_number(d_token)
                # Check if next token has chainage
                if chainage is None and d_idx + 1 < len(tokens):
                    chainage = self.parse_chainage_number(tokens[d_idx + 1])

                rec = FWDRecord(
                    side=side,
                    station_id=d_token,
                    station=chainage if chainage is not None else 0.0,
                    station_str=str(chainage if chainage is not None else "0"),
                    source_file=filename,
                    source_format="PDF"
                )

                # Attempt numeric deflection extraction from subsequent tokens
                numeric_tokens = []
                for idx, t in enumerate(tokens):
                    if idx != d_idx:
                        val = self.parse_float(t)
                        if val is not None:
                            numeric_tokens.append(val)

                if numeric_tokens:
                    # If first numeric is around 20-60, might be force (kN)
                    start_d = 0
                    if 10.0 <= numeric_tokens[0] <= 150.0 and len(numeric_tokens) > 1:
                        rec.force = numeric_tokens[0]
                        start_d = 1

                    for d_idx_num, num_val in enumerate(numeric_tokens[start_d:start_d + 7]):
                        setattr(rec, f"d{d_idx_num}", num_val)

                rec.extra_data = [t for idx, t in enumerate(tokens) if idx != d_idx]
                records.append(rec)

        return records
