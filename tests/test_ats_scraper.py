import pytest
from datetime import datetime
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts")))

from ats_scraper import (
    resolve_ats_subdocument_url,
    extract_json_ld,
    parse_position_type,
    parse_closing_deadline,
    fetch_page_content,
    inspect_job_page,
)


def test_resolve_icims_iframe():
    html = '''<html><body><iframe src="https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"></iframe></body></html>'''
    base_url = "https://careers-cotiviti.icims.com/jobs/19531/job"
    resolved = resolve_ats_subdocument_url(base_url, html)
    assert resolved == "https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"


def test_resolve_iframe_preceded_by_analytics():
    html = '''<html><body>
      <iframe src="https://www.googletagmanager.com/ns.html?id=GTM-1234"></iframe>
      <iframe src="https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"></iframe>
    </body></html>'''
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


def test_extract_json_ld_graph():
    html = '''
    <html><head><script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {"@type": "WebSite", "name": "Company Careers"},
        {
          "@type": "JobPosting",
          "title": "Data Science Intern",
          "employmentType": "FULL_TIME"
        }
      ]
    }
    </script></head></html>
    '''
    data = extract_json_ld(html)
    assert data is not None
    assert data.get("title") == "Data Science Intern"
    assert data.get("employmentType") == "FULL_TIME"


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


def test_parse_position_type_space_separated_and_json_ld_dash():
    html = "<div><p>Position Type: Full Time</p></div>"
    pos_type, hours = parse_position_type(html, json_ld=None)
    assert pos_type == "Full-Time"
    assert hours == "Full-Time (40 hrs/week)"

    json_ld = {"employmentType": "FULL-TIME"}
    pos_type2, hours2 = parse_position_type("", json_ld=json_ld)
    assert pos_type2 == "Full-Time"
    assert hours2 == "Full-Time (40 hrs/week)"

    json_ld_space = {"employmentType": "Full Time"}
    pos_type3, hours3 = parse_position_type("", json_ld=json_ld_space)
    assert pos_type3 == "Full-Time"
    assert hours3 == "Full-Time (40 hrs/week)"


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


def test_parse_closing_deadline_json_ld_iso_tz_offset():
    # validThrough with ISO timezone offset
    json_ld = {"validThrough": "2026-12-31T23:59:59-05:00"}
    ref_date = datetime(2026, 10, 4)
    deadline_dt, is_expired, reason = parse_closing_deadline("", json_ld=json_ld, reference_date=ref_date)
    assert deadline_dt == datetime(2026, 12, 31, 23, 59, 59)
    assert is_expired is False

    # validThrough in past with ISO +02:00
    json_ld_past = {"validThrough": "2026-06-30T12:00:00+02:00"}
    deadline_dt2, is_expired2, reason2 = parse_closing_deadline("", json_ld=json_ld_past, reference_date=ref_date)
    assert deadline_dt2 == datetime(2026, 6, 30, 12, 0, 0)
    assert is_expired2 is True
    assert "2026-06-30" in reason2


def test_parse_closing_deadline_year_first_and_ordinal():
    ref_date = datetime(2026, 10, 4)

    # YYYY/MM/DD slashed format
    html_year_first = "<p>Application deadline: 2026/11/20</p>"
    deadline_dt, is_expired, reason = parse_closing_deadline(html_year_first, json_ld=None, reference_date=ref_date)
    assert deadline_dt == datetime(2026, 11, 20)
    assert is_expired is False

    # Ordinal date: "July 18th, 2026"
    html_ordinal = "<p>Applications close on July 18th, 2026</p>"
    deadline_dt2, is_expired2, reason2 = parse_closing_deadline(html_ordinal, json_ld=None, reference_date=ref_date)
    assert deadline_dt2 == datetime(2026, 7, 18)
    assert is_expired2 is True
    assert "closed on 2026-07-18" in reason2


def test_inspect_job_page_full_flow_icims_expired():
    parent_html = '''<html><body><iframe src="https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"></iframe></body></html>'''
    iframe_html = '''
    <html>
      <div class="iCIMS_JobHeaderTag">
        <dt class="iCIMS_JobHeaderField">Position Type</dt>
        <dd class="iCIMS_JobHeaderData"><span>Full-Time</span></dd>
      </div>
      <div>
        <p>Date of posting: 6/18/2026</p>
        <p>We anticipate that the application window will close on 7/18/2026.</p>
      </div>
    </html>
    '''
    ref_date = datetime(2026, 10, 4)

    def mock_fetch(url, timeout=10):
        if "in_iframe=1" in url:
            return iframe_html, 200, url
        return parent_html, 200, url

    with patch("ats_scraper.fetch_page_content", side_effect=mock_fetch):
        info = inspect_job_page("https://careers-cotiviti.icims.com/jobs/19531/job", reference_date=ref_date)
        assert info["is_active"] is False
        assert "closed on 2026-07-18" in info["reason"].lower()
        assert info["position_type"] == "Full-Time"
        assert info["hours_per_week"] == "Full-Time (40 hrs/week)"


