#!/usr/bin/env python3
"""
WeChat Official Account Article Publisher - Refactored Version

Usage:
    python -m skills.md2wechat.scripts publish --markdown /path/to/article.md
    python -m skills.md2wechat.scripts publish --html /path/to/article.html
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from .publisher import ArticlePublisher
except ImportError:
    from publisher import ArticlePublisher


def check_env_file():
    """Check if .env file exists and show helpful message if not."""
    env_paths = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path.home() / ".md2wechat" / ".env"
    ]

    for env_path in env_paths:
        if env_path.exists():
            return True

    if os.environ.get("WECHAT_APPID") and os.environ.get("WECHAT_APP_SECRET"):
        return True

    return False


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

        # Check for credentials
        if not check_env_file():
            print("=" * 60, file=sys.stderr)
            print("警告：未找到 .env 文件或环境变量", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print("\n请创建 .env 文件并添加微信凭证：", file=sys.stderr)
            print("  echo 'WECHAT_APPID=your_appid_here' > .env", file=sys.stderr)
            print("  echo 'WECHAT_APP_SECRET=your_secret_here' >> .env", file=sys.stderr)
            print("\n或设置环境变量：", file=sys.stderr)
            print("  export WECHAT_APPID=your_appid_here", file=sys.stderr)
            print("  export WECHAT_APP_SECRET=your_secret_here", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print("\n")

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
            return 0 if result.get("success") else 1
        except Exception as e:
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"错误: {e}", file=sys.stderr)
            print(f"{'=' * 60}", file=sys.stderr)

            error_str = str(e).lower()
            if "appsecret" in error_str or "40001" in error_str:
                print("\n提示：AppSecret 无效", file=sys.stderr)
                print("1. 登录 mp.weixin.qq.com", file=sys.stderr)
                print("2. 设置 → 开发 → 基本配置", file=sys.stderr)
                print("3. 检查 AppSecret 是否正确", file=sys.stderr)
            elif "appid" in error_str or "40013" in error_str:
                print("\n提示：AppID 无效", file=sys.stderr)
                print("1. AppID 应以 wx 开头", file=sys.stderr)
            elif "ip" in error_str or "40164" in error_str:
                print("\n提示：IP 白名单问题", file=sys.stderr)
                print("1. 设置 → 开发 → 基本配置 → IP 白名单", file=sys.stderr)

            return 1


if __name__ == "__main__":
    sys.exit(main())
