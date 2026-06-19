"""Protocol-driven building blocks for stateful parsing of semi-structured text.

This module defines a small framework for orchestrating parser selection and
execution over an ordered stream of indexed strings.

Core flow:
1. An ``IndexedStringProviderProtocol`` yields input items.
2. ``StateParser`` asks a ``ParseStrategyProtocol`` which parsers are expected
    for the current state.
3. Parsers are tried in order until one returns a non-``NoMatchResult``.
4. Terminal parse failures raise immediately; unmatched input raises
    ``NoMatchingParser``.

The intent is to keep orchestration generic while letting task-specific parser
implementations and strategies encode domain rules.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

type ParseContext = dict[str, Any]


class StateParserError(Exception):
    """Base exception for all state parser orchestration errors."""

    def __init__(self, *args: Any):
        super().__init__(*args)


class ParserStopError(StateParserError):
    """Raised when a parser reports a terminal failure.

    Wraps a ``ParseFailureStop`` result so callers can inspect failure context
    and the original error message.
    """

    def __init__(self, parse_failure: ParseFailureStop):
        self.parse_failure = parse_failure
        super().__init__(parse_failure.error_message)


class NoMatchingParser(StateParserError):
    """Raised when no expected parser can handle an input item.

    This is raised by ``StateParser`` after exhausting all parsers returned by
    ``ParseStrategyProtocol.expected`` for the current input.
    """

    def __init__(self, parse_result: NoMatchResult):
        self.parse_result = parse_result
        super().__init__("No matching parser found for the parse result.")


@dataclass
class IndexedStringBase:
    """Input unit passed through the parser pipeline.

    Attributes:
        index: Source position identifier (line number, offset, token id, etc.).
        string: Raw text to parse at that position.
    """

    index: Any
    string: str


@dataclass
class IndexedStringInt(IndexedStringBase):
    """``IndexedStringBase`` specialization with an integer index.

    Useful when the input position is naturally represented as a line number or
    character offset.
    """

    index: int


@dataclass
class ParseResultBase:
    """Base type for all parser return results.

    Parsers should return concrete subclasses to communicate how orchestration
    should proceed.
    """

    indexed_string: IndexedStringBase


@dataclass
class ParseFailureStop(ParseResultBase):
    """Result indicating an unrecoverable parse failure.

    Returning this from a parser causes ``StateParser`` to raise
    ``ParserStopError`` immediately.

    Attributes:
        context: Parse context at the time of failure.
        error_message: Human-readable failure detail.
    """

    context: ParseContext
    error_message: str


@dataclass
class NoMatchResult(ParseResultBase):
    """Result indicating the current parser does not apply to the input.

    ``StateParser`` treats this as a non-terminal miss and tries the next parser
    in the expected parser tuple. If all expected parsers return ``NoMatchResult``,
    ``StateParser`` raises ``NoMatchingParser``.
    """

    pass


class ParserProtocol(Protocol):
    """Contract for a parser that attempts to parse one indexed string.

    Implementations can mutate and return context to carry state across inputs.
    """

    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]:
        """Parse a single indexed string.

        Args:
            indexed_string: Current input item.
            ctx: Current parse context.

        Returns:
            A tuple of ``(parse_result, updated_context)``.

            Recommended result semantics:
            - Return ``NoMatchResult`` when this parser should be skipped.
            - Return ``ParseFailureStop`` for unrecoverable parse failures.
            - Return a task-specific ``ParseResultBase`` subclass on success.
        """
        ...


class ParseStrategyProtocol(Protocol):
    """Contract for selecting which parsers to try next.

    Strategy implementations encode state-machine rules by choosing parser order
    from recent parse history and current context.
    """

    def expected(
        self, parse_history: list[ParseResultBase], ctx: ParseContext
    ) -> tuple[ParserProtocol, ...]:
        """Return parsers to try, in priority order, for the next input item.

        Args:
            parse_history: Most recent parse results, clipped to the configured
                ``StateParser.parser_lookback`` window.
            ctx: Current parse context.

        Returns:
            A tuple of parser instances ordered from most to least likely.
        """
        ...


class IndexedStringProviderProtocol(Protocol):
    """Contract for providing ordered input to ``StateParser``."""

    def indexed_string(self) -> Iterable[IndexedStringBase]:
        """Yield indexed strings in the order they should be parsed."""
        ...


class StateParser:
    """Orchestrates parser selection and execution for indexed text input.

    ``StateParser`` does not implement domain parsing itself. Instead, it:
    - obtains candidate parsers from ``ParseStrategyProtocol``,
    - tries them in order,
    - records successful parse results,
    - and raises explicit exceptions for terminal failure or no match.
    """

    def __init__(
        self,
        parse_strategy: ParseStrategyProtocol,
        parser_lookback: int = 5,
    ):
        """Initialize a state parser.

        Args:
            parse_strategy: Strategy used to select candidate parsers.
            parser_lookback: Number of most recent parse results provided to
                ``parse_strategy.expected``. Use ``0`` to disable history.

        Raises:
            TypeError: If ``parser_lookback`` is not an ``int``.
            ValueError: If ``parser_lookback`` is negative.
        """
        if type(parser_lookback) is not int:
            raise TypeError("parser_lookback must be an integer.")
        if parser_lookback < 0:
            raise ValueError("parser_lookback must be a non-negative integer.")

        self._parse_strategy = parse_strategy
        self._parser_lookback = parser_lookback

    def run(
        self,
        indexed_string_provider: IndexedStringProviderProtocol,
        ctx: ParseContext,
    ) -> list[ParseResultBase]:
        """Run parsing over all input from the provider.

        Args:
            indexed_string_provider: Source of ordered ``IndexedStringBase``
                items to parse.
            ctx: Initial parse context. Parsers may mutate and replace it.

        Returns:
            Parse results produced by successful parser matches in this run.

        Raises:
            ParserStopError: If a parser returns ``ParseFailureStop``.
            NoMatchingParser: If no expected parser matches an input item.

        Notes:
            Parser trial behavior per input item:
            1. Query strategy for expected parsers.
            2. Try each parser in order.
            3. On ``NoMatchResult``, continue to the next parser.
            4. On first non-``NoMatchResult`` success, record result and move to
               the next input item.
        """
        results: list[ParseResultBase] = []
        for indexed_string in indexed_string_provider.indexed_string():
            if self._parser_lookback == 0:
                lookback_history = []
            else:
                lookback_history = results[-self._parser_lookback :]
            expected_parsers = self._parse_strategy.expected(lookback_history, ctx)
            matched_parser = False
            for parser in expected_parsers:
                parse_result, ctx = parser.parse(indexed_string, ctx)
                if isinstance(parse_result, ParseFailureStop):
                    raise ParserStopError(parse_result)
                if isinstance(parse_result, NoMatchResult):
                    continue
                results.append(parse_result)
                matched_parser = True
                break
            if not matched_parser:
                raise NoMatchingParser(NoMatchResult(indexed_string=indexed_string))
        return results
