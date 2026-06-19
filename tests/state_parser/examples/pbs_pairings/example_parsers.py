"""Parsers and strategy for the PBS pairings schedule page example."""

from __future__ import annotations

import re
from dataclasses import dataclass

from state_parser.state_parser import (
    IndexedStringBase,
    NoMatchResult,
    ParseContext,
    ParseResultBase,
    ParserProtocol,
    ParseStrategyProtocol,
)

from .example_results import (
    CalendarHeaderResult,
    FlightLegResult,
    FooterResult,
    IgnoredLineResult,
    ReleaseResult,
    ReportTimeResult,
    SequenceStartResult,
    SequenceTotalResult,
    TableHeaderResult,
)

_CALENDAR_RE = re.compile(r"CALENDAR\s+(?P<range>[0-9/\-−]+)")
_SEQ_RE = re.compile(r"^\s*SEQ\s+(?P<seq_id>\d+)\b")
_RPT_RE = re.compile(r"^\s*RPT\s+(?P<time>\d{4}/\d{4})\b")
_RLS_RE = re.compile(r"^\s*RLS\s+(?P<time>\d{4}/\d{4})\b")
_TTL_RE = re.compile(r"^\s*TTL\b")
_FOOTER_RE = re.compile(
    r"^\s*COCKPIT\s+ISSUED\s+(?P<issued>\d{2}[A-Z]{3}\d{4})"
    r"\s+EFF\s+(?P<effective>\d{2}[A-Z]{3}\d{4}).*?PAGE\s+(?P<page>\d+)\s*$"
)


def _no_match(indexed_string: IndexedStringBase) -> NoMatchResult:
    return NoMatchResult(indexed_string=indexed_string)


@dataclass
class BlankLineParser(ParserProtocol):
    """Ignore blank lines while preserving parse continuity."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        if indexed_string.string.strip() != "":
            return _no_match(indexed_string), ctx
        return IgnoredLineResult(indexed_string=indexed_string, category="blank"), ctx


@dataclass
class SeparatorParser(ParserProtocol):
    """Parse horizontal rule separator lines."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        stripped = indexed_string.string.strip()
        if stripped and set(stripped) <= {"-", "−"}:
            return (
                IgnoredLineResult(indexed_string=indexed_string, category="separator"),
                ctx,
            )
        return _no_match(indexed_string), ctx


@dataclass
class TableHeaderParser(ParserProtocol):
    """Parse top table-title line."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        cleaned = indexed_string.string.replace("\f", "").strip()
        if (
            "DAY" not in cleaned
            or "DEPARTURE" not in cleaned
            or "ARRIVAL" not in cleaned
        ):
            return _no_match(indexed_string), ctx
        return TableHeaderResult(indexed_string=indexed_string), ctx


@dataclass
class CalendarHeaderParser(ParserProtocol):
    """Parse header line containing the PBS calendar window."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _CALENDAR_RE.search(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["calendar_range"] = match.group("range")
        return (
            CalendarHeaderResult(
                indexed_string=indexed_string,
                calendar_range=match.group("range"),
            ),
            next_ctx,
        )


@dataclass
class SequenceParser(ParserProtocol):
    """Parse sequence header lines (SEQ)."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _SEQ_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["current_sequence"] = match.group("seq_id")
        return (
            SequenceStartResult(
                indexed_string=indexed_string,
                sequence_id=match.group("seq_id"),
            ),
            next_ctx,
        )


@dataclass
class ReportParser(ParserProtocol):
    """Parse report time lines (RPT)."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _RPT_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        return (
            ReportTimeResult(
                indexed_string=indexed_string,
                report_time=match.group("time"),
            ),
            ctx,
        )


