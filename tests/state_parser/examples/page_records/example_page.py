"""Example input page and provider for the page_records parser example."""

from collections.abc import Iterable

from state_parser.state_parser import (
    IndexedStringBase,
    IndexedStringInt,
    IndexedStringProviderProtocol,
)

EXAMPLE_PAGE_TEXT = """PAGE REPORT 2026-06-01

RECORD: A-100
NAME: Alice Johnson
TAG: onboarding
TAG: priority
VALUE: score=87
VALUE: tier=gold

RECORD: B-220
NAME: Bob Smith
TAG: followup
VALUE: score=72
VALUE: tier=silver
VALUE: risk=low

RECORD: C-330
NAME: Casey Nguyen
TAG: escalation
TAG: partner
VALUE: score=91

END REPORT total_records=3
"""


class ExamplePageProvider(IndexedStringProviderProtocol):
    """Yield indexed lines from the sample page text.

    The provider preserves blank lines because they carry structure in this
    example format.
    """

    def __init__(self, text: str = EXAMPLE_PAGE_TEXT):
        self._text = text

    def indexed_string(self) -> Iterable[IndexedStringBase]:
        for i, line in enumerate(self._text.splitlines(), start=1):
            yield IndexedStringInt(index=i, string=line)


def get_example_provider() -> ExamplePageProvider:
    """Return a provider for the built-in example page text."""

    return ExamplePageProvider()
