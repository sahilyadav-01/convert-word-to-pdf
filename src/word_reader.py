"""Word document reader supporting .docx and .doc structures."""

import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DocumentData:
    """Contains raw parsed data from a Word document."""
    file_path: str
    filename: str
    tables: List[List[List[str]]] = field(default_factory=list)  # list of tables, each table is rows of cells
    paragraphs: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class WordReader:
    """Reads Word documents (.docx and legacy .doc)."""

    @staticmethod
    def read_docx(file_path: str) -> DocumentData:
        """Read a .docx file using python-docx."""
        import docx

        data = DocumentData(
            file_path=file_path,
            filename=os.path.basename(file_path)
        )

        try:
            doc = docx.Document(file_path)

            # Read all tables
            for table in doc.tables:
                table_rows = []
                for row in table.rows:
                    # Clean and collect cell text
                    row_cells = [cell.text.strip() for cell in row.cells]
                    # De-duplicate consecutive identical cells caused by merged cells in Word
                    # while preserving distinct columns
                    cleaned_row = []
                    prev_cell = None
                    for cell_txt in row_cells:
                        cleaned_row.append(cell_txt)
                    table_rows.append(cleaned_row)
                if table_rows:
                    data.tables.append(table_rows)

            # Read all paragraphs
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    data.paragraphs.append(txt)

            data.success = True
        except Exception as e:
            data.success = False
            data.error_message = f"Failed to read .docx: {str(e)}"

        return data

    @staticmethod
    def convert_doc_to_docx(doc_path: str) -> Optional[str]:
        """Convert legacy .doc to .docx on Windows using Word COM if available."""
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False

            temp_dir = tempfile.mkdtemp()
            docx_path = os.path.join(temp_dir, os.path.splitext(os.path.basename(doc_path))[0] + ".docx")
            
            doc = word.Documents.Open(os.path.abspath(doc_path))
            # 16 corresponds to wdFormatXMLDocument (.docx)
            doc.SaveAs2(os.path.abspath(docx_path), FileFormat=16)
            doc.Close()
            word.Quit()
            return docx_path
        except Exception:
            return None

    @classmethod
    def read(cls, file_path: str) -> DocumentData:
        """Unified read method supporting both .docx and .doc."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".docx":
            return cls.read_docx(file_path)
        elif ext == ".doc":
            # Attempt COM conversion
            converted_path = cls.convert_doc_to_docx(file_path)
            if converted_path and os.path.exists(converted_path):
                try:
                    res = cls.read_docx(converted_path)
                    res.file_path = file_path
                    res.filename = os.path.basename(file_path)
                    return res
                finally:
                    # Clean up temporary converted docx
                    try:
                        shutil.rmtree(os.path.dirname(converted_path), ignore_errors=True)
                    except Exception:
                        pass
            else:
                return DocumentData(
                    file_path=file_path,
                    filename=os.path.basename(file_path),
                    success=False,
                    error_message="Legacy .doc format requires Microsoft Word COM to convert. Please save as .docx."
                )
        else:
            return DocumentData(
                file_path=file_path,
                filename=os.path.basename(file_path),
                success=False,
                error_message=f"Unsupported file extension: {ext}"
            )
