import os
import sys
from datetime import datetime
import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from adapters.base import parse_age_days


def test_parse_age_relative_strings():
    assert parse_age_days("today") == 0
    assert parse_age_days("just now") == 0
    assert parse_age_days("3d") == 3
    assert parse_age_days("5 days") == 5
    assert parse_age_days("2mo") == 60
    assert parse_age_days("12h") == 0


def test_parse_age_explicit_past_year():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 10, 2024", reference_date=ref_date) > 700
    assert parse_age_days("10/24/2024", reference_date=ref_date) > 700


def test_parse_age_yearless_date_current_year():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 01", reference_date=ref_date, default_year=2026) == 3
    assert parse_age_days("Sep 28", reference_date=ref_date, default_year=2026) == 6


def test_parse_age_yearless_date_past_default_year():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 10", reference_date=ref_date, default_year=2024) > 700


def test_parse_age_fallbacks():
    assert parse_age_days("") == 999
    assert parse_age_days(None) == 999
    assert parse_age_days("unknown-date-format") == 7


def test_parse_age_day_month_format():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("1 Oct", reference_date=ref_date, default_year=2026) == 3
    assert parse_age_days("10 Oct 2024", reference_date=ref_date) > 700


def test_parse_age_iso_format():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("2026-10-01", reference_date=ref_date) == 3
    assert parse_age_days("2024-10-10", reference_date=ref_date) > 700


def test_parse_age_future_date():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 10, 2026", reference_date=ref_date) == 0


def test_parse_age_multiples_of_ten_days():
    assert parse_age_days("0d") == 0
    assert parse_age_days("0 days") == 0
    assert parse_age_days("10d") == 10
    assert parse_age_days("20d") == 20
    assert parse_age_days("30d") == 30
    assert parse_age_days("10 days") == 10


def test_parse_age_relative_weeks_and_years():
    assert parse_age_days("yesterday") == 1
    assert parse_age_days("1 week") == 7
    assert parse_age_days("2w") == 14
    assert parse_age_days("1 year ago") == 365
    assert parse_age_days("2y") == 730


def test_parse_age_string_default_year():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 10", reference_date=ref_date, default_year="2024") > 700
    assert parse_age_days("Oct 01", reference_date=ref_date, default_year="2026") == 3


def test_parse_age_slash_two_digit_year():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("10/24/24", reference_date=ref_date) > 700
    assert parse_age_days("10/01/26", reference_date=ref_date) == 3


def test_parse_age_ordinal_dates():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 1st", reference_date=ref_date, default_year=2026) == 3
    assert parse_age_days("Oct 2nd", reference_date=ref_date, default_year=2026) == 2
    assert parse_age_days("1st Oct", reference_date=ref_date, default_year=2026) == 3
    assert parse_age_days("2nd Oct", reference_date=ref_date, default_year=2026) == 2


def test_parse_age_month_year_format():
    ref_date = datetime(2026, 10, 4)
    assert parse_age_days("Oct 2024", reference_date=ref_date) > 700
    assert parse_age_days("October 2026", reference_date=ref_date) == 3


