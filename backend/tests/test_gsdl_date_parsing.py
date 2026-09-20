import pytest
from datetime import datetime
from backend.app.domain.delhi.digital_twin.ingestion.historical_flood_ingestor import _parse_gsdl_date

def test_parse_gsdl_date_standard():
    assert _parse_gsdl_date("2024-06-28") == datetime(2024, 6, 28)
    assert _parse_gsdl_date("28.06.2024") == datetime(2024, 6, 28)

def test_parse_gsdl_date_non_standard_formats():
    # Test cases that should work
    assert _parse_gsdl_date("1 1.08.2024") == datetime(2024, 8, 1)
    assert _parse_gsdl_date("26 07.2024") == datetime(2024, 7, 26)
    assert _parse_gsdl_date("1 05.2023") == datetime(2023, 5, 1)
    assert _parse_gsdl_date("2 10.2024") == datetime(2024, 10, 2)
    assert _parse_gsdl_date("23.062023") == datetime(2023, 6, 23)
