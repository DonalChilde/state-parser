"""Result types and output shaping for the page_records example."""

from dataclasses import dataclass, field
from typing import Any

from state_parser.state_parser import IndexedStringBase, ParseResultBase


@dataclass
class HeaderResult(ParseResultBase):
    """Parsed page header line."""

    report_date: str


@dataclass
class RecordStartResult(ParseResultBase):
    """Parsed record start line."""

    record_id: str


@dataclass
class NameResult(ParseResultBase):
    """Parsed record name line."""

    name: str


@dataclass
class TagResult(ParseResultBase):
    """Parsed repeated tag line."""

    tag: str


@dataclass
class ValueResult(ParseResultBase):
    """Parsed repeated key/value detail line."""

    key: str
    value: str


@dataclass
class BlankLineResult(ParseResultBase):
    """Parsed structural blank line."""


@dataclass
class FooterResult(ParseResultBase):
    """Parsed footer line."""

    total_records: int


@dataclass
class ParsedRecord:
    """Structured record assembled from parsed line results."""

    record_id: str
    name: str | None = None
    tags: list[str] = field(default_factory=list)
    values: dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedPage:
    """Structured page assembled from parser output."""

    report_date: str | None = None
    records: list[ParsedRecord] = field(default_factory=list)
    footer_total_records: int | None = None


def results_to_dict(results: list[ParseResultBase]) -> dict[str, Any]:
    """Convert raw parse results into a display-friendly dictionary."""

    page = ParsedPage()
    current_record: ParsedRecord | None = None

    for result in results:
        if isinstance(result, HeaderResult):
            page.report_date = result.report_date
            continue

        if isinstance(result, RecordStartResult):
            current_record = ParsedRecord(record_id=result.record_id)
            page.records.append(current_record)
            continue

        if isinstance(result, NameResult) and current_record is not None:
            current_record.name = result.name
            continue

        if isinstance(result, TagResult) and current_record is not None:
            current_record.tags.append(result.tag)
            continue

        if isinstance(result, ValueResult) and current_record is not None:
            current_record.values[result.key] = result.value
            continue

        if isinstance(result, FooterResult):
            page.footer_total_records = result.total_records

    return {
        "report_date": page.report_date,
        "footer_total_records": page.footer_total_records,
        "parsed_record_count": len(page.records),
        "records": [
            {
                "record_id": record.record_id,
                "name": record.name,
                "tags": record.tags,
                "values": record.values,
            }
            for record in page.records
        ],
    }


def as_indexed_string(index: int, text: str) -> IndexedStringBase:
    """Create a minimal indexed-string object for tests that need one."""

    return IndexedStringBase(index=index, string=text)
