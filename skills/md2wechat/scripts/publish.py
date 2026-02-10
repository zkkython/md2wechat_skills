#!/usr/bin/env python3
"""
CLI wrapper for md2wechat publisher.
Maintains backward compatibility with the old wechat_official_api.py interface.
"""

import argparse
import json
import sys
from pathlib import Path

# Try relative imports first (for package usage), then absolute (for direct execution)
try:
    from .publisher import ArticlePublisher
except ImportError:
    try:
        from publisher import ArticlePublisher
    except ImportError:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        from publisher import ArticlePublisher


def main():
    parser = argparse.ArgumentParser(
        description="Publish Markdown/HTML articles to WeChat Official Account drafts",
        prog="publish"
    )

    parser.add_argument(
        "--markdown",
        help="Path to markdown file"
    )
    parser.add_argument(
        "--html",
        help="Path to HTML file"
    )
    parser.add_argument(
        "--title",
        help="Article title (max 64 characters)"
    )
    parser.add_argument(
        "--content",
        help="Article content (Markdown or HTML)"
    )
    parser.add_argument(
        "--summary",
        help="Article summary (max 120 characters)"
    )
    parser.add_argument(
        "--cover",
        help="Cover image URL or path"
    )
    parser.add_argument(
        "--author",
        help="Author name"
    )
    parser.add_argument(
        "--type",
        choices=["news", "newspic"],
        default="news",
        help="Article type: news (default) or newspic (小绿书)"
    )

    args = parser.parse_args()

    # Determine input file
    if args.markdown:
        filepath = args.markdown
    elif args.html:
        filepath = args.html
    else:
        print("Error: Either --markdown or --html must be specified", file=sys.stderr)
        sys.exit(1)

    # Publish
    try:
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
        sys.exit(0 if result.get("success") else 1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
