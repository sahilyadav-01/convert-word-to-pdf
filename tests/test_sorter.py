"""Tests for directional chainage sorting engine."""

import pytest
from core.data_model import FWDRecord
from core.sorter import DirectionalSorter


def test_directional_sorting():
    # Provide LHS and RHS records in shuffled/random order
    records = [
        FWDRecord(side="RHS", source_file="02_RHS.docx", station_id="D495", station=495.0, station_str="495"),
        FWDRecord(side="LHS", source_file="02_LHS.docx", station_id="D110", station=110.0, station_str="110"),
        FWDRecord(side="RHS", source_file="01_RHS.docx", station_id="D490", station=490.0, station_str="490"),
        FWDRecord(side="LHS", source_file="01_LHS.docx", station_id="D100", station=100.0, station_str="100"),
        FWDRecord(side="RHS", source_file="03_RHS.docx", station_id="D500", station=500.0, station_str="500"),
        FWDRecord(side="LHS", source_file="03_LHS.docx", station_id="D105", station=105.0, station_str="105"),
        FWDRecord(side="UNKNOWN", source_file="07_UNK.docx", station_id="D999", station=999.0, station_str="999"),
    ]

    sorted_res = DirectionalSorter.sort(records)
    assert len(sorted_res) == 7

    # Verify LHS come first
    assert [r.side for r in sorted_res[:3]] == ["LHS", "LHS", "LHS"]
    # Verify LHS is increasing (ascending chainage)
    assert [r.station for r in sorted_res[:3]] == [100.0, 105.0, 110.0]

    # Verify RHS come after LHS
    assert [r.side for r in sorted_res[3:6]] == ["RHS", "RHS", "RHS"]
    # Verify RHS is decreasing (descending chainage)
    assert [r.station for r in sorted_res[3:6]] == [500.0, 495.0, 490.0]

    # Verify UNKNOWN is at the end
    assert sorted_res[6].side == "UNKNOWN"
    assert sorted_res[6].station == 999.0


def test_split_and_sort():
    records = [
        FWDRecord(side="LHS", station=105.0),
        FWDRecord(side="LHS", station=100.0),
        FWDRecord(side="RHS", station=490.0),
        FWDRecord(side="RHS", station=500.0),
        FWDRecord(side="UNKNOWN", station=0.0),
    ]

    lhs, rhs, unk = DirectionalSorter.split_and_sort(records)
    assert [r.station for r in lhs] == [100.0, 105.0]
    assert [r.station for r in rhs] == [500.0, 490.0]
    assert len(unk) == 1

