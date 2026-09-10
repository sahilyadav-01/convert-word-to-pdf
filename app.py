"""Main entry point for Word to Excel Batch Converter."""

import argparse
import os
import sys

from src.excel_writer import ExcelWriter
from src.extractor import ExtractedRecord, Extractor
from src.file_manager import FileManager
from src.sorter import Sorter
from src.word_reader import WordReader


def run_cli(input_paths, output_path: str, prefix: str = "D"):
    """Command-line execution mode for automated headless processing."""
    print("=" * 60)
    print("WORD TO EXCEL BATCH CONVERTER (CLI Mode)")
    print("=" * 60)

    fm = FileManager()
    for raw_p in input_paths:
        p = raw_p.strip('"\'')
        if os.path.isdir(p):
            fm.add_folder(p)
        elif os.path.isfile(p):
            fm.add_file(p)

    print(f"Total files queued: {fm.total_count}")
    print(f"LHS files: {len(fm.lhs_files)}")
    print(f"RHS files: {len(fm.rhs_files)}")
    print(f"Unknown files: {len(fm.unknown_files)}")

    if fm.total_count == 0:
        print("Error: No valid .docx / .doc files found.")
        sys.exit(1)

    extractor = Extractor(prefix=prefix)
    all_records = []
    error_logs = []

    for idx, f in enumerate(fm.files, 1):
        print(f"[{idx}/{fm.total_count}] Reading {f.filename} (Side: {f.side})...")
        doc_data = WordReader.read(f.path)
        if not doc_data.success:
            print(f"  Warning: {doc_data.error_message}")
            error_logs.append({
                "file": f.filename,
                "level": "ERROR",
                "message": doc_data.error_message or "Read error",
                "action": "Skipped file"
            })
            continue

        records = extractor.extract(doc_data, side=f.side)
        print(f"  Extracted {len(records)} '{prefix}' records.")
        all_records.extend(records)

    if not all_records:
        print(f"Error: No records beginning with '{prefix}' found.")
        sys.exit(1)

    print(f"Sorting {len(all_records)} total records: LHS (increasing) -> RHS (decreasing)...")
    sorted_records = Sorter.sort_records(all_records)
    lhs_sorted, rhs_sorted, unk_sorted = Sorter.split_and_sort(all_records)

    summary_stats = {
        "total_files": fm.total_count,
        "lhs_files": len(fm.lhs_files),
        "rhs_files": len(fm.rhs_files),
        "unknown_files": len(fm.unknown_files),
        "total_records": len(sorted_records),
        "lhs_records": len(lhs_sorted),
        "rhs_records": len(rhs_sorted),
        "prefix": prefix,
        "output_path": output_path
    }

    print(f"Generating Excel workbook: {output_path}...")
    out_file = ExcelWriter.write_workbook(
        output_path=output_path,
        records=sorted_records,
        summary_stats=summary_stats,
        error_logs=error_logs
    )
    print(f"Success! Final Excel workbook created at: {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Word to Excel Batch Converter (.docx/.doc -> .xlsx)")
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode without GUI")
    parser.add_argument("-i", "--input", nargs="+", help="Input files or folders to process")
    parser.add_argument("-o", "--output", default="FWD_Output.xlsx", help="Output .xlsx file path")
    parser.add_argument("-p", "--prefix", default="D", help="Record prefix filter (default: 'D')")

    args, unknown = parser.parse_known_args()

    if args.cli or args.input:
        if not args.input:
            print("Error: --input argument required in CLI mode.")
            sys.exit(1)
        run_cli(args.input, args.output, args.prefix)
    else:
        # Launch modern GUI
        from src.gui import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
