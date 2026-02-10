"""md2wechat - WeChat Official Account Article Publisher

This package provides tools to publish Markdown and HTML articles
to WeChat Official Account drafts via the official WeChat API.
"""

__version__ = "1.0.0"
__author__ = "zkkython"

# Core components
from .config import Config
from .wechat_client import WeChatAPIClient
from .parsers import (
    ContentParser,
    MarkdownParser,
    HTMLParser,
    ParseResult,
    ParserRegistry,
)
from .image_processor import ImageProcessor
from .publisher import ArticlePublisher

# CLI entry point
from .__main__ import main

__all__ = [
    # Core classes
    "Config",
    "WeChatAPIClient",
    "ContentParser",
    "MarkdownParser",
    "HTMLParser",
    "ParseResult",
    "ParserRegistry",
    "ImageProcessor",
    "ArticlePublisher",
    # CLI
    "main",
]
