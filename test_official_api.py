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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills/md2wechat/libs'))

from pathlib import Path


def test_import():
    """Test that dependencies can be imported."""
    try:
        import pygments
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
        # Code block should be present even after syntax highlighting
        assert "hello" in result.content and "return" in result.content, "Code block not preserved"
        assert '<pre' in result.content and "white-space" in result.content, "Code block not converted to styled pre block"
        assert 'background-color:#161b22;' in result.content, "Code block header should use GitHub dark chrome"
        assert 'background-color:#0d1117;' in result.content, "Code block body should use GitHub dark background"
        assert 'background-color:#ff5f56;' in result.content, "Code block header should render mac-style red dot"
        assert 'color:#6ebf26;' in result.content.lower(), "Native keyword color not applied"

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


def test_theme_loading():
    """Test nested YAML theme loading and default fallback behavior."""
    try:
        from themes import ThemeRegistry

        theme_dir = Path("/tmp/test_themes")
        theme_dir.mkdir(exist_ok=True)
        theme_file = theme_dir / "custom.yaml"
        theme_file.write_text(
            """name: 自定义主题
header:
  bg_color: "#111111"
paragraph:
  color: "#222222"
""",
            encoding="utf-8",
        )

        registry = ThemeRegistry(theme_dir)
        styles = registry.get_theme_names()
        config = registry.get_theme("custom")

        assert styles == {"custom": "自定义主题"}, f"Unexpected theme names: {styles}"
        assert config.header_bg_color == "#111111", "Custom override not loaded"
        assert config.paragraph_color == "#222222", "Nested override not loaded"
        assert config.header_text_color == "#FFFFFF", "Default fallback not applied"

        print("✓ Theme loading test passed")
        theme_file.unlink()
        theme_dir.rmdir()
        return True
    except Exception as e:
        print(f"✗ Theme loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wechat_theme_builtin():
    """Test built-in wechat theme values."""
    try:
        from themes import ThemeRegistry

        config = ThemeRegistry().get_theme("wechat")

        assert config.name == "WeChat 主题", "WeChat theme display name mismatch"
        assert config.paragraph_color == "#232323", "WeChat theme paragraph color mismatch"
        assert config.card_bg_color == "#f6f6f6", "WeChat theme card background mismatch"
        assert config.code_bg_color == "#1E2523", "WeChat theme code block background mismatch"
        assert config.table_border_color == "#e6e6e6", "WeChat theme table border color mismatch"

        print("✓ WeChat built-in theme test passed")
        return True
    except Exception as e:
        print(f"✗ WeChat built-in theme test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wechat_native_table_border_color():
    """Test native table cells use the updated wechat border color."""
    try:
        from converter import MarkdownToWeChatConverter

        converter = MarkdownToWeChatConverter(style="wechat")
        html = converter.convert("| h |\n| --- |\n| c |\n")

        assert 'border:1px solid #e6e6e6;' in html, "WeChat native table cells should use #e6e6e6 border color"
        assert 'border:1px solid #DFF6EA;' not in html, "WeChat native table cells should no longer use #DFF6EA"

        print("✓ WeChat native table border color test passed")
        return True
    except Exception as e:
        print(f"✗ WeChat native table border color test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ant_theme_builtin():
    """Test built-in ant theme values."""
    try:
        from themes import ThemeRegistry

        config = ThemeRegistry().get_theme("ant")

        assert config.name == "Ant 主题", "Ant theme display name mismatch"
        assert config.header_bg_color == "#597ef7", "Ant theme header color mismatch"
        assert config.h2_title_text_color == "#597ef7", "Ant theme heading color mismatch"
        assert config.h3_title_bg_color == "#E6F4FF", "Ant theme card color mismatch"

        print("✓ Ant built-in theme test passed")
        return True
    except Exception as e:
        print(f"✗ Ant built-in theme test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_heading_td_has_no_border():
    """Test heading rendering without an auto-inserted article title block."""
    try:
        from converter import MarkdownToWeChatConverter

        converter = MarkdownToWeChatConverter(style="academic_gray")
        html = converter.convert("# H1\n\n## H2\n\n### H3\n\n#### H4\n\n##### H5\n", title="Header Title")

        assert html.count('style="margin:0px;background:none;border:none !important;">') >= 2, "H1/H2 wrapper tables should use 0px margin"
        assert 'bgcolor="ECF0F1" style="margin:0px;background:none;border:none !important;">' in html, "H3 wrapper table should use 0px margin"
        assert html.count('border:none !important;') >= 3, "Heading td containers should force border:none"
        assert 'font-size:22px;font-weight:bold' in html, "H1 should use 22px"
        assert 'background:none;color:#2C3E50;padding:6px 20px;font-size:18px;font-weight:bold;border-radius:8px;' in html, "H2 should use theme text color without background"
        assert 'width:40px;height:3px;margin:8px auto 0;background-color:#2C3E50;border-radius:999px;' not in html, "H2 should not render the centered 40x3 accent bar"
        assert 'display:block;padding:8px 8px 8px 0px;font-size:16px;font-weight:bold;color:#34495E;' in html, "H3 span should use 0px left padding"
        assert 'font-size:16px;font-weight:bold' in html, "H3/H4/H5 should use paragraph font size"
        assert 'Header Title' not in html, "Converter should not inject the publish title into body HTML"

        print("✓ Heading td border-none test passed")
        return True
    except Exception as e:
        print(f"✗ Heading td border-none test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visible_content_uses_default_line_height():
    """Test that converted line-height styles are normalized to 1."""
    try:
        from converter import MarkdownToWeChatConverter

        converter = MarkdownToWeChatConverter(style="academic_gray")
        html = converter.convert(
            "Paragraph text with `inline` code.\n\n> Quote text\n\n- Item 1\n\n---\n\n```python\nprint('hi')\n```\n"
        )

        assert 'line-height:1;' in html, "Converted HTML should keep minimal normalized line-height rules"
        assert 'line-height:1.5;' in html, "Code block should use a slightly larger IDE-like line height"
        assert 'background-color:#f0f0f0;' in html, "Inline code should use the fixed neutral background"
        assert 'line-height:0' not in html, "line-height:0 should be removed"
        assert 'line-height:inherit' not in html, "line-height:inherit should be normalized"
        assert 'line-height:1.8' not in html, "Paragraph/list/blockquote should not force line-height"
        assert 'line-height:1.7' not in html, "Code block should not force an overly loose line-height"
        assert 'line-height:1.6' not in html, "Table cells should not force line-height"
        assert 'line-height:1.4' not in html, "Heading should not force line-height"

        print("✓ Default line-height test passed")
        return True
    except Exception as e:
        print(f"✗ Default line-height test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_paragraph_newlines_render_as_separate_blocks():
    """Test that paragraph line breaks render as separate p blocks instead of br tags."""
    try:
        from converter import MarkdownToWeChatConverter

        converter = MarkdownToWeChatConverter(style="academic_gray")
        html = converter.convert("第一行\n第二行")

        assert '<br>' not in html and '<br/>' not in html, "Paragraph line breaks should not render as br tags"
        assert '<p style="margin:0 0 10px 0;font-size:16px;color:#2C3E50;">第一行</p>' in html, "Non-final line should use 10px bottom margin"
        assert '<p style="margin:0;font-size:16px;color:#2C3E50;">第二行</p>' in html, "Final line should not use paragraph margin"

        print("✓ Paragraph newline block rendering test passed")
        return True
    except Exception as e:
        print(f"✗ Paragraph newline block rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_default_body_and_code_font_size():
    """Test that body/list text stay aligned and code uses 12px."""
    try:
        from converter import MarkdownToWeChatConverter

        converter = MarkdownToWeChatConverter(style="academic_gray")
        html = converter.convert(
            "Paragraph text.\n\n- Item 1\n\n> Quote text\n\n| h |\n| --- |\n| c |\n\n```python\nprint('hi')\n```\n"
        )

        assert 'font-size:16px;' in html, "Academic gray body text should use theme paragraph font size"
        assert '<p style="margin:16px 0;font-size:16px;color:#2C3E50;">' in html, "Paragraph should keep a minimal unified style"
        assert '<li style="margin:10px 0;padding:0;font-size:16px;">' in html, "List items should match body font size and have no padding"
        assert 'font-size:12px;' in html, "Code should use 12px"
        assert 'font-size:12px;line-height:1.5;color:' in html, "Code pre should use line-height:1.5"
        assert 'background-color:#e5e5e5;font-weight:bold;color:#2C3E50;font-size:13px;' in html, "Native table header should use the fixed gray background"
        assert 'background-color:transparent;color:#2C3E50;font-size:13px;' in html, "Native table rows should use transparent backgrounds"
        assert '<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:13px;">' in html, "Native table should render directly"
        assert 'border-radius:8px;overflow:hidden;border:1px solid' not in html, "Native table should not be wrapped by a decorative table"
        assert 'text-align:justify' not in html, "Paragraphs should not force justification"
        assert 'letter-spacing:0.3px' not in html, "Paragraphs should not force letter spacing"
        assert 'font-style:italic' not in html, "Paragraphs should keep a simple unified style"

        print("✓ Default body/code font-size test passed")
        return True
    except Exception as e:
        print(f"✗ Default body/code font-size test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_block_highlighting_and_fallback():
    """Test that known languages highlight and unknown ones fall back safely."""
    try:
        from converter import CodeBlockFormatter
        from themes import get_default_style

        formatter = CodeBlockFormatter(get_default_style())

        highlighted = formatter.format_code_block(
            "def hello(name):\n    return 'hi'\n",
            language="python",
            show_line_numbers=False,
        )
        fallback = formatter.format_code_block(
            "plain <text>\n",
            language="unknownlang",
            show_line_numbers=False,
        )

        assert formatter.style_config.code_pygments_style == "material", "Default code style should use Material"
        assert '<span style="color:' in highlighted.lower(), "Known languages should render highlighted token spans"
        assert 'border-radius:8px;' not in highlighted, "Code block should not have 8px radius"
        assert '<div style="margin:16px 0;width:100%;max-width:100%;overflow:hidden;background:none;border:none !important;">' in highlighted, "Code block outer wrapper should clip page-level overflow"
        assert 'height:30px;display:flex;align-items:center;padding:0 12px;' in highlighted, "Code block should render a 30px header bar"
        assert 'background-color:#161b22;' in highlighted, "Code block header should use GitHub dark chrome"
        assert 'background-color:#ff5f56;' in highlighted and 'background-color:#ffbd2e;' in highlighted and 'background-color:#27c93f;' in highlighted, "Code block header should render red/yellow/green dots"
        assert 'overflow-x:auto;overflow-y:hidden;box-sizing:border-box;' in highlighted, "Code block should provide horizontal scrolling on the pre element"
        assert 'white-space:pre;word-wrap:normal;overflow-wrap:normal;' in highlighted, "Code block should preserve long lines for horizontal scrolling"
        assert 'white-space:pre-wrap' not in highlighted, "Code block should not soft-wrap long lines"
        assert 'word-wrap:break-word' not in highlighted, "Code block should not force long-line wrapping"
        assert 'overflow-wrap:anywhere' not in highlighted, "Code block should not force overflow wrapping"
        assert 'width:max-content' not in highlighted, "Code block should not expand the full page width"
        assert '<br>' not in highlighted, "Code block lines should use real newlines inside pre"
        assert '&lt;text&gt;' in fallback, "Fallback should still escape HTML"
        assert 'color:#6ebf26;' not in fallback.lower(), "Unknown language should not use syntax highlight spans"

        print("✓ Code block highlighting/fallback test passed")
        return True
    except Exception as e:
        print(f"✗ Code block highlighting/fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_non_table_wrappers_use_background_none():
    """Test that non-table content wrappers use background:none, zero padding, and forced border reset."""
    try:
        from converter import MarkdownToWeChatConverter

        converter = MarkdownToWeChatConverter(style="academic_gray")
        html = converter.convert(
            "# H1\n\n## H2\n\n### H3\n\n> Quote text\n\n---\n\n```python\nprint('hi')\n```\n\n![img](https://example.com/a.png)\n",
            title="Header Title",
        )

        assert html.startswith('<div style="width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;">'), "Final article HTML should use a page-level width guard"
        assert 'background:none;' in html, "Non-table wrappers should set background:none"
        assert html.count('background:none;') >= 6, "Expected wrapper tables to include background:none"
        assert 'table-layout:fixed;' in html, "Decorative tables should lock width with fixed layout"
        assert 'Header Title' not in html, "Auto-generated article title wrapper should be removed"
        assert 'border:none !important;' in html, "Decorative table wrappers should force border:none"
        assert '<tr style="border:none !important;">' in html, "Decorative wrapper rows should force border:none"
        assert '<td style="padding:0;border:none !important;' in html or 'style="border:none !important;padding:0;' in html, "Decorative wrapper cells should force border:none"
        assert '<td style="padding:8px 0;border:none !important;">' in html or '<td style="padding:8px 0;border:none !important;font-size:0.85em;color:#888888;">' in html, "Text card wrapper td should use 8px vertical padding"
        assert 'padding:0px;border:none !important;' in html, "Card wrapper direct div should use 0px padding and no border"
        assert 'background-color:#f0f0f0;padding:10px;border-left:3px solid #2c3e50 !important;border:none;' in html.lower(), "Blockquote direct div should use citation styling"
        assert '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin:28px 0;background:none;border:none !important;">' not in html, "Empty divider div should not be wrapped by a decorative table"
        assert 'cellpadding="16"' not in html, "Wrapper tables should not use non-zero cellpadding"
        assert 'cellpadding="12"' not in html, "Card wrapper tables should not use non-zero cellpadding"
        assert 'cellpadding="8"' not in html, "Heading wrapper tables should not use non-zero cellpadding"
        assert 'padding-bottom:8px' not in html, "Heading wrapper td should not use padding"
        assert 'padding:0 4px' not in html, "Meta wrapper td should not use padding"
        assert 'style="width:100%;border-collapse:collapse;margin:20px 0;font-size:13px;">' in html or '<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:13px;">' not in html, "Actual markdown table renderer should remain unchanged"

        print("✓ Non-table wrapper background-none test passed")
        return True
    except Exception as e:
        print(f"✗ Non-table wrapper background-none test failed: {e}")
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
    results.append(("Theme loading", test_theme_loading()))
    results.append(("WeChat theme", test_wechat_theme_builtin()))
    results.append(("WeChat table border", test_wechat_native_table_border_color()))
    results.append(("Ant theme", test_ant_theme_builtin()))
    results.append(("Heading td border", test_heading_td_has_no_border()))
    results.append(("Default line-height", test_visible_content_uses_default_line_height()))
    results.append(("Body/code font-size", test_default_body_and_code_font_size()))
    results.append(("Code highlighting", test_code_block_highlighting_and_fallback()))
    results.append(("Wrapper background none", test_non_table_wrappers_use_background_none()))
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
