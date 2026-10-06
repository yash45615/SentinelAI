import pytest
from fastapi import HTTPException

from app.services.incident_manager import (
    ALLOWED_TRANSITIONS,
    VALID_STATUSES,
    validate_status,
)


def test_all_expected_statuses_exist():
    expected = {
        "DETECTED",
        "TRIAGED",
        "INVESTIGATING",
        "ROOT_CAUSE_IDENTIFIED",
        "REMEDIATION_PENDING",
        "REMEDIATING",
        "VERIFYING",
        "RESOLVED",
        "FAILED",
        "CANCELLED",
    }

    assert expected == VALID_STATUSES


def test_detected_can_move_to_triaged():
    assert "TRIAGED" in ALLOWED_TRANSITIONS["DETECTED"]


def test_triaged_can_move_to_investigating():
    assert "INVESTIGATING" in ALLOWED_TRANSITIONS["TRIAGED"]


def test_investigating_can_identify_root_cause():
    assert (
        "ROOT_CAUSE_IDENTIFIED"
        in ALLOWED_TRANSITIONS["INVESTIGATING"]
    )


def test_resolved_is_terminal():
    assert ALLOWED_TRANSITIONS["RESOLVED"] == set()


def test_cancelled_is_terminal():
    assert ALLOWED_TRANSITIONS["CANCELLED"] == set()


def test_failed_is_terminal():
    assert ALLOWED_TRANSITIONS["FAILED"] == set()


def test_valid_status():
    assert validate_status("triaged") == "TRIAGED"


def test_invalid_status():
    with pytest.raises(HTTPException):
        validate_status("NOT_A_REAL_STATUS")