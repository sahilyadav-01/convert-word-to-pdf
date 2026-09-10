# Word to Excel (.xlsx) Batch Converter

Standalone Windows Desktop Application that batch-processes multiple Word documents (`.docx` / `.doc`), automatically classifies them into **LHS** and **RHS**, extracts all data records whose identifier starts with **`D`**, and generates a single consolidated Excel workbook (`.xlsx`) with directional sorting.

---

## 🚀 Key Features

* **Multi-File & Folder Batch Selection:** Select 10, 50, 100+ `.docx` or `.doc` files or select an entire folder.
* **Automatic LHS / RHS Detection:** Case-insensitive filename scanner identifies `LHS` and `RHS` files automatically (e.g. `01_LHS.docx`, `02_rhs.docx`).
* **'D' Record Extraction:** Automatically extracts records starting with `D` (e.g. `D100`, `D105`, `D500`), while ignoring other non-target records (`A...`, `B...`, `C...`).
* **Directional Chainage Ordering:**
  * **LHS Records:** Sorted in strictly **increasing** (ascending) chainage order.
  * **RHS Records:** Sorted in strictly **decreasing** (descending) chainage order.
  * **Combined Output:** All LHS records first (increasing), followed by all RHS records (decreasing).
* **Consolidated Multi-Sheet Excel Output:**
  1. **Sheet 1: `Final Data`** — Fully formatted with navy headers, bold titles, auto-fit columns, freeze panes, zebra stripes, and active auto-filters.
  2. **Sheet 2: `Processing Summary`** — Summary metrics of total files, LHS/RHS file counts, extracted record counts, and run timestamp.
  3. **Sheet 3: `Error Log`** — Detailed warning and error log for files with unidentifiable sides or missing records.
* **Modern Desktop GUI:** Built with PyQt6 featuring smooth progress bars, real-time logging, status badges, and direct "Open Excel" buttons.
* **Standalone Windows `.EXE`:** Runs natively on any Windows computer without requiring Python or Microsoft Office installed.

---

## 📂 Project Structure

```text
convert-word-to-pdf/
├── app.py                      # Main entry point (GUI or CLI mode)
├── build_exe.py                # Standalone EXE compilation script
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
│
├── src/
│   ├── __init__.py
│   ├── file_manager.py         # Batch file scanner and LHS/RHS detection
│   ├── word_reader.py          # Word document reader (.docx and .doc)
│   ├── extractor.py            # D-record parsing engine
│   ├── sorter.py               # Directional sorting (LHS ↑ / RHS ↓)
│   ├── excel_writer.py         # openpyxl 3-sheet Excel generator
│   └── gui.py                  # PyQt6 Desktop application
│
├── tests/
│   ├── test_file_manager.py    # Side detection unit tests
│   ├── test_extractor.py       # D-record extraction unit tests
│   ├── test_sorter.py          # Directional sorting unit tests
│   └── test_excel_writer.py    # Excel workbook generation unit tests
│
├── samples/                    # Sample test Word documents
│   ├── 01_LHS.docx
│   ├── 02_LHS.docx
│   ├── 03_RHS.docx
│   └── 04_RHS.docx
│
└── dist/
    └── WordToXLSX/
        └── WordToXLSX.exe      # Compiled Windows executable
```

---

## 🖥️ How to Run the Application

### 1. Launch Modern Desktop GUI
```bash
python app.py
```

### 2. Run via Command Line (CLI)
```bash
python app.py --cli -i samples -o FWD_Output.xlsx
```

### 3. Run the Standalone `.exe`
Launch directly without Python:
```text
dist\WordToXLSX\WordToXLSX.exe
```

---

## 🧪 Running Automated Tests

```bash
python -m pytest -v tests/
```
