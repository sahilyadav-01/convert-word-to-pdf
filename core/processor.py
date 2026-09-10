"""Pipeline processor coordinating multi-format parsing, validation, sorting, and Excel output."""

import os
from typing import Any, Callable, Dict, List, Optional

from core.data_model import FWDRecord
from core.detector import InputFileInfo
from core.sorter import DirectionalSorter
from core.validator import Validator
from output.excel_writer import ExcelWriter
from parsers.csv_parser import CSVParser
from parsers.excel_parser import ExcelParser
from parsers.fwd_parser import FWDParser
from parsers.pdf_parser import PDFParser
from parsers.txt_parser import TXTParser
from parsers.word_parser import WordParser


class PipelineProcessor:
    """Coordinates format-specific parsers, common data models, sorting, and Excel export."""

    def __init__(self, prefix: str = "D"):
        self.prefix = prefix
        self.parsers = {
            "WORD": WordParser(prefix=prefix),
            "PDF": PDFParser(prefix=prefix),
            "CSV": CSVParser(prefix=prefix),
            "EXCEL": ExcelParser(prefix=prefix),
            "TXT": TXTParser(prefix=prefix),
            "FWD": FWDParser(prefix=prefix),
        }

    def process(
        self,
        files: List[InputFileInfo],
        output_path: str,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
        log_cb: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """Runs the complete batch extraction and conversion pipeline.

        Returns:
            Dict containing processing summary metrics and generated file path.
        """
        all_records: List[FWDRecord] = []
        all_logs: List[Dict[str, str]] = []
        format_counts: Dict[str, int] = {}
        lhs_files = 0
        rhs_files = 0
        unknown_files = 0

        total_files = len(files)
        if total_files == 0:
            raise ValueError("No files provided for conversion.")

        for idx, file_info in enumerate(files, start=1):
            if progress_cb:
                progress_cb(idx, total_files, file_info.filename)

            if log_cb:
                log_cb(f"[{idx}/{total_files}] Processing ({file_info.format}): {file_info.filename} [Side: {file_info.side}]", "INFO")

            # Track format stats
            format_counts[file_info.format] = format_counts.get(file_info.format, 0) + 1

            if file_info.side == "LHS":
                lhs_files += 1
            elif file_info.side == "RHS":
                rhs_files += 1
            else:
                unknown_files += 1
                all_logs.append({
                    "file": file_info.filename,
                    "level": "WARNING",
                    "message": "File side could not be automatically detected as LHS or RHS.",
                    "action": "Records placed in general section."
                })

            parser = self.parsers.get(file_info.format)
            if not parser:
                if log_cb:
                    log_cb(f"Unsupported format '{file_info.format}' for {file_info.filename}", "ERROR")
                all_logs.append({
                    "file": file_info.filename,
                    "level": "ERROR",
                    "message": f"Unsupported format: {file_info.format}",
                    "action": "Skipped file"
                })
                continue

            try:
                records = parser.parse(file_info.path, side=file_info.side)
                if not records:
                    if log_cb:
                        log_cb(f"No '{self.prefix}' records extracted from {file_info.filename}", "WARN")
                    all_logs.append({
                        "file": file_info.filename,
                        "level": "WARNING",
                        "message": f"No valid '{self.prefix}' records found.",
                        "action": "0 records added"
                    })
                else:
                    if log_cb:
                        log_cb(f"Extracted {len(records)} '{self.prefix}' record(s) from {file_info.filename}", "INFO")
                    all_records.extend(records)
            except Exception as e:
                if log_cb:
                    log_cb(f"Error parsing {file_info.filename}: {str(e)}", "ERROR")
                all_logs.append({
                    "file": file_info.filename,
                    "level": "ERROR",
                    "message": str(e),
                    "action": "Skipped file"
                })

        if not all_records:
            raise ValueError(f"No records beginning with '{self.prefix}' were found in any of the selected files.")

        # Data Validation
        valid_records, val_logs = Validator.validate(all_records)
        all_logs.extend(val_logs)

        # Directional Sorting: LHS (increasing) -> RHS (decreasing)
        if log_cb:
            log_cb("Sorting records: LHS (increasing chainage) -> RHS (decreasing chainage)...", "INFO")

        sorted_records = DirectionalSorter.sort(valid_records)
        lhs_sorted, rhs_sorted, unk_sorted = DirectionalSorter.split_and_sort(valid_records)

        summary_stats = {
            "total_files": total_files,
            "lhs_files": lhs_files,
            "rhs_files": rhs_files,
            "unknown_files": unknown_files,
            "total_records": len(sorted_records),
            "lhs_records": len(lhs_sorted),
            "rhs_records": len(rhs_sorted),
            "unknown_records": len(unk_sorted),
            "format_counts": format_counts,
            "prefix": self.prefix,
            "output_path": output_path
        }

        # Write Excel Workbook
        if log_cb:
            log_cb(f"Writing consolidated Excel workbook: {output_path}...", "INFO")

        out_file = ExcelWriter.write_workbook(
            output_path=output_path,
            records=sorted_records,
            summary_stats=summary_stats,
            error_logs=all_logs
        )

        return {
            "output_path": out_file,
            "summary": summary_stats,
            "records_count": len(sorted_records)
        }
