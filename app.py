"""Main entry point for FWD Data Converter Pro."""

import argparse
import os
import sys

from core.detector import Detector, InputFileInfo
from core.processor import PipelineProcessor


def run_cli(input_paths, output_path: str, prefix: str = "D"):
    """Command-line batch execution across multi-format files."""
    print("=" * 65)
    print("FWD DATA CONVERTER PRO (CLI Mode)")
    print("=" * 65)

    files = []
    for raw_p in input_paths:
        p = raw_p.strip('"\'')
        if os.path.isdir(p):
            for root, _, filenames in os.walk(p):
                for fn in sorted(filenames):
                    full = os.path.join(root, fn)
                    info = Detector.inspect_file(full)
                    if info and not any(f.path == info.path for f in files):
                        files.append(info)
        elif os.path.isfile(p):
            info = Detector.inspect_file(p)
            if info and not any(f.path == info.path for f in files):
                files.append(info)

    if not files:
        print("Error: No valid FWD survey files found (.docx, .doc, .pdf, .xlsx, .xls, .csv, .txt, .fwd).")
        sys.exit(1)

    print(f"Total files queued: {len(files)}")
    lhs_count = sum(1 for f in files if f.side == "LHS")
    rhs_count = sum(1 for f in files if f.side == "RHS")
    unk_count = sum(1 for f in files if f.side not in ("LHS", "RHS"))
    print(f"  • LHS files: {lhs_count}")
    print(f"  • RHS files: {rhs_count}")
    print(f"  • Unknown files: {unk_count}")

    processor = PipelineProcessor(prefix=prefix)

    def log_print(msg, level):
        print(f"  [{level}] {msg}")

    try:
        result = processor.process(
            files=files,
            output_path=output_path,
            progress_cb=lambda c, t, f: print(f"Processing ({c}/{t}): {f}"),
            log_cb=log_print
        )
        print("\n" + "=" * 65)
        print("CONVERSION SUCCESSFUL!")
        print(f"• Total records extracted: {result['records_count']}")
        print(f"• Output Excel: {result['output_path']}")
        print("=" * 65)
    except Exception as e:
        print(f"\nProcessing failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="FWD Data Converter Pro (Multi-Format -> Excel .xlsx)")
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode without GUI")
    parser.add_argument("-i", "--input", nargs="+", help="Input files or folders to process")
    parser.add_argument("-o", "--output", default="FWD_Consolidated_Output.xlsx", help="Output .xlsx file path")
    parser.add_argument("-p", "--prefix", default="D", help="Record prefix filter (default: 'D')")

    args, unknown = parser.parse_known_args()

    if args.cli or args.input:
        if not args.input:
            print("Error: --input argument required in CLI mode.")
            sys.exit(1)
        run_cli(args.input, args.output, args.prefix)
    else:
        from gui.main_window import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
