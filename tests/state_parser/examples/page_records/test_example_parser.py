"""Executable test example for the page_records state parser."""

import json

from state_parser.state_parser import NoMatchingParser, ParserStopError, StateParser

from .example_page import EXAMPLE_PAGE_TEXT, ExamplePageProvider
from .example_parsers import PageRecordsParseStrategy, initial_context
from .example_results import results_to_dict


def run_example(text: str = EXAMPLE_PAGE_TEXT) -> dict[str, object]:
    """Run the parser example and return structured output data."""

    parser = StateParser(parse_strategy=PageRecordsParseStrategy(), parser_lookback=5)
    provider = ExamplePageProvider(text=text)
    results = parser.run(provider, ctx=initial_context())
    parsed = results_to_dict(results)
    print(json.dumps(parsed, indent=2, sort_keys=True))
    return parsed


def test_page_records_example_end_to_end() -> None:
    """Parse the valid sample page and validate key extracted fields."""

    parsed = run_example()

    assert parsed["report_date"] == "2026-06-01"
    assert parsed["parsed_record_count"] == 3
    assert parsed["footer_total_records"] == 3

    records = parsed["records"]
    assert isinstance(records, list)
    assert records[0]["record_id"] == "A-100"
    assert records[0]["name"] == "Alice Johnson"
    assert len(records[0]["tags"]) == 2
    assert records[1]["values"]["risk"] == "low"


def test_missing_structural_blank_line_raises() -> None:
    """Demonstrate that a structural blank-line omission breaks parsing."""

    malformed = EXAMPLE_PAGE_TEXT.replace("\n\nRECORD: B-220", "\nRECORD: B-220", 1)

    try:
        run_example(malformed)
    except NoMatchingParser, ParserStopError:
        return

    raise AssertionError("Expected a parse failure for malformed input.")