@dataclass
class FlightLegParser(ParserProtocol):
    """Parse flight-leg detail lines beginning with duty-day numbers."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        line = indexed_string.string
        stripped = line.strip()
        if not stripped or not stripped[0].isdigit():
            return _no_match(indexed_string), ctx

        parts = stripped.split()
        if len(parts) < 8:
            return _no_match(indexed_string), ctx

        if "/" not in parts[1]:
            return _no_match(indexed_string), ctx

        duty_day_str = parts[0]
        if not duty_day_str.isdigit():
            return _no_match(indexed_string), ctx

        dep_station = parts[4]
        dep_time = parts[5]
        if len(dep_station) != 3 or "/" not in dep_time:
            return _no_match(indexed_string), ctx

        meal_code: str | None = None
        arr_index = 6
        if len(parts[6]) == 1 and parts[6].isalpha():
            meal_code = parts[6]
            arr_index = 7

        if len(parts) <= arr_index + 1:
            return _no_match(indexed_string), ctx

        arr_station = parts[arr_index]
        arr_time = parts[arr_index + 1]
        if len(arr_station) != 3 or "/" not in arr_time:
            return _no_match(indexed_string), ctx

        block_value: str | None = None
        if len(parts) > arr_index + 2:
            candidate = parts[arr_index + 2]
            if candidate == "TE" or re.fullmatch(r"\d+\.\d+", candidate):
                block_value = candidate

        return (
            FlightLegResult(
                indexed_string=indexed_string,
                duty_day=int(duty_day_str),
                day_pair=parts[1],
                equipment=parts[2],
                flight_number=parts[3],
                departure_station=dep_station,
                departure_time=dep_time,
                meal_code=meal_code,
                arrival_station=arr_station,
                arrival_time=arr_time,
                block_value=block_value,
            ),
            ctx,
        )


@dataclass
class ReleaseParser(ParserProtocol):
    """Parse release lines (RLS)."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _RLS_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        return (
            ReleaseResult(
                indexed_string=indexed_string,
                release_time=match.group("time"),
            ),
            ctx,
        )


@dataclass
class TotalParser(ParserProtocol):
    """Parse sequence total lines (TTL)."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        if not _TTL_RE.match(indexed_string.string):
            return _no_match(indexed_string), ctx

        values = re.findall(r"\d+\.\d+", indexed_string.string)
        return (
            SequenceTotalResult(
                indexed_string=indexed_string,
                numeric_values=values,
            ),
            ctx,
        )


@dataclass
class FooterParser(ParserProtocol):
    """Parse final footer line containing issue/effective/page metadata."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _FOOTER_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["footer_page"] = match.group("page")
        return (
            FooterResult(
                indexed_string=indexed_string,
                issued_date=match.group("issued"),
                effective_date=match.group("effective"),
                page_number=match.group("page"),
            ),
            next_ctx,
        )


@dataclass
class LodgingParser(ParserProtocol):
    """Parse lodging information lines for completeness."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        stripped = indexed_string.string.strip()
        if not stripped:
            return _no_match(indexed_string), ctx
        if (
            " HOTEL " in f" {stripped} "
            or " INN " in f" {stripped} "
            or " MARRIOTT " in f" {stripped} "
        ):
            return (
                IgnoredLineResult(indexed_string=indexed_string, category="lodging"),
                ctx,
            )
        return _no_match(indexed_string), ctx


@dataclass
class TransportParser(ParserProtocol):
    """Parse ground-transport lines for completeness."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        stripped = indexed_string.string.strip().upper()
        if not stripped:
            return _no_match(indexed_string), ctx
        keywords = ("TAXI", "LIMO", "TRANSPORTATION", "SHUTTLE", "SKYHOP")
        if any(keyword in stripped for keyword in keywords):
            return (
                IgnoredLineResult(indexed_string=indexed_string, category="transport"),
                ctx,
            )
        return _no_match(indexed_string), ctx


@dataclass
class FallbackIgnoreParser(ParserProtocol):
    """Catch-all parser so exploratory examples can tolerate extra line variants."""

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        return IgnoredLineResult(indexed_string=indexed_string, category="other"), ctx


class PbsPairingsParseStrategy(ParseStrategyProtocol):
    """Strategy that prioritizes specific line parsers before fallback ignore."""

    def __init__(self):
        self._blank = BlankLineParser()
        self._separator = SeparatorParser()
        self._table_header = TableHeaderParser()
        self._calendar_header = CalendarHeaderParser()
        self._sequence = SequenceParser()
        self._report = ReportParser()
        self._flight_leg = FlightLegParser()
        self._release = ReleaseParser()
        self._total = TotalParser()
        self._footer = FooterParser()
        self._lodging = LodgingParser()
        self._transport = TransportParser()
        self._fallback = FallbackIgnoreParser()

    def expected(
        self, parse_history: list[ParseResultBase], ctx: ParseContext
    ) -> tuple[ParserProtocol, ...]:
        _ = parse_history
        _ = ctx
        return (
            self._blank,
            self._separator,
            self._table_header,
            self._calendar_header,
            self._sequence,
            self._report,
            self._flight_leg,
            self._release,
            self._total,
            self._footer,
            self._lodging,
            self._transport,
            self._fallback,
        )


def initial_context() -> ParseContext:
    """Create a fresh context for the PBS pairings example."""

    return {}
