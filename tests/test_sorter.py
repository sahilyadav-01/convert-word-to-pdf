"""Tests for directional chainage sorting engine."""

import pytest
from src.extractor import ExtractedRecord
from src.sorter import Sorter


def test_directional_sorting():
    # Provide LHS and RHS records in shuffled/random order
    records = [
        ExtractedRecord(side="RHS", source_file="02_RHS.docx", d_value="D495", chainage=495.0, chainage_str="495"),
        ExtractedRecord(side="LHS", source_file="02_LHS.docx", d_value="D110", chainage=110.0, chainage_str="110"),
        ExtractedRecord(side="RHS", source_file="01_RHS.docx", d_value="D490", chainage=490.0, chainage_str="490"),
        ExtractedRecord(side="LHS", source_file="01_LHS.docx", d_value="D100", chainage=100.0, chainage_str="100"),
        ExtractedRecord(side="RHS", source_file="03_RHS.docx", d_value="D500", chainage=500.0, chainage_str="500"),
        ExtractedRecord(side="LHS", source_file="03_LHS.docx", d_value="D105", chainage=105.0, chainage_str="105"),
    ]

    sorted_res = Sorter.sort_records(records)
    assert len(sorted_res) == 6

    # Verify LHS come first
    assert [r.side for r in sorted_res[:3]] == ["LHS", "LHS", "LHS"]
    # Verify LHS is increasing (ascending chainage)
    assert [r.chainage for r in sorted_res[:3]] == [100.0, 105.0, 110.0]

    # Verify RHS come after LHS
    assert [r.side for r in sorted_res[3:]] == ["RHS", "RHS", "RHS"]
    # Verify RHS is decreasing (descending chainage)
    assert [r.chainage for r in sorted_res[3:]] == [500.0, 495.0, 490.0]
