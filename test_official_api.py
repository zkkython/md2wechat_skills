#!/usr/bin/env python3
"""
Test script for md2wechat publisher (refactored version)

Usage:
    python test_official_api.py
"""

import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills/md2wechat/scripts'))

from pathlib import Path


def test_import():
    """Test that dependencies can be imported."""
    try:
        from wechatpy import WeChatClient
        from parsers import MarkdownParser, HTMLParser
        from publisher import ArticlePublisher
        from config import Config
        from image_processor import ImageProcessor
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False


def test_markdown_parsing():
    """Test markdown parsing function."""
    try:
        from parsers import MarkdownParser

        # Create test markdown file
        test_md = """# Test Article

This is a test article for WeChat publishing.

## Section 1

Some **bold** and *italic* text.

![cover](https://example.com/image.jpg)

- Item 1
- Item 2

> A quote block

```python
def hello():
    return 42
```
"""

        test_file = Path("/tmp/test_article.md")
        test_file.write_text(test_md, encoding="utf-8")

        parser = MarkdownParser()
        result = parser.parse(str(test_file))

        assert result.title == "Test Article", f"Expected 'Test Article', got '{result.title}'"
        assert "Section 1" in result.content, "Section 1 not found in content"
        assert "<strong>bold</strong>" in result.content, "Bold formatting not converted"
        assert result.cover_image == "https://example.com/image.jpg", "Cover image not extracted"
        assert "def hello():" in result.content, "Code block not preserved"
        assert "<table" in result.content, "Code block not converted to table"

        print("✓ Markdown parsing test passed")
        test_file.unlink()
        return True
    except Exception as e:
        print(f"✗ Markdown parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_parsing():
    """Test HTML parsing function."""
    try:
        from parsers import HTMLParser

        test_html = """<!DOCTYPE html>
<html>
<head><title>HTML Test Article</title></head>
<body>
<h1>Main Title</h1>
<p>This is the first paragraph.</p>
<img src="cover.jpg" alt="cover">
</body>
</html>"""

        test_file = Path("/tmp/test_article.html")
        test_file.write_text(test_html, encoding="utf-8")

        parser = HTMLParser()
        result = parser.parse(str(test_file))

        assert result.title == "HTML Test Article", f"Expected 'HTML Test Article', got '{result.title}'"
        assert "<h1>Main Title</h1>" in result.content, "Main title not in content"
        # cover_image is None because cover.jpg doesn't exist as a real file
        assert result.cover_image is None, "Cover image should be None for non-existent file"

        print("✓ HTML parsing test passed")
        test_file.unlink()
        return True
    except Exception as e:
        print(f"✗ HTML parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_loading():
    """Test environment variable loading."""
    try:
        from config import Config

        # Create test .env file
        env_file = Path("/tmp/test.env")
        env_file.write_text("WECHAT_APPID=test_appid\nWECHAT_APP_SECRET=test_secret\n")

        # Clear any existing env vars
        os.environ.pop("WECHAT_APPID", None)
        os.environ.pop("WECHAT_APP_SECRET", None)

        config = Config(str(env_file))

        assert config.appid == "test_appid", "APPID not loaded"
        assert config.app_secret == "test_secret", "APP_SECRET not loaded"

        print("✓ Environment loading test passed")
        env_file.unlink()
        return True
    except Exception as e:
        print(f"✗ Environment loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parser_registry():
    """Test parser registry functionality."""
    try:
        from parsers import ParserRegistry, MarkdownParser, HTMLParser

        registry = ParserRegistry()

        # Test markdown file detection
        md_parser = registry.get_parser("/path/to/article.md")
        assert isinstance(md_parser, MarkdownParser), "Should return MarkdownParser for .md file"

        # Test HTML file detection
        html_parser = registry.get_parser("/path/to/article.html")
        assert isinstance(html_parser, HTMLParser), "Should return HTMLParser for .html file"

        print("✓ Parser registry test passed")
        return True
    except Exception as e:
        print(f"✗ Parser registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 50)
    print("Testing md2wechat Publisher (Refactored)")
    print("=" * 50)
    print()

    results = []

    results.append(("Import modules", test_import()))
    results.append(("Environment loading", test_env_loading()))
    results.append(("Parser registry", test_parser_registry()))
    results.append(("Markdown parsing", test_markdown_parsing()))
    results.append(("HTML parsing", test_html_parsing()))

    print()
    print("=" * 50)
    print("Test Results:")
    print("=" * 50)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print()
    print(f"Total: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
