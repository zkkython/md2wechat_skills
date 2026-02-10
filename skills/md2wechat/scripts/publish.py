#!/usr/bin/env python3
"""
CLI wrapper for md2wechat publisher.
Maintains backward compatibility with the old wechat_official_api.py interface.
"""

import argparse
import json
import os
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

    # Check if environment variables are set
    if os.environ.get("WECHAT_APPID") and os.environ.get("WECHAT_APP_SECRET"):
        return True

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Publish Markdown/HTML articles to WeChat Official Account drafts",
        prog="md2wechat"
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

    # Check for credentials before starting
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
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"错误: {e}", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)

        # Provide helpful suggestions based on error
        error_str = str(e).lower()
        if "appsecret" in error_str or "40001" in error_str:
            print("\n提示：AppSecret 无效", file=sys.stderr)
            print("1. 登录 mp.weixin.qq.com", file=sys.stderr)
            print("2. 设置 → 开发 → 基本配置", file=sys.stderr)
            print("3. 检查 AppSecret 是否正确", file=sys.stderr)
            print("4. 如果刚重置过 AppSecret，请更新 .env 文件", file=sys.stderr)
        elif "appid" in error_str or "40013" in error_str:
            print("\n提示：AppID 无效", file=sys.stderr)
            print("1. AppID 应以 wx 开头", file=sys.stderr)
            print("2. 不要混淆 AppID 和 AppSecret", file=sys.stderr)
        elif "ip" in error_str or "40164" in error_str:
            print("\n提示：IP 白名单问题", file=sys.stderr)
            print("1. 登录 mp.weixin.qq.com", file=sys.stderr)
            print("2. 设置 → 开发 → 基本配置 → IP 白名单", file=sys.stderr)
            print("3. 添加当前服务器 IP 地址", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