def test_inspect_job_page_active_part_time():
    html = '''
    <html>
      <p>Position Type: Part-Time</p>
      <p>Schedule will not exceed 29hrs/week.</p>
      <p>We anticipate that the application window will close on 12/01/2026.</p>
    </html>
    '''
    ref_date = datetime(2026, 10, 4)

    def mock_fetch(url, timeout=10):
        return html, 200, url

    with patch("ats_scraper.fetch_page_content", side_effect=mock_fetch):
        info = inspect_job_page("https://example.com/job/123", reference_date=ref_date)
        assert info["is_active"] is True
        assert info["position_type"] == "Part-Time"
        assert "29" in info["hours_per_week"] or "Part-Time" in info["hours_per_week"]


def test_inspect_job_page_missing_url():
    info = inspect_job_page("")
    assert info["is_active"] is False
    assert info["reason"] == "Missing URL"


def test_inspect_job_page_http_error_404():
    import urllib.error
    with patch("ats_scraper.fetch_page_content", side_effect=urllib.error.HTTPError("https://example.com/job/404", 404, "Not Found", {}, None)):
        info = inspect_job_page("https://example.com/job/404")
        assert info["is_active"] is False
        assert "Dead Link (HTTP 404)" in info["reason"]
        assert info["is_expired"] is True


def test_inspect_job_page_http_error_403_protected():
    import urllib.error
    with patch("ats_scraper.fetch_page_content", side_effect=urllib.error.HTTPError("https://example.com/job/403", 403, "Forbidden", {}, None)):
        info = inspect_job_page("https://example.com/job/403")
        assert info["is_active"] is True
        assert "Protected ATS (HTTP 403)" in info["reason"]


def test_inspect_job_page_network_exception():
    with patch("ats_scraper.fetch_page_content", side_effect=Exception("Connection timed out")):
        info = inspect_job_page("https://example.com/job/timeout")
        assert info["is_active"] is True
        assert "Network skip" in info["reason"]


def test_inspect_job_page_subdocument_404_inactive():
    import urllib.error
    parent_html = '<html><body><iframe src="https://careers-example.icims.com/jobs/123/job?in_iframe=1"></iframe></body></html>'

    def mock_fetch(url, timeout=10):
        if "in_iframe=1" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return parent_html, 200, url

    with patch("ats_scraper.fetch_page_content", side_effect=mock_fetch):
        info = inspect_job_page("https://careers-example.icims.com/jobs/123/job")
        assert info["is_active"] is False
        assert "Dead Link in ATS Subdocument (HTTP 404)" in info["reason"]
        assert info["is_expired"] is True


def test_inspect_job_page_http_500():
    import urllib.error
    with patch("ats_scraper.fetch_page_content", side_effect=urllib.error.HTTPError("https://example.com/job/500", 500, "Internal Server Error", {}, None)):
        info = inspect_job_page("https://example.com/job/500")
        assert info["is_active"] is True
        assert "HTTP Error 500" in info["reason"]
        assert info["is_expired"] is False


def test_inspect_job_page_fallback_to_parent_json_ld():
    parent_html = '''
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Machine Learning Engineer",
          "employmentType": "FULL_TIME",
          "validThrough": "2026-12-31T23:59:59Z"
        }
        </script>
      </head>
      <body>
        <iframe src="https://careers-example.icims.com/jobs/456/job?in_iframe=1"></iframe>
      </body>
    </html>
    '''
    sub_html = '''
    <html>
      <body>
        <div>Description without JSON-LD</div>
      </body>
    </html>
    '''
    ref_date = datetime(2026, 10, 4)

    def mock_fetch(url, timeout=10):
        if "in_iframe=1" in url:
            return sub_html, 200, url
        return parent_html, 200, url

    with patch("ats_scraper.fetch_page_content", side_effect=mock_fetch):
        info = inspect_job_page("https://careers-example.icims.com/jobs/456/job", reference_date=ref_date)
        assert info["is_active"] is True
        assert info["position_type"] == "Full-Time"
        assert info["hours_per_week"] == "Full-Time (40 hrs/week)"
        assert info["deadline"] == datetime(2026, 12, 31, 23, 59, 59)
        assert info["is_expired"] is False

