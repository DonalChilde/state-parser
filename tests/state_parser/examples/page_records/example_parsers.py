"""Parsers and strategy for the page_records example."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from state_parser.state_parser import (
    IndexedStringBase,
    NoMatchResult,
    ParseContext,
    ParseFailureStop,
    ParseResultBase,
    ParserProtocol,
    ParseStrategyProtocol,
)

from .example_results import (
    BlankLineResult,
    FooterResult,
    HeaderResult,
    NameResult,
    RecordStartResult,
    TagResult,
    ValueResult,
)

_HEADER_RE = re.compile(r"^PAGE REPORT (?P<date>\d{4}-\d{2}-\d{2})$")
_RECORD_RE = re.compile(r"^RECORD: (?P<record_id>[A-Z]-\d+)$")
_NAME_RE = re.compile(r"^NAME: (?P<name>.+)$")
_TAG_RE = re.compile(r"^TAG: (?P<tag>.+)$")
_VALUE_RE = re.compile(r"^VALUE: (?P<key>[a-z_]+)=(?P<value>.+)$")
_FOOTER_RE = re.compile(r"^END REPORT total_records=(?P<count>\d+)$")


def _no_match(indexed_string: IndexedStringBase) -> NoMatchResult:
    return NoMatchResult(indexed_string=indexed_string)


@dataclass
class HeaderParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _HEADER_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["phase"] = "expect_post_header_blank"
        return (
            HeaderResult(
                indexed_string=indexed_string,
                report_date=match.group("date"),
            ),
            next_ctx,
        )


@dataclass
class BlankLineParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        if indexed_string.string != "":
            return _no_match(indexed_string), ctx

        phase = ctx.get("phase", "expect_header")
        if phase not in {"expect_post_header_blank", "in_record_details"}:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["phase"] = "expect_record_or_footer"
        return BlankLineResult(indexed_string=indexed_string), next_ctx


@dataclass
class RecordStartParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _RECORD_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["phase"] = "in_record_expect_name"
        return (
            RecordStartResult(
                indexed_string=indexed_string,
                record_id=match.group("record_id"),
            ),
            next_ctx,
        )


@dataclass
class NameLineParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _NAME_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["phase"] = "in_record_details"
        return NameResult(
            indexed_string=indexed_string, name=match.group("name")
        ), next_ctx


@dataclass
class TagLineParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _TAG_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        return TagResult(indexed_string=indexed_string, tag=match.group("tag")), dict(
            ctx
        )


@dataclass
class ValueLineParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _VALUE_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        return (
            ValueResult(
                indexed_string=indexed_string,
                key=match.group("key"),
                value=match.group("value"),
            ),
            dict(ctx),
        )


@dataclass
class FooterParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        match = _FOOTER_RE.match(indexed_string.string)
        if not match:
            return _no_match(indexed_string), ctx

        next_ctx = dict(ctx)
        next_ctx["phase"] = "done"
        return (
            FooterResult(
                indexed_string=indexed_string,
                total_records=int(match.group("count")),
            ),
            next_ctx,
        )


@dataclass
class FinalPhaseParser(ParserProtocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        return (
            ParseFailureStop(
                indexed_string=indexed_string,
                context=ctx,
                error_message="Input found after footer line.",
            ),
            ctx,
        )


class PageRecordsParseStrategy(ParseStrategyProtocol):
    """State-machine strategy for the page_records example page grammar."""

    def __init__(self):
        self._header = HeaderParser()
        self._blank = BlankLineParser()
        self._record_start = RecordStartParser()
        self._name = NameLineParser()
        self._tag = TagLineParser()
        self._value = ValueLineParser()
        self._footer = FooterParser()
        self._final = FinalPhaseParser()

    def expected(
        self, parse_history: list[ParseResultBase], ctx: ParseContext
    ) -> tuple[ParserProtocol, ...]:
        _ = parse_history
        phase = ctx.get("phase", "expect_header")

        if phase == "expect_header":
            return (self._header,)
        if phase == "expect_post_header_blank":
            return (self._blank,)
        if phase == "expect_record_or_footer":
            return (self._record_start, self._footer)
        if phase == "in_record_expect_name":
            return (self._name,)
        if phase == "in_record_details":
            return (self._tag, self._value, self._blank)
        if phase == "done":
            return (self._final,)

        return (self._final,)


def initial_context() -> dict[str, Any]:
    """Create a fresh parse context for this example."""

    return {"phase": "expect_header"}
