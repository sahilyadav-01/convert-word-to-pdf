# FWD Data Converter Pro

**Standalone Windows Desktop Application (`.EXE`)** for batch processing multi-format Falling Weight Deflectometer (FWD) and road survey data into a single consolidated, professionally formatted Excel workbook (`.xlsx`).

---

## 🚀 Supported Input Formats

You can select and batch process multiple files across different formats simultaneously:

| Format Category | Supported Extensions | Parser Engine |
| :--- | :--- | :--- |
| **Microsoft Word** | `.docx`, `.doc` | `python-docx` / COM |
| **PDF Documents** | `.pdf` | `pypdf` |
| **CSV Spreadsheets** | `.csv` | `csv` (auto-detects delimiter `,`, `;`, `\t`) |
| **Microsoft Excel** | `.xlsx`, `.xls` | `openpyxl` |
| **Plain Text** | `.txt` | Tabular & report line parser |
| **FWD Equipment** | `.fwd` | Dynatest, KUAB, Carl Bro, FastFWD ASCII |

---

## 🔄 Core Processing Architecture

```text
                  INPUT FILES (Mixed Formats)
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       Word (.docx)       PDF (.pdf)         CSV / Excel / FWD / TXT
            │                  │                  │
            └──────────────────┼──────────────────┘
                               ▼
                       FORMAT DETECTOR
                               │
                               ▼
                     MULTI-FORMAT PARSERS
                               │
                               ▼
                      COMMON DATA MODEL
                      (Side, Stn, Force, D0..D6, Temp, Lat, Long, etc.)
                               │
                               ▼
                       LHS / RHS DETECTOR
                               │
                        ┌──────┴──────┐
                        ▼             ▼
                    LHS Files     RHS Files
                        │             │
                        ▼             ▼
                    Increasing    Decreasing
                     Chainage      Chainage
                        │             │
                        └──────┬──────┘
                               ▼
                         LHS FIRST (+) RHS
                               │
                               ▼
                       VALIDATION ENGINE
                               │
                               ▼
                        XLSX GENERATOR
                               │
                               ▼
                   FWD_Consolidated_Output.xlsx
```

---

## 📋 Common Data Model (`FWDRecord`)

Every parser normalizes its records into a unified structure:
* **Side:** `LHS` or `RHS` (or `UNKNOWN`)
* **Station ID:** e.g. `D100`, `D105`
* **Station / Chainage:** Numeric chainage for directional sorting (e.g. `100.0`, `10+250` $\rightarrow$ `10250.0`)
* **Force:** Target impact load in kN (e.g. `40.0 kN`)
* **Deflections ($D_0$ through $D_6$):** Sensor deflection values (in mm)
* **Temperatures:** Air Temperature & Asphalt / Pavement Temperature (°C)
* **GPS:** Latitude & Longitude
* **Metadata:** Survey Time, Remarks, Source File, Source Format

---

## 📊 Consolidated Excel Output Structure

The output workbook (`.xlsx`) automatically generates three dedicated sheets:
1. **Sheet 1: `Final Data`**
   - Consolidated table with all LHS records first (ordered by increasing chainage), followed by all RHS records (ordered by decreasing chainage).
   - Styled with dark navy header (`#1F4E79`), bold white text, alternating row fills (subtle blue for LHS, mint green for RHS), thin borders, frozen header row, and active auto-filters.
2. **Sheet 2: `Processing Summary`**
   - High-level metrics: Total files processed, breakdown by format (`Word`, `PDF`, `CSV`, `Excel`, `TXT`, `FWD`), LHS/RHS file counts, total D records extracted, filter rule, and timestamp.
3. **Sheet 3: `Error Log`**
   - Detailed warning and error log for files with unidentifiable sides or missing records.

---

## 🖥️ How to Run

### 1. Standalone Windows Executable (.exe)
No Python or Office installation required on the target machine:
```text
dist\FWD Data Converter Pro\FWD Data Converter Pro.exe
```

### 2. Launch GUI via Python
```bash
python app.py
```

### 3. Batch CLI Mode
```bash
python app.py --cli -i samples/ -o FWD_Consolidated_Output.xlsx
```

---

## 🧪 Automated Testing

```bash
python -m pytest -v tests/
```
All 15 unit and integration tests validate the format detectors, individual parsers, directional sorter, and the unified batch pipeline.
