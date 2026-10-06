from datetime import datetime, timedelta
from weatherappbackV2 import date_list_creator, date_transformer
import pytest

## Date List Creator

def test_date_list_creator_returns_ten():
    result = date_list_creator("2026-06-01", "2026-06-10")
    assert len(result) == 10

def test_date_list_creator_counts_down_from_this_year():
    result = date_list_creator("2026-06-01", "2026-06-10")
    this_year = datetime.now().year
    # First tuple should use this year; last should be 9 years back.
    assert result[0][0].startswith(str(this_year))
    assert result[9][0].startswith(str(this_year - 9))

def test_date_list_creator_preserves_month_day():
    result = date_list_creator("2026-06-01", "2026-06-10")
    # Every start date should end in "-06-01", every end in "-06-10".
    for start, end in result:
        assert start[4:] == "-06-01"
        assert end[4:] == "-06-10"

def test_date_list_creator_returns_YYYYMMDD_format():
    result = date_list_creator("06-01", "06-10")
    assert len(result) == 10 
    assert isinstance(result[0], tuple) 
    assert datetime.strptime(result[0][0], "%Y-%m-%d")

## Date List Creator Properties

"""
- Returns a list of 10 items
- Each item on the list is a tuple
- Each tuple contains two items
- Each item in each tuple is a string
- Each item in each tuple is a date in the shape YYYY-MM-DD
- The list is ordered by descending years with each subsequent tuple one year less
- The most recent year is always the first year
- The least recent year is always the last year
- The calendar span between start and end date remains the same (preserves dates, only changes years)
- Preserves the "year wrap" created by date_transformer (CURRENTLY DESIGN DOES NOT, NEED TO REWORK)
"""



## Date Transformer

def test_date_transformer_returns_two_values():
    result = date_transformer("06-01", "06-10")
    assert isinstance(result, tuple)
    assert len(result) == 2

def test_date_transformer_returns_preserves_month_and_day_from_input():
    result = date_transformer("06-01", "06-10")
    assert result[0][5:10] == "06-01"
    assert result[1][5:10] == "06-10"

def test_date_transformer_returns_the_date_with_current_year():
    result = date_transformer("06-01", "06-10", 2026)
    assert result[0].startswith("2026")
    assert result[1].startswith("2026")

def test_date_transformer_wraps_at_year_change():
    result = date_transformer("12-25", "01-10")
    assert result[0].startswith("2026")
    assert result[1].startswith("2027")
    
def test_date_transformer_calls_date_span_check_and_receives_error():
    with pytest.raises(ValueError, match="Date span"):
        date_transformer("12-10", "12-01", 2026)

def test_date_transformer_returns_YYYYMMDD_shape():
    start, end = date_transformer("06-01", "06-10", 2026)
    assert datetime.strptime(start, "%Y-%m-%d")
    assert datetime.strptime(end, "%Y-%m-%d")

def test_date_transformer_fails_if_not_YYYYMMDD_shape():
    with pytest.raises(ValueError): #raises before date_span_check error, match not needed
        date_transformer("99-99", "99-99")
