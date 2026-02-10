#!/usr/bin/env python3
"""
WeChat Official Account Article Publisher - Refactored Version

Usage:
    python -m md2wechat publish --markdown /path/to/article.md
    python -m md2wechat publish --html /path/to/article.html
"""

import argparse
import json
import sys

try:
    from .publisher import ArticlePublisher
except ImportError:
    from publisher import ArticlePublisher


def main():
    parser = argparse.ArgumentParser(
        description="Publish articles to WeChat Official Account drafts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish article")
    publish_parser.add_argument("--title", help="Article title (max 64 chars)")
    publish_parser.add_argument("--summary", help="Article summary (max 120 chars)")
    publish_parser.add_argument("--cover", help="Cover image URL or path")
    publish_parser.add_argument("--author", help="Author name")
    publish_parser.add_argument(
        "--type",
        choices=["news", "newspic"],
        default="news",
        help="Article type"
    )

    # Input source (mutually exclusive)
    input_group = publish_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--markdown", help="Path to markdown file")
    input_group.add_argument("--html", help="Path to HTML file")

    args = parser.parse_args()

    if args.command == "publish":
        filepath = args.markdown or args.html

        publisher = ArticlePublisher()
        result = publisher.publish(
            filepath=filepath,
            title=args.title,
            summary=args.summary,
            cover_image=args.cover,
            author=args.author,
            article_type=args.type
        )

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
