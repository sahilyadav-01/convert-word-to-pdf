"""Tests for D-record extractor and chainage parsing."""

import pytest
from src.extractor import Extractor
from src.word_reader import DocumentData


def test_is_d_identifier():
    extractor = Extractor(prefix="D")
    assert extractor.is_d_identifier("D100") is True
    assert extractor.is_d_identifier("d125") is True
    assert extractor.is_d_identifier("D 130") is True
    assert extractor.is_d_identifier("D-500") is True
    assert extractor.is_d_identifier("D.450") is True

    # Negative test cases (A..., B..., C...)
    assert extractor.is_d_identifier("A123") is False
    assert extractor.is_d_identifier("B456") is False
    assert extractor.is_d_identifier("C987") is False
    assert extractor.is_d_identifier("Deflection") is False
    assert extractor.is_d_identifier("") is False


def test_parse_chainage_number():
    assert Extractor.parse_chainage_number("100") == 100.0
    assert Extractor.parse_chainage_number("125.5") == 125.5
    assert Extractor.parse_chainage_number("D105") == 105.0
    assert Extractor.parse_chainage_number("10+250") == 10250.0
    assert Extractor.parse_chainage_number("Km 45.2") == 45.2


def test_extract_table_data():
    extractor = Extractor(prefix="D")
    doc_data = DocumentData(
        file_path="dummy_01_LHS.docx",
        filename="01_LHS.docx",
        tables=[
            [
                ["Station ID", "Chainage", "Deflection 1", "Deflection 2"],
                ["A101", "50", "0.45", "0.32"],
                ["D100", "100", "0.55", "0.41"],
                ["B202", "102", "0.60", "0.45"],
                ["D105", "105", "0.52", "0.38"],
                ["C303", "108", "0.58", "0.42"],
                ["D110", "110", "0.49", "0.36"],
            ]
        ]
    )

    records = extractor.extract(doc_data, side="LHS")
    assert len(records) == 3
    assert records[0].d_value == "D100"
    assert records[0].chainage == 100.0
    assert records[1].d_value == "D105"
    assert records[1].chainage == 105.0
    assert records[2].d_value == "D110"
    assert records[2].chainage == 110.0
