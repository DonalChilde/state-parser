"""Base classes and protocols for the state parser."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

type ParseContext = dict[str, Any]


class StateParserError(Exception):
    """An exception class for state parser errors."""

    def __init__(self, *args: Any):
        super().__init__(*args)


class ParserStopError(StateParserError):
    """An exception class for parse failures that should stop the parse process."""

    def __init__(self, parse_failure: ParseFailureStop):
        self.parse_failure = parse_failure
        super().__init__(parse_failure.error_message)


class NoMatchingParser(StateParserError):
    """An exception class for no matching parser."""

    def __init__(self, parse_result: NoMatchResult):
        self.parse_result = parse_result
        super().__init__("No matching parser found for the parse result.")


@dataclass
class IndexedStringBase:
    """A base class for an indexed string, which consists of an index and a string.

    The index can be of any type, as it is not specified in the base class. Specific
    implementations can extend this class to specify the type of the index as needed.
    """

    index: Any
    string: str


@dataclass
class IndexedStringInt(IndexedStringBase):
    """A class for an indexed string, which consists of an index and a string."""

    index: int


@dataclass
class ParseResultBase:
    """A base class for a parse result, which consists of an index and a value.

    Specific parsers can extend this class to include additional fields as needed.
    """

    indexed_string: IndexedStringBase


@dataclass
class ParseFailureStop(ParseResultBase):
    """A class for a parse failure, which consists of an index and a value.

    Signals that a parse attempt has failed, and the parse process should stop.
    Includes an error message for debugging purposes.
    """

    context: ParseContext
    error_message: str


@dataclass
class NoMatchResult(ParseResultBase):
    """A class for a parse result that did not match a parser.

    Used by a parser to signal that it did not match the input, and that the next
    expected parser should be tried.

    Also used by the state parser to signal that no expected parser matched the input,
    and that a NoMatchingParser error should be raised.
    """

    pass


class ParserProtocol(Protocol):
    def parse(
        self, indexed_string: IndexedStringBase, ctx: ParseContext
    ) -> tuple[ParseResultBase, ParseContext]: ...


class ParseStrategyProtocol(Protocol):
    """A protocol for a parse strategy.

    The expected method should return a tuple of parsers that are expected to be used
    next, based on the parse history and the current context.
    """

    def expected(
        self, parse_history: list[ParseResultBase], ctx: ParseContext
    ) -> tuple[ParserProtocol, ...]:
        """Returns a tuple of parsers that are expected to be used next."""
        ...


class IndexedStringProviderProtocol(Protocol):
    """A protocol for an indexed string provider."""

    def indexed_string(self) -> Iterable[IndexedStringBase]: ...


class StateParser:
    def __init__(
        self,
        parse_strategy: ParseStrategyProtocol,
        parser_lookback: int = 5,
    ):
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
        """Runs the state parser on the provided input.

        Args:
            indexed_string_provider: An object that provides an iterable of indexed strings.
            ctx: A dictionary representing the current parse context.

        Returns:
            A list of parse results.
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
