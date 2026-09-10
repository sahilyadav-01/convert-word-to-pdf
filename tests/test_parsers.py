"""Unit tests for individual format parsers."""

import pytest
from parsers.word_parser import WordParser
from parsers.pdf_parser import PDFParser
from parsers.csv_parser import CSVParser
from parsers.fwd_parser import FWDParser
from parsers.txt_parser import TXTParser
from parsers.excel_parser import ExcelParser


def test_word_parser():
    p = WordParser(prefix="D")
    records = p.parse("samples/01_LHS.docx", side="LHS")
    assert len(records) == 2
    assert records[0].station_id == "D100"
    assert records[0].station == 100.0
    assert records[0].force == 40.2
    assert records[0].d0 == 0.55


def test_pdf_parser():
    p = PDFParser(prefix="D")
    records = p.parse("samples/02_LHS.pdf", side="LHS")
    assert len(records) == 2
    assert records[0].station_id == "D110"
    assert records[0].station == 110.0


def test_csv_parser():
    p = CSVParser(prefix="D")
    records = p.parse("samples/03_RHS.csv", side="RHS")
    assert len(records) == 2
    assert records[0].station_id == "D500"
    assert records[0].station == 500.0
    assert records[0].force == 40.0
    assert records[0].d0 == 0.62


def test_fwd_parser():
    p = FWDParser(prefix="D")
    records = p.parse("samples/04_RHS.fwd", side="RHS")
    assert len(records) == 2
    assert records[0].station_id == "D490"
    assert records[0].station == 490.0


def test_txt_parser():
    p = TXTParser(prefix="D")
    records = p.parse("samples/05_LHS.txt", side="LHS")
    assert len(records) == 2
    assert records[0].station_id == "D120"
    assert records[0].station == 120.0


def test_excel_parser():
    p = ExcelParser(prefix="D")
    records = p.parse("samples/06_RHS.xlsx", side="RHS")
    assert len(records) == 2
    assert records[0].station_id == "D480"
    assert records[0].station == 480.0
    assert records[0].force == 40.1
    assert records[0].d0 == 0.53
