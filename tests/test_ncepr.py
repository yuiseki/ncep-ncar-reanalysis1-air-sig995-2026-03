from datetime import datetime

import ncepr

LISTING = """
<a href="air.sig995.1948.nc">air.sig995.1948.nc</a>  2023-01-11 12:06   21M  &nbsp;
<a href="air.sig995.2026.nc">air.sig995.2026.nc</a>  2026-03-19 08:28  4.4M  &nbsp;
<a href="skt.sfc.gauss.1948.nc">skt.sfc.gauss.1948.nc</a>  2023-02-21 16:28  35M
<a href="air.sig995.2025.nc.bak">air.sig995.2025.nc.bak</a> 2026-01-05 09:29 1M
"""


def test_parse_listing_keeps_only_the_wanted_variable():
    rows = ncepr.parse_listing(LISTING)
    assert [r["name"] for r in rows] == ["air.sig995.1948.nc", "air.sig995.2026.nc"]
    assert rows[1]["modified"] == datetime(2026, 3, 19, 8, 28)


def test_year_of_name():
    assert ncepr.year_of("air.sig995.1999.nc") == 1999


def test_vintage_is_the_last_month_the_content_changed():
    rows = ncepr.parse_listing(LISTING)
    assert ncepr.vintage_month(rows) == "2026-03"


def test_expected_years_are_consecutive():
    assert ncepr.missing_years([1948, 1949, 1951]) == [1950]
    assert ncepr.missing_years([2000, 2001]) == []
