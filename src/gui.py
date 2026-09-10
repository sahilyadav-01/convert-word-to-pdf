"""Modern PyQt6 Desktop GUI for Word to Excel Batch Converter."""

import os
import sys
from typing import List, Optional

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.excel_writer import ExcelWriter
from src.extractor import ExtractedRecord, Extractor
from src.file_manager import FileManager, WordFileInfo
from src.sorter import Sorter
from src.word_reader import WordReader


class WorkerSignals(QObject):
    """Signals for batch conversion background worker thread."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    log = pyqtSignal(str, str)            # message, level ('INFO', 'WARN', 'ERROR')
    finished = pyqtSignal(str, int, int)  # output_path, total_files, total_records
    error = pyqtSignal(str)


class ConversionWorker(QThread):
    """Background worker that performs batch Word reading, extraction, sorting, and Excel writing."""

    def __init__(self, files: List[WordFileInfo], output_path: str, prefix: str = "D"):
        super().__init__()
        self.files = files
        self.output_path = output_path
        self.prefix = prefix
        self.signals = WorkerSignals()

    def run(self):
        try:
            total_files = len(self.files)
            if total_files == 0:
                self.signals.error.emit("No files selected for conversion.")
                return

            extractor = Extractor(prefix=self.prefix)
            all_records: List[ExtractedRecord] = []
            error_logs = []
            lhs_count = 0
            rhs_count = 0
            unknown_count = 0

            self.signals.log.emit(f"Starting batch conversion of {total_files} file(s)...", "INFO")

            for idx, file_info in enumerate(self.files, start=1):
                self.signals.progress.emit(idx, total_files, file_info.filename)
                self.signals.log.emit(f"[{idx}/{total_files}] Processing: {file_info.filename} (Side: {file_info.side})", "INFO")

                if file_info.side == "LHS":
                    lhs_count += 1
                elif file_info.side == "RHS":
                    rhs_count += 1
                else:
                    unknown_count += 1
                    error_logs.append({
                        "file": file_info.filename,
                        "level": "WARNING",
                        "message": "File side could not be automatically detected as LHS or RHS.",
                        "action": "Records placed in general section."
                    })

                # Read Word document
                doc_data = WordReader.read(file_info.path)
                if not doc_data.success:
                    self.signals.log.emit(f"Failed to read {file_info.filename}: {doc_data.error_message}", "ERROR")
                    error_logs.append({
                        "file": file_info.filename,
                        "level": "ERROR",
                        "message": doc_data.error_message or "Read error",
                        "action": "Skipped file"
                    })
                    continue

                # Extract D records
                records = extractor.extract(doc_data, side=file_info.side)
                if not records:
                    self.signals.log.emit(f"No records beginning with '{self.prefix}' found in {file_info.filename}.", "WARN")
                    error_logs.append({
                        "file": file_info.filename,
                        "level": "WARNING",
                        "message": f"No records beginning with '{self.prefix}' found in document.",
                        "action": "0 records added"
                    })
                else:
                    self.signals.log.emit(f"Extracted {len(records)} '{self.prefix}' record(s) from {file_info.filename}", "INFO")
                    all_records.extend(records)

            if not all_records:
                self.signals.error.emit(f"No records beginning with '{self.prefix}' were found in any of the selected files.")
                return

            # Apply directional sorting
            self.signals.log.emit("Sorting records: LHS (increasing) -> RHS (decreasing)...", "INFO")
            sorted_records = Sorter.sort_records(all_records)
            lhs_sorted, rhs_sorted, unk_sorted = Sorter.split_and_sort(all_records)

            self.signals.log.emit(
                f"Sorting completed: {len(lhs_sorted)} LHS record(s), {len(rhs_sorted)} RHS record(s), {len(unk_sorted)} Other record(s).",
                "INFO"
            )

            # Build Excel workbook
            self.signals.log.emit(f"Generating consolidated Excel file: {self.output_path}...", "INFO")
            summary_stats = {
                "total_files": total_files,
                "lhs_files": lhs_count,
                "rhs_files": rhs_count,
                "unknown_files": unknown_count,
                "total_records": len(sorted_records),
                "lhs_records": len(lhs_sorted),
                "rhs_records": len(rhs_sorted),
                "prefix": self.prefix,
                "output_path": self.output_path
            }

            out_file = ExcelWriter.write_workbook(
                output_path=self.output_path,
                records=sorted_records,
                summary_stats=summary_stats,
                error_logs=error_logs
            )

            self.signals.log.emit(f"Successfully created Excel file: {out_file}", "INFO")
            self.signals.finished.emit(out_file, total_files, len(sorted_records))

        except Exception as e:
            self.signals.error.emit(f"An unexpected error occurred during processing:\n{str(e)}")


class MainWindow(QWidget):
    """Main application window for Word to Excel Batch Converter."""

    def __init__(self):
        super().__init__()
        self.file_manager = FileManager()
        self.worker: Optional[ConversionWorker] = None
        self.last_generated_file: Optional[str] = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("WORD → XLSX BATCH CONVERTER (FWD Automation)")
        self.resize(950, 720)
        self.setMinimumSize(850, 600)
        self.apply_stylesheet()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title Banner
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        title_lbl = QLabel("WORD → XLSX BATCH CONVERTER")
        title_lbl.setObjectName("titleLabel")
        subtitle_lbl = QLabel("Automated LHS/RHS detection • Directional sorting (LHS ↑ / RHS ↓) • Multi-sheet formatted Excel generation")
        subtitle_lbl.setObjectName("subtitleLabel")
        
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        main_layout.addWidget(header_frame)

        # File Queue Management Card
        queue_frame = QFrame()
        queue_frame.setObjectName("cardFrame")
        queue_layout = QVBoxLayout(queue_frame)
        queue_layout.setContentsMargins(15, 15, 15, 15)
        queue_layout.setSpacing(10)

        # Top Button Bar
        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("+ Add Word Files (.docx / .doc)")
        self.btn_add_files.setObjectName("btnPrimary")
        self.btn_add_files.clicked.connect(self.on_add_files)

        self.btn_add_folder = QPushButton("Select Folder")
        self.btn_add_folder.setObjectName("btnSecondary")
        self.btn_add_folder.clicked.connect(self.on_add_folder)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.setObjectName("btnSecondary")
        self.btn_remove.clicked.connect(self.on_remove_selected)

        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_clear.clicked.connect(self.on_clear_list)

        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        queue_layout.addLayout(btn_layout)

        # File List Table
        self.file_table = QTableWidget(0, 4)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Detected Side", "File Size", "Path"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(1, 120)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(2, 100)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(True)
        queue_layout.addWidget(self.file_table)

        # Summary Counters Badge Bar
        badge_layout = QHBoxLayout()
        self.lbl_total_files = QLabel("Total Files: 0")
        self.lbl_total_files.setObjectName("statBadgeTotal")

        self.lbl_lhs_files = QLabel("LHS Files: 0")
        self.lbl_lhs_files.setObjectName("statBadgeLHS")

        self.lbl_rhs_files = QLabel("RHS Files: 0")
        self.lbl_rhs_files.setObjectName("statBadgeRHS")

        self.lbl_unk_files = QLabel("Unknown Side: 0")
        self.lbl_unk_files.setObjectName("statBadgeUNK")

        badge_layout.addWidget(self.lbl_total_files)
        badge_layout.addWidget(self.lbl_lhs_files)
        badge_layout.addWidget(self.lbl_rhs_files)
        badge_layout.addWidget(self.lbl_unk_files)
        badge_layout.addStretch()
        queue_layout.addLayout(badge_layout)

        main_layout.addWidget(queue_frame)

        # Rules and Settings Card
        settings_frame = QFrame()
        settings_frame.setObjectName("cardFrame")
        settings_layout = QHBoxLayout(settings_frame)
        settings_layout.setContentsMargins(15, 12, 15, 12)
        settings_layout.setSpacing(20)

        # Extraction Rule
        rule_vbox = QVBoxLayout()
        rule_lbl = QLabel("<b>Extraction Rule:</b>")
        rule_sub = QHBoxLayout()
        prefix_lbl = QLabel("Record Prefix:")
        self.txt_prefix = QLineEdit("D")
        self.txt_prefix.setMaximumWidth(60)
        rule_desc = QLabel("(Extracts only rows/items beginning with 'D')")
        rule_sub.addWidget(prefix_lbl)
        rule_sub.addWidget(self.txt_prefix)
        rule_sub.addWidget(rule_desc)
        rule_sub.addStretch()
        rule_vbox.addWidget(rule_lbl)
        rule_vbox.addLayout(rule_sub)
        settings_layout.addLayout(rule_vbox, 1)

        # Ordering Rule Preview
        order_vbox = QVBoxLayout()
        order_lbl = QLabel("<b>Chainage Ordering Rules:</b>")
        order_details = QLabel("• <b>LHS:</b> Increasing chainage (Ascending)<br>• <b>RHS:</b> Decreasing chainage (Descending)")
        order_vbox.addWidget(order_lbl)
        order_vbox.addWidget(order_details)
        settings_layout.addLayout(order_vbox, 1)

        main_layout.addWidget(settings_frame)

        # Output Selection Card
        out_frame = QFrame()
        out_frame.setObjectName("cardFrame")
        out_layout = QHBoxLayout(out_frame)
        out_layout.setContentsMargins(15, 12, 15, 12)
        out_layout.setSpacing(10)

        out_lbl = QLabel("<b>Output Excel File (.xlsx):</b>")
        default_out = os.path.join(os.getcwd(), "FWD_Output.xlsx")
        self.txt_output = QLineEdit(default_out)
        self.btn_browse_out = QPushButton("Browse...")
        self.btn_browse_out.setObjectName("btnSecondary")
        self.btn_browse_out.clicked.connect(self.on_browse_output)

        out_layout.addWidget(out_lbl)
        out_layout.addWidget(self.txt_output)
        out_layout.addWidget(self.btn_browse_out)
        main_layout.addWidget(out_frame)

        # Progress & Primary Convert Button
        exec_layout = QHBoxLayout()
        self.btn_convert = QPushButton("⚡ CONVERT TO XLSX")
        self.btn_convert.setObjectName("btnConvert")
        self.btn_convert.setMinimumHeight(44)
        self.btn_convert.clicked.connect(self.on_convert)

        self.btn_open_file = QPushButton("Open Excel")
        self.btn_open_file.setObjectName("btnAction")
        self.btn_open_file.setMinimumHeight(44)
        self.btn_open_file.setEnabled(False)
        self.btn_open_file.clicked.connect(self.on_open_excel)

        self.btn_open_folder = QPushButton("Open Folder")
        self.btn_open_folder.setObjectName("btnAction")
        self.btn_open_folder.setMinimumHeight(44)
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.on_open_folder)

        exec_layout.addWidget(self.btn_convert, 3)
        exec_layout.addWidget(self.btn_open_file, 1)
        exec_layout.addWidget(self.btn_open_folder, 1)
        main_layout.addLayout(exec_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        main_layout.addWidget(self.progress_bar)

        # Real-time Log Console
        self.log_console = QTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(130)
        self.log_console.setPlaceholderText("Execution log messages will appear here...")
        main_layout.addWidget(self.log_console)

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                color: #212529;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            #headerFrame {
                background-color: #1F4E79;
                border-radius: 8px;
            }
            #titleLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            #subtitleLabel {
                color: #D1E1F0;
                font-size: 12px;
            }
            #cardFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            #btnPrimary {
                background-color: #1F4E79;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            #btnPrimary:hover {
                background-color: #28639B;
            }
            #btnSecondary {
                background-color: #ECEFF1;
                color: #37474F;
                border: 1px solid #CFD8DC;
                border-radius: 5px;
                padding: 8px 14px;
            }
            #btnSecondary:hover {
                background-color: #DFE5E8;
            }
            #btnConvert {
                background-color: #2E7D32;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            #btnConvert:hover {
                background-color: #388E3C;
            }
            #btnConvert:disabled {
                background-color: #A5D6A7;
            }
            #btnAction {
                background-color: #455A64;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            #btnAction:hover {
                background-color: #546E7A;
            }
            #btnAction:disabled {
                background-color: #B0BEC5;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                gridline-color: #F0F0F0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #ECEFF1;
                color: #37474F;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #CFD8DC;
            }
            #statBadgeTotal {
                background-color: #ECEFF1;
                color: #37474F;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            #statBadgeLHS {
                background-color: #E3F2FD;
                color: #1565C0;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            #statBadgeRHS {
                background-color: #E8F5E9;
                color: #2E7D32;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            #statBadgeUNK {
                background-color: #FFF3E0;
                color: #E65100;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QLineEdit:focus {
                border: 1px solid #1F4E79;
            }
            QProgressBar {
                border: 1px solid #CFD8DC;
                border-radius: 4px;
                text-align: center;
                background-color: #FFFFFF;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #1F4E79;
                border-radius: 3px;
            }
            #logConsole {
                background-color: #263238;
                color: #ECEFF1;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border-radius: 4px;
                padding: 6px;
            }
        """)

    def on_add_files(self):
        """Open multi-file selection dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Word Documents",
            "",
            "Word Documents (*.docx *.doc);;All Files (*.*)"
        )
        if files:
            added = self.file_manager.add_files(files)
            self.refresh_table()
            self.append_log(f"Added {added} file(s) to queue.", "INFO")

    def on_add_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Word Files")
        if folder:
            added = self.file_manager.add_folder(folder, recursive=False)
            self.refresh_table()
            self.append_log(f"Scanned folder '{folder}': added {added} Word file(s).", "INFO")

    def on_remove_selected(self):
        """Remove currently selected rows."""
        selected_rows = sorted(set(index.row() for index in self.file_table.selectedIndexes()), reverse=True)
        for row in selected_rows:
            self.file_manager.remove_file(row)
        self.refresh_table()

    def on_clear_list(self):
        """Clear all queued files."""
        self.file_manager.clear()
        self.refresh_table()
        self.append_log("File queue cleared.", "INFO")

    def on_browse_output(self):
        """Select destination Excel file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Consolidated Excel File",
            self.txt_output.text(),
            "Excel Workbook (*.xlsx)"
        )
        if file_path:
            if not file_path.lower().endswith(".xlsx"):
                file_path += ".xlsx"
            self.txt_output.setText(file_path)

    def refresh_table(self):
        """Updates the table view and statistics badges."""
        self.file_table.setRowCount(0)
        for row_idx, file_info in enumerate(self.file_manager.files):
            self.file_table.insertRow(row_idx)

            # Filename
            item_fn = QTableWidgetItem(file_info.filename)
            self.file_table.setItem(row_idx, 0, item_fn)

            # Detected Side Badge
            item_side = QTableWidgetItem(file_info.side)
            item_side.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if file_info.side == "LHS":
                item_side.setForeground(QColor("#1565C0"))
                item_side.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif file_info.side == "RHS":
                item_side.setForeground(QColor("#2E7D32"))
                item_side.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            else:
                item_side.setForeground(QColor("#E65100"))
                item_side.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.file_table.setItem(row_idx, 1, item_side)

            # File size in KB
            kb_size = f"{file_info.size_bytes / 1024:.1f} KB"
            item_size = QTableWidgetItem(kb_size)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.file_table.setItem(row_idx, 2, item_size)

            # Path
            item_path = QTableWidgetItem(file_info.path)
            self.file_table.setItem(row_idx, 3, item_path)

        # Update counter badges
        self.lbl_total_files.setText(f"Total Files: {self.file_manager.total_count}")
        self.lbl_lhs_files.setText(f"LHS Files: {len(self.file_manager.lhs_files)}")
        self.lbl_rhs_files.setText(f"RHS Files: {len(self.file_manager.rhs_files)}")
        self.lbl_unk_files.setText(f"Unknown Side: {len(self.file_manager.unknown_files)}")

    def append_log(self, message: str, level: str = "INFO"):
        """Append a message to the real-time log window."""
        color = "#ECEFF1"
        if level == "WARN":
            color = "#FFB74D"
        elif level == "ERROR":
            color = "#EF5350"
        elif level == "SUCCESS":
            color = "#81C784"

        html = f"<span style='color: {color};'>[{level}] {message}</span>"
        self.log_console.append(html)

    def on_convert(self):
        """Trigger the batch conversion process."""
        if self.file_manager.total_count == 0:
            QMessageBox.warning(self, "No Files", "Please add at least one Word file (.docx / .doc) to proceed.")
            return

        out_path = self.txt_output.text().strip()
        if not out_path:
            QMessageBox.warning(self, "Missing Output Path", "Please specify a destination path for the Excel output.")
            return

        prefix = self.txt_prefix.text().strip()
        if not prefix:
            prefix = "D"

        # Check for unknown side files and alert user
        unknowns = self.file_manager.unknown_files
        if unknowns:
            msg = (
                f"{len(unknowns)} file(s) could not be automatically identified as 'LHS' or 'RHS' from their filenames.\n"
                f"They will be processed, but placed at the end without directional sorting.\n\n"
                f"Do you wish to proceed?"
            )
            reply = QMessageBox.question(
                self,
                "Unknown Side Files Detected",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Prepare UI for processing
        self.btn_convert.setEnabled(False)
        self.btn_add_files.setEnabled(False)
        self.btn_add_folder.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Starting...")

        # Launch Worker Thread
        self.worker = ConversionWorker(
            files=list(self.file_manager.files),
            output_path=out_path,
            prefix=prefix
        )
        self.worker.signals.progress.connect(self.on_worker_progress)
        self.worker.signals.log.connect(self.append_log)
        self.worker.signals.finished.connect(self.on_worker_finished)
        self.worker.signals.error.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, current: int, total: int, filename: str):
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"Processing {current}/{total} ({pct}%) - {filename}")

    def on_worker_finished(self, out_file: str, total_files: int, total_records: int):
        self.last_generated_file = out_file
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Conversion Completed Successfully!")
        self.btn_convert.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_open_file.setEnabled(True)
        self.btn_open_folder.setEnabled(True)

        self.append_log(f"All done! Extracted {total_records} records from {total_files} files.", "SUCCESS")

        QMessageBox.information(
            self,
            "Conversion Complete",
            f"Batch conversion completed successfully!\n\n"
            f"• Files processed: {total_files}\n"
            f"• Total D records extracted: {total_records}\n"
            f"• Saved to: {out_file}\n\n"
            f"Ordering applied: LHS (Ascending) -> RHS (Descending)"
        )

    def on_worker_error(self, err_msg: str):
        self.progress_bar.setFormat("Error occurred during conversion")
        self.btn_convert.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_remove.setEnabled(True)

        self.append_log(err_msg, "ERROR")
        QMessageBox.critical(self, "Conversion Error", err_msg)

    def on_open_excel(self):
        """Open the generated Excel file in default handler."""
        if self.last_generated_file and os.path.exists(self.last_generated_file):
            try:
                os.startfile(self.last_generated_file)
            except Exception as e:
                QMessageBox.warning(self, "Open Error", f"Could not open file: {e}")

    def on_open_folder(self):
        """Open the output folder in Windows Explorer."""
        if self.last_generated_file:
            folder = os.path.dirname(os.path.abspath(self.last_generated_file))
            if os.path.exists(folder):
                try:
                    os.startfile(folder)
                except Exception as e:
                    QMessageBox.warning(self, "Open Error", f"Could not open folder: {e}")


def launch_gui():
    """Launch the PyQt6 GUI application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
