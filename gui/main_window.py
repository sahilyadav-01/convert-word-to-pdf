"""Modern PyQt6 desktop GUI for FWD Data Converter Pro."""

import os
import sys
from typing import List, Optional

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
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

from core.detector import Detector, InputFileInfo
from core.processor import PipelineProcessor


class WorkerSignals(QObject):
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(str, int, int)
    error = pyqtSignal(str)


class ConversionWorker(QThread):
    def __init__(self, files: List[InputFileInfo], output_path: str, prefix: str = "D"):
        super().__init__()
        self.files = files
        self.output_path = output_path
        self.prefix = prefix
        self.signals = WorkerSignals()

    def run(self):
        try:
            processor = PipelineProcessor(prefix=self.prefix)
            result = processor.process(
                files=self.files,
                output_path=self.output_path,
                progress_cb=lambda c, t, f: self.signals.progress.emit(c, t, f),
                log_cb=lambda m, l: self.signals.log.emit(m, l)
            )
            self.signals.finished.emit(
                result["output_path"],
                len(self.files),
                result["records_count"]
            )
        except Exception as e:
            self.signals.error.emit(str(e))


class MainWindow(QWidget):
    """Main window for FWD Data Converter Pro."""

    FORMAT_COLORS = {
        "WORD": "#2979FF",
        "PDF": "#D50000",
        "CSV": "#00C853",
        "EXCEL": "#1B5E20",
        "TXT": "#795548",
        "FWD": "#FF6D00",
        "UNKNOWN": "#757575"
    }

    def __init__(self):
        super().__init__()
        self.files: List[InputFileInfo] = []
        self.worker: Optional[ConversionWorker] = None
        self.last_output_file: Optional[str] = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("FWD Data Converter Pro")
        self.resize(1020, 750)
        self.setMinimumSize(900, 620)
        self.apply_stylesheet()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Header Frame
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("FWD DATA CONVERTER PRO")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Multi-Format Ingestion (Word • PDF • CSV • Excel • Text • FWD) • Automated Directional Sorting • Unified XLSX Export")
        subtitle.setObjectName("subtitleLabel")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_frame)

        # File List Management Frame
        queue_frame = QFrame()
        queue_frame.setObjectName("cardFrame")
        queue_layout = QVBoxLayout(queue_frame)
        queue_layout.setContentsMargins(14, 14, 14, 14)
        queue_layout.setSpacing(10)

        btn_bar = QHBoxLayout()
        self.btn_add_files = QPushButton("+ Add Files (Multi-Format)")
        self.btn_add_files.setObjectName("btnPrimary")
        self.btn_add_files.clicked.connect(self.on_add_files)

        self.btn_add_folder = QPushButton("Select Folder")
        self.btn_add_folder.setObjectName("btnSecondary")
        self.btn_add_folder.clicked.connect(self.on_add_folder)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.setObjectName("btnSecondary")
        self.btn_remove.clicked.connect(self.on_remove_selected)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_clear.clicked.connect(self.on_clear)

        btn_bar.addWidget(self.btn_add_files)
        btn_bar.addWidget(self.btn_add_folder)
        btn_bar.addWidget(self.btn_remove)
        btn_bar.addWidget(self.btn_clear)
        btn_bar.addStretch()
        queue_layout.addLayout(btn_bar)

        # Table Widget
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Filename", "Format", "Detected Side", "Size", "File Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 90)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 110)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 90)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        queue_layout.addWidget(self.table)

        # Statistics Bar
        stat_bar = QHBoxLayout()
        self.lbl_total = QLabel("Total: 0")
        self.lbl_total.setObjectName("badgeDefault")
        self.lbl_lhs = QLabel("LHS: 0")
        self.lbl_lhs.setObjectName("badgeLHS")
        self.lbl_rhs = QLabel("RHS: 0")
        self.lbl_rhs.setObjectName("badgeRHS")
        self.lbl_formats = QLabel("Formats: None")
        self.lbl_formats.setObjectName("badgeDefault")

        stat_bar.addWidget(self.lbl_total)
        stat_bar.addWidget(self.lbl_lhs)
        stat_bar.addWidget(self.lbl_rhs)
        stat_bar.addWidget(self.lbl_formats)
        stat_bar.addStretch()
        queue_layout.addLayout(stat_bar)

        main_layout.addWidget(queue_frame)

        # Rule & Settings
        settings_frame = QFrame()
        settings_frame.setObjectName("cardFrame")
        settings_layout = QHBoxLayout(settings_frame)
        settings_layout.setContentsMargins(14, 10, 14, 10)
        settings_layout.setSpacing(16)

        rule_box = QHBoxLayout()
        rule_box.addWidget(QLabel("<b>Extraction Filter:</b> Target Prefix:"))
        self.txt_prefix = QLineEdit("D")
        self.txt_prefix.setMaximumWidth(50)
        rule_box.addWidget(self.txt_prefix)
        rule_box.addWidget(QLabel("(matches records beginning with 'D', e.g. D100, D105)"))
        settings_layout.addLayout(rule_box, 1)

        sort_info = QLabel("<b>Directional Order:</b> • LHS: Increasing Chainage (↑)  • RHS: Decreasing Chainage (↓)")
        settings_layout.addWidget(sort_info, 1)
        main_layout.addWidget(settings_frame)

        # Output Selection Frame
        out_frame = QFrame()
        out_frame.setObjectName("cardFrame")
        out_layout = QHBoxLayout(out_frame)
        out_layout.setContentsMargins(14, 10, 14, 10)
        out_layout.setSpacing(10)

        out_layout.addWidget(QLabel("<b>Output Excel File (.xlsx):</b>"))
        default_out = os.path.join(os.getcwd(), "FWD_Consolidated_Output.xlsx")
        self.txt_output = QLineEdit(default_out)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setObjectName("btnSecondary")
        self.btn_browse.clicked.connect(self.on_browse_output)

        out_layout.addWidget(self.txt_output)
        out_layout.addWidget(self.btn_browse)
        main_layout.addWidget(out_frame)

        # Execution Bar
        exec_bar = QHBoxLayout()
        self.btn_convert = QPushButton("⚡ CONVERT TO CONSOLIDATED XLSX")
        self.btn_convert.setObjectName("btnConvert")
        self.btn_convert.setMinimumHeight(44)
        self.btn_convert.clicked.connect(self.on_convert)

        self.btn_open_excel = QPushButton("Open Excel")
        self.btn_open_excel.setObjectName("btnAction")
        self.btn_open_excel.setMinimumHeight(44)
        self.btn_open_excel.setEnabled(False)
        self.btn_open_excel.clicked.connect(self.on_open_excel)

        self.btn_open_folder = QPushButton("Open Folder")
        self.btn_open_folder.setObjectName("btnAction")
        self.btn_open_folder.setMinimumHeight(44)
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.on_open_folder)

        exec_bar.addWidget(self.btn_convert, 3)
        exec_bar.addWidget(self.btn_open_excel, 1)
        exec_bar.addWidget(self.btn_open_folder, 1)
        main_layout.addLayout(exec_bar)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")
        main_layout.addWidget(self.progress_bar)

        # Console Log
        self.log_console = QTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(120)
        self.log_console.setPlaceholderText("Execution log messages...")
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
            #badgeDefault {
                background-color: #ECEFF1;
                color: #37474F;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 4px;
            }
            #badgeLHS {
                background-color: #E3F2FD;
                color: #1565C0;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 4px;
            }
            #badgeRHS {
                background-color: #E8F5E9;
                color: #2E7D32;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 4px;
                padding: 6px 10px;
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
        file_filter = (
            "All Supported FWD Files (*.docx *.doc *.pdf *.xlsx *.xls *.csv *.txt *.fwd);;"
            "Word Files (*.docx *.doc);;"
            "PDF Files (*.pdf);;"
            "Excel Files (*.xlsx *.xls);;"
            "CSV Files (*.csv);;"
            "Text / FWD Files (*.txt *.fwd);;"
            "All Files (*.*)"
        )
        paths, _ = QFileDialog.getOpenFileNames(self, "Select FWD Data Files", "", file_filter)
        if paths:
            added = 0
            for p in paths:
                info = Detector.inspect_file(p)
                if info and not any(f.path == info.path for f in self.files):
                    self.files.append(info)
                    added += 1
            self.refresh_table()
            self.append_log(f"Added {added} file(s) to queue.", "INFO")

    def on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Survey Files")
        if folder:
            added = 0
            for root, _, filenames in os.walk(folder):
                for fn in sorted(filenames):
                    full = os.path.join(root, fn)
                    info = Detector.inspect_file(full)
                    if info and not any(f.path == info.path for f in self.files):
                        self.files.append(info)
                        added += 1
            self.refresh_table()
            self.append_log(f"Scanned folder '{folder}': added {added} file(s).", "INFO")

    def on_remove_selected(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        for row in selected_rows:
            if 0 <= row < len(self.files):
                self.files.pop(row)
        self.refresh_table()

    def on_clear(self):
        self.files.clear()
        self.refresh_table()
        self.append_log("Queue cleared.", "INFO")

    def on_browse_output(self):
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Save Consolidated Excel File",
            self.txt_output.text(),
            "Excel Workbook (*.xlsx)"
        )
        if dest:
            if not dest.lower().endswith(".xlsx"):
                dest += ".xlsx"
            self.txt_output.setText(dest)

    def refresh_table(self):
        self.table.setRowCount(0)
        lhs_cnt = 0
        rhs_cnt = 0
        fmt_counts = {}

        for row_idx, f in enumerate(self.files):
            self.table.insertRow(row_idx)

            # Filename
            self.table.setItem(row_idx, 0, QTableWidgetItem(f.filename))

            # Format Badge
            item_fmt = QTableWidgetItem(f.format)
            item_fmt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_fmt.setForeground(QColor(self.FORMAT_COLORS.get(f.format, "#757575")))
            item_fmt.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row_idx, 1, item_fmt)

            # Side Badge
            item_side = QTableWidgetItem(f.side)
            item_side.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if f.side == "LHS":
                item_side.setForeground(QColor("#1565C0"))
                item_side.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                lhs_cnt += 1
            elif f.side == "RHS":
                item_side.setForeground(QColor("#2E7D32"))
                item_side.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                rhs_cnt += 1
            else:
                item_side.setForeground(QColor("#E65100"))
                item_side.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row_idx, 2, item_side)

            # Size
            size_kb = f"{f.size_bytes / 1024:.1f} KB"
            item_size = QTableWidgetItem(size_kb)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 3, item_size)

            # Path
            self.table.setItem(row_idx, 4, QTableWidgetItem(f.path))

            fmt_counts[f.format] = fmt_counts.get(f.format, 0) + 1

        self.lbl_total.setText(f"Total: {len(self.files)}")
        self.lbl_lhs.setText(f"LHS: {lhs_cnt}")
        self.lbl_rhs.setText(f"RHS: {rhs_cnt}")

        if fmt_counts:
            fmt_str = " • ".join(f"{k}: {v}" for k, v in sorted(fmt_counts.items()))
            self.lbl_formats.setText(f"Formats: {fmt_str}")
        else:
            self.lbl_formats.setText("Formats: None")

    def append_log(self, msg: str, level: str = "INFO"):
        color = "#ECEFF1"
        if level == "WARN":
            color = "#FFB74D"
        elif level == "ERROR":
            color = "#EF5350"
        elif level == "SUCCESS":
            color = "#81C784"
        self.log_console.append(f"<span style='color: {color};'>[{level}] {msg}</span>")

    def on_convert(self):
        if not self.files:
            QMessageBox.warning(self, "No Files", "Please add at least one input file to proceed.")
            return

        out_path = self.txt_output.text().strip()
        if not out_path:
            QMessageBox.warning(self, "Missing Output", "Please specify an output Excel path.")
            return

        prefix = self.txt_prefix.text().strip() or "D"

        self.btn_convert.setEnabled(False)
        self.btn_add_files.setEnabled(False)
        self.btn_add_folder.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Starting batch processing...")

        self.worker = ConversionWorker(files=list(self.files), output_path=out_path, prefix=prefix)
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
        self.last_output_file = out_file
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Conversion Completed!")
        self.btn_convert.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_open_excel.setEnabled(True)
        self.btn_open_folder.setEnabled(True)

        self.append_log(f"Conversion complete! Extracted {total_records} records into {out_file}", "SUCCESS")

        QMessageBox.information(
            self,
            "Conversion Complete",
            f"Multi-Format FWD Batch Conversion Completed!\n\n"
            f"• Files Processed: {total_files}\n"
            f"• Records Extracted: {total_records}\n"
            f"• Consolidated Excel: {out_file}\n\n"
            f"Sorted: LHS (Ascending) -> RHS (Descending)"
        )

    def on_worker_error(self, err: str):
        self.progress_bar.setFormat("Error during processing")
        self.btn_convert.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_remove.setEnabled(True)

        self.append_log(err, "ERROR")
        QMessageBox.critical(self, "Conversion Error", err)

    def on_open_excel(self):
        if self.last_output_file and os.path.exists(self.last_output_file):
            try:
                os.startfile(self.last_output_file)
            except Exception as e:
                QMessageBox.warning(self, "Open Error", str(e))

    def on_open_folder(self):
        if self.last_output_file:
            folder = os.path.dirname(os.path.abspath(self.last_output_file))
            if os.path.exists(folder):
                try:
                    os.startfile(folder)
                except Exception as e:
                    QMessageBox.warning(self, "Open Error", str(e))


def launch_gui():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
