"""Tests for file manager and LHS/RHS detection."""

import pytest
from src.file_manager import FileManager


def test_detect_side():
    # Standard LHS cases
    assert FileManager.detect_side("01_LHS.docx") == "LHS"
    assert FileManager.detect_side("report_lhs_km10.docx") == "LHS"
    assert FileManager.detect_side("LHS_test.doc") == "LHS"
    assert FileManager.detect_side("Survey-Lhs-2026.docx") == "LHS"

    # Standard RHS cases
    assert FileManager.detect_side("01_RHS.docx") == "RHS"
    assert FileManager.detect_side("survey_rhs_ch50.docx") == "RHS"
    assert FileManager.detect_side("Rhs_data.docx") == "RHS"

    # Unknown cases
    assert FileManager.detect_side("random_document.docx") == "UNKNOWN"
    assert FileManager.detect_side("both_LHS_and_RHS.docx") == "UNKNOWN"
