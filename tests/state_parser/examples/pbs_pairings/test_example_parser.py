"""Executable test example for the PBS pairings state parser."""

import json

from state_parser.state_parser import StateParser

from .example_page import EXAMPLE_PAGE_TEXT, ExamplePageProvider
from .example_parsers import PbsPairingsParseStrategy, initial_context
from .example_results import results_to_dict


def run_example(text: str = EXAMPLE_PAGE_TEXT) -> dict[str, object]:
    """Run the parser example and return a structured schedule summary."""

    parser = StateParser(parse_strategy=PbsPairingsParseStrategy(), parser_lookback=8)
    provider = ExamplePageProvider(text=text)
    results = parser.run(provider, ctx=initial_context())
    parsed = results_to_dict(results)
    print(json.dumps(parsed, indent=2, sort_keys=True))
    return parsed


def test_pbs_pairings_example_end_to_end() -> None:
    """Parse the sample schedule page and validate key extracted values."""

    parsed = run_example()

    assert parsed["calendar_range"] == "06/02−07/01"
    assert parsed["sequence_count"] == 4
    assert parsed["sequence_ids"] == ["11273", "11274", "11275", "11276"]

    assert parsed["leg_count"] == 24
    assert parsed["report_time_count"] == 9
    assert parsed["release_count"] == 9
    assert parsed["sequence_total_count"] == 4

    footer = parsed["footer"]
    assert isinstance(footer, dict)
    assert footer["page_number"] == "3924"
    assert footer["effective_date"] == "02JUN2026"


def test_missing_footer_is_detectable_in_output() -> None:
    """Show that removing the footer does not crash, but output reflects absence."""

    no_footer_text = EXAMPLE_PAGE_TEXT.replace("COCKPIT  ISSUED", "XOCKPIT  ISSUED", 1)
    parsed = run_example(no_footer_text)

    assert parsed["footer"] is None
    assert parsed["sequence_count"] == 4
