"""Result models and output shaping for the PBS pairings example."""

from dataclasses import dataclass, field
from typing import Any

from state_parser.state_parser import ParseResultBase


@dataclass
class TableHeaderResult(ParseResultBase):
    """Parsed schedule table header."""


@dataclass
class CalendarHeaderResult(ParseResultBase):
    """Parsed calendar-range header line."""

    calendar_range: str


@dataclass
class SequenceStartResult(ParseResultBase):
    """Parsed sequence start line (SEQ)."""

    sequence_id: str


@dataclass
class ReportTimeResult(ParseResultBase):
    """Parsed report-time line (RPT)."""

    report_time: str


@dataclass
class FlightLegResult(ParseResultBase):
    """Parsed flight leg line."""

    duty_day: int
    day_pair: str
    equipment: str
    flight_number: str
    departure_station: str
    departure_time: str
    meal_code: str | None
    arrival_station: str
    arrival_time: str
    block_value: str | None


@dataclass
class ReleaseResult(ParseResultBase):
    """Parsed release line (RLS)."""

    release_time: str


@dataclass
class SequenceTotalResult(ParseResultBase):
    """Parsed sequence total line (TTL)."""

    numeric_values: list[str] = field(default_factory=list)


@dataclass
class FooterResult(ParseResultBase):
    """Parsed page footer metadata."""

    issued_date: str
    effective_date: str
    page_number: str


@dataclass
class IgnoredLineResult(ParseResultBase):
    """Parsed line that is intentionally ignored by the example."""

    category: str


def results_to_dict(results: list[ParseResultBase]) -> dict[str, Any]:
    """Convert parser results into a display-friendly summary dictionary."""

    calendar_range: str | None = None
    footer: dict[str, str] | None = None

    sequence_ids: list[str] = []
    report_times: list[str] = []
    legs: list[dict[str, Any]] = []
    releases: list[str] = []
    totals: list[list[str]] = []

    ignored_count = 0
    table_header_count = 0

    for result in results:
        if isinstance(result, TableHeaderResult):
            table_header_count += 1
            continue

        if isinstance(result, CalendarHeaderResult):
            calendar_range = result.calendar_range
            continue

        if isinstance(result, SequenceStartResult):
            sequence_ids.append(result.sequence_id)
            continue

        if isinstance(result, ReportTimeResult):
            report_times.append(result.report_time)
            continue

        if isinstance(result, FlightLegResult):
            legs.append(
                {
                    "sequence_day": result.duty_day,
                    "day_pair": result.day_pair,
                    "equipment": result.equipment,
                    "flight_number": result.flight_number,
                    "departure_station": result.departure_station,
                    "departure_time": result.departure_time,
                    "meal_code": result.meal_code,
                    "arrival_station": result.arrival_station,
                    "arrival_time": result.arrival_time,
                    "block_value": result.block_value,
                }
            )
            continue

        if isinstance(result, ReleaseResult):
            releases.append(result.release_time)
            continue

        if isinstance(result, SequenceTotalResult):
            totals.append(result.numeric_values)
            continue

        if isinstance(result, FooterResult):
            footer = {
                "issued_date": result.issued_date,
                "effective_date": result.effective_date,
                "page_number": result.page_number,
            }
            continue

        if isinstance(result, IgnoredLineResult):
            ignored_count += 1

    return {
        "calendar_range": calendar_range,
        "sequence_ids": sequence_ids,
        "sequence_count": len(sequence_ids),
        "report_time_count": len(report_times),
        "report_times": report_times,
        "leg_count": len(legs),
        "sample_legs": legs[:5],
        "release_count": len(releases),
        "sequence_total_count": len(totals),
        "table_header_count": table_header_count,
        "ignored_line_count": ignored_count,
        "footer": footer,
    }
