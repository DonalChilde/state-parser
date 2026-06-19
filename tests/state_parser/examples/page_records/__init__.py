"""Page-records example package for state parser demonstrations."""

from .example_page import EXAMPLE_PAGE_TEXT, ExamplePageProvider, get_example_provider
from .example_parsers import PageRecordsParseStrategy, initial_context
from .test_example_parser import run_example

__all__ = [
    "EXAMPLE_PAGE_TEXT",
    "ExamplePageProvider",
    "PageRecordsParseStrategy",
    "get_example_provider",
    "initial_context",
    "run_example",
]
