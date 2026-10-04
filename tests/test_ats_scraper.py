import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts")))

from ats_scraper import (
    resolve_ats_subdocument_url,
    extract_json_ld,
    parse_position_type,
    parse_closing_deadline
)


def test_resolve_icims_iframe():
    html = '''<html><body><iframe src="https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"></iframe></body></html>'''
    base_url = "https://careers-cotiviti.icims.com/jobs/19531/job"
    resolved = resolve_ats_subdocument_url(base_url, html)
    assert resolved == "https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"


def test_resolve_non_iframe_url():
    html = '''<html><body><div>Standard Job Board</div></body></html>'''
    base_url = "https://job-boards.greenhouse.io/datacor/jobs/123"
    resolved = resolve_ats_subdocument_url(base_url, html)
    assert resolved == base_url


def test_extract_json_ld():
    html = '''
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Machine Learning Intern",
          "employmentType": "FULL_TIME",
          "validThrough": "2026-12-31T23:59:59Z"
        }
        </script>
      </head>
    </html>
    '''
    data = extract_json_ld(html)
    assert data is not None
    assert data.get("title") == "Machine Learning Intern"
    assert data.get("employmentType") == "FULL_TIME"
    assert data.get("validThrough") == "2026-12-31T23:59:59Z"


def test_parse_position_type_icims_header():
    html = '''
    <div class="iCIMS_JobHeaderTag">
      <dt class="iCIMS_JobHeaderField">Position Type</dt>
      <dd class="iCIMS_JobHeaderData"><span>Full-Time</span></dd>
    </div>
    '''
    pos_type, hours = parse_position_type(html, json_ld=None)
    assert pos_type == "Full-Time"
    assert hours == "Full-Time (40 hrs/week)"


def test_parse_position_type_part_time_hours():
    html = '''
    <div>
      <p>Interns will have flexibility around school schedules. Please note schedule will not exceed 29hrs/week.</p>
      <span>Position Type: Part-Time</span>
    </div>
    '''
    pos_type, hours = parse_position_type(html, json_ld=None)
    assert pos_type == "Part-Time"
    assert "29" in hours or "20-30" in hours


def test_parse_closing_deadline_past():
    html = '''
    <p>Date of posting: 6/18/2026</p>
    <p>Applications are assessed on a rolling basis. We anticipate that the application window will close on 7/18/2026, but may change.</p>
    '''
    ref_date = datetime(2026, 10, 4)
    deadline_dt, is_expired, reason = parse_closing_deadline(html, json_ld=None, reference_date=ref_date)
    assert deadline_dt == datetime(2026, 7, 18)
    assert is_expired is True
    assert "closed on 2026-07-18" in reason.lower()


def test_parse_closing_deadline_future():
    html = '''
    <p>We anticipate that the application window will close on 11/15/2026.</p>
    '''
    ref_date = datetime(2026, 10, 4)
    deadline_dt, is_expired, reason = parse_closing_deadline(html, json_ld=None, reference_date=ref_date)
    assert deadline_dt == datetime(2026, 11, 15)
    assert is_expired is False
    assert reason == ""
