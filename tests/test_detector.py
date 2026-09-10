"""Tests for Detector module."""

import pytest
from core.detector import Detector


def test_detect_format():
    assert Detector.detect_format("survey.docx") == "WORD"
    assert Detector.detect_format("report.doc") == "WORD"
    assert Detector.detect_format("data.pdf") == "PDF"
    assert Detector.detect_format("export.csv") == "CSV"
    assert Detector.detect_format("measurements.xlsx") == "EXCEL"
    assert Detector.detect_format("legacy.xls") == "EXCEL"
    assert Detector.detect_format("log.txt") == "TXT"
    assert Detector.detect_format("dynatest.fwd") == "FWD"
    assert Detector.detect_format("unknown.xyz") == "UNKNOWN"


def test_detect_side():
    assert Detector.detect_side("01_LHS.docx") == "LHS"
    assert Detector.detect_side("02_lhs.pdf") == "LHS"
    assert Detector.detect_side("03_RHS.csv") == "RHS"
    assert Detector.detect_side("04_rhs.fwd") == "RHS"
    assert Detector.detect_side("05_random.txt") == "UNKNOWN"
    assert Detector.detect_side("LHS_and_RHS.xlsx") == "UNKNOWN"
