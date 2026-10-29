"""Metadata-only scan filtering never needs a provider account or live network."""
from datetime import date, datetime
import pytest
from fonesi_edit.downloads import (
    normalize_scan_date, normalize_scan_metadata,
    parse_scan_metadata_filters, scan_matches_metadata,
)


@pytest.mark.parametrize(('raw', 'expected'), [
    ('20240229', '20240229'),
    ('2024-02-29', '20240229'),
    (date(2024, 2, 29), '20240229'),
    (datetime(2024, 2, 29, 23, 30), '20240229'),
    ('20260229', None),
    ('2024-02-30', None),
    ('2024011', None),
    ('2024/01/01', None),
    (False, None),
    (None, None),
])
def test_scan_dates_are_calendar_checked(raw, expected):
    assert normalize_scan_date(raw) == expected


def test_scan_metadata_is_whitelisted_and_invalid_values_become_missing():
    raw = {'date': datetime(2024, 2, 29), 'duration': '60.5', 'width': '1920',
           'height': 1080, 'url': 'https://example.invalid/?token=SECRET',
           'description': 'private', 'cookie': 'SECRET'}
    assert normalize_scan_metadata(raw) == {
        'upload_date': '20240229', 'duration': 60.5,
        'width': 1920, 'height': 1080,
    }
    assert isinstance(raw['date'], datetime)
    assert normalize_scan_metadata({'upload_date': '20260229',
                                    'duration': float('nan'),
                                    'width': True, 'height': -5}) == {}
    assert normalize_scan_metadata({'date': date(2024, 2, 29), 'height': '720.5'}) == {
        'upload_date': '20240229'}
    assert normalize_scan_metadata(None) == {}


def test_scan_metadata_ranges_are_inclusive_and_missing_policy_is_per_field():
    filters = parse_scan_metadata_filters(
        after='2024-02-01', before='20240229',
        duration_min='30', duration_max='60.5',
        max_height='1080', include_missing=False)
    assert filters['after'] == '20240201'
    item = {'upload_date': '20240229', 'duration': 60.5, 'height': 1080}
    assert scan_matches_metadata(item, filters)
    assert not scan_matches_metadata({**item, 'upload_date': '20240301'}, filters)
    assert not scan_matches_metadata({**item, 'duration': 60.6}, filters)
    assert not scan_matches_metadata({**item, 'height': 1081}, filters)
    assert not scan_matches_metadata({**item, 'duration': None}, filters)
    include = parse_scan_metadata_filters(after='20240201',duration_min='30',
                                          max_height='1080')
    assert scan_matches_metadata({}, include)  # old scans remain visible by default
    assert scan_matches_metadata({'height': None, 'duration': 40}, include)
    assert not scan_matches_metadata({'duration': 2}, include)
    assert scan_matches_metadata({}, parse_scan_metadata_filters(include_missing=False))


@pytest.mark.parametrize('settings', [
    {'after': '2026-02-29'},
    {'before': '2024-13-01'},
    {'after': '20240301', 'before': '20240201'},
    {'duration_min': '-1'},
    {'duration_max': 'nan'},
    {'duration_min': '1e309'},
    {'duration_max': 'inf'},
    {'duration_min': '61', 'duration_max': '60'},
    {'max_height': '0'},
    {'max_height': '720.5'},
    {'max_height': 'abc'},
    {'include_missing': 'false'},
])
def test_scan_filter_rejects_invalid_input_without_partial_application(settings):
    with pytest.raises(ValueError):
        parse_scan_metadata_filters(**settings)
