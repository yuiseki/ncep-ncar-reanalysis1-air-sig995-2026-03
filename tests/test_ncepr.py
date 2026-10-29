from datetime import datetime

import ncepr


def row(name, modified, size):
    return (
        '<tr class="odd"><td class="indexcolicon"><img src="/icons/ball.gray.gif" alt="[   ]"/></td>'
        f'<td class="indexcolname"><a href="{name}">{name}</a></td>'
        f'<td class="indexcollastmod">{modified}  </td><td class="indexcolsize"> {size}</td>'
        '<td class="indexcoldesc">&nbsp;</td></tr>\n'
    )


LISTING = (
    row("air.sig995.1948.nc", "2023-01-11 12:06", "21M")
    + row("air.sig995.2026.nc", "2026-03-19 08:28", "4.4M")
    + row("skt.sfc.gauss.1948.nc", "2023-02-21 16:28", "35M")
    + row("air.sig995.2025.nc.bak", "2026-01-05 09:29", "1M")
)


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


def test_time_axis_check_finds_a_gap_and_a_wrong_step():
    six = 6.0
    assert ncepr.time_problems([0.0, 6.0, 12.0, 18.0], six) == []
    assert ncepr.time_problems([0.0, 6.0, 18.0], six) == [(1, 12.0)]
    assert ncepr.time_problems([0.0, 6.0, 6.0], six) == [(1, 0.0)]


def test_hours_since_1800_to_datetime():
    assert ncepr.hours_to_datetime(1314864.0).isoformat() == "1950-01-01T00:00:00"
