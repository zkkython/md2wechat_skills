"""Content parsers for different input formats."""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class ContentParser(ABC):
    """Abstract base class for content parsers."""

    @abstractmethod
    def parse(self, filepath: str) -> dict:
        """Parse file and return structured content."""
        pass

    @abstractmethod
    def supports(self, filepath: str) -> bool:
        """Check if this parser supports the given file."""
        pass


class ParseResult:
    """Result of parsing a content file."""

    def __init__(
        self,
        title: str,
        content: str,
        cover_image: Optional[str] = None,
        summary: Optional[str] = None,
        base_path: Optional[Path] = None
    ):
        self.title = title
        self.content = content
        self.cover_image = cover_image
        self.summary = summary
        self.base_path = base_path or Path.cwd()


class MarkdownParser(ContentParser):
    """Parser for Markdown files."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith('.md')

    def parse(self, filepath: str) -> ParseResult:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")

        # Remove backslash escapes
        content = self._unescape(content)

        # Extract title from filename
        title = self._extract_title_from_filename(path)

        # Extract cover image
        cover_image = self._extract_first_image(content, path.parent)

        # Extract summary
        summary = self._extract_summary(content)

        # Convert to HTML
        html_content = self._convert_to_html(content)

        return ParseResult(
            title=title,
            content=html_content,
            cover_image=cover_image,
            summary=summary,
            base_path=path.parent
        )

    def _unescape(self, content: str) -> str:
        """Remove backslash escapes from content."""
        replacements = [
            ("\\_", "_"),
            ("\\*", "*"),
            ("\\[", "["),
            ("\\]", "]"),
            ("\\(", "("),
            ("\\)", ")"),
            ("\\`", "`"),
            ("\\\\", "\\"),
        ]
        for old, new in replacements:
            content = content.replace(old, new)
        return content

    def _extract_title_from_filename(self, path: Path) -> str:
        """Extract title from filename."""
        title = path.stem.replace("_", " ").replace("-", " ").title()
        return title[:64]

    def _extract_first_image(self, content: str, base_path: Path) -> Optional[str]:
        """Extract first image from markdown content."""
        pattern = re.compile(r"!\[[^\]]*\]\(([^)]*)\)")
        match = pattern.search(content)
        if match:
            src = match.group(1)
            if src and not src.startswith(("http://", "https://")):
                img_path = base_path / src
                if img_path.exists():
                    return str(img_path.absolute())
            return src
        return None

    def _extract_summary(self, content: str) -> Optional[str]:
        """Extract summary from first paragraph."""
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "!", ">", "-", "*", "`")):
                return stripped[:120]
        return None

    def _convert_to_html(self, markdown: str) -> str:
        """Convert markdown to WeChat-compatible HTML."""
        html = markdown

        # Process images first
        html = self._process_images(html)

        # Process code blocks
        html = self._process_code_blocks(html)

        # Process inline code
        html = self._process_inline_code(html)

        # Process headers
        html = self._process_headers(html)

        # Process formatting
        html = self._process_formatting(html)

        # Process paragraphs
        html = self._process_paragraphs(html)

        return html

    def _process_images(self, html: str) -> str:
        """Convert markdown images to HTML."""
        return re.sub(
            r"!\[([^\]]*)\]\(([^)]*)\)",
            r'<img src="\2" alt="\1" />',
            html
        )

    def _process_code_blocks(self, html: str) -> str:
        """Convert markdown code blocks to HTML tables."""
        def convert_block(match):
            code = match.group(1)
            code = code.replace("&", "&amp;")
            code = code.replace("<", "&lt;")
            code = code.replace(">", "&gt;")

            # Preserve indentation with &nbsp;
            lines = code.split('\n')
            formatted_lines = []
            for line in lines:
                leading_spaces = len(line) - len(line.lstrip(' '))
                if leading_spaces > 0:
                    line = '&nbsp;' * leading_spaces + line[leading_spaces:]
                line = line.replace('  ', '&nbsp;&nbsp;')
                formatted_lines.append(line)
            code_content = '<br>'.join(formatted_lines)

            return (
                f'<table width="100%" cellpadding="12" cellspacing="0" border="0" '
                f'bgcolor="#f8f9fa" style="border:1px solid #e9ecef;border-radius:6px;margin:12px 0;">'
                f'<tr><td style="font-family:SF Mono,Monaco,Courier New,monospace;'
                f'font-size:13px;line-height:1.6;color:#212529;">{code_content}</td></tr></table>'
            )

        return re.sub(r"```[\w]*\n(.*?)```", convert_block, html, flags=re.DOTALL)

    def _process_inline_code(self, html: str) -> str:
        """Convert inline code to HTML."""
        # Protect code blocks first
        code_blocks = []
        pattern = re.compile(r'(<table width="100%"[\s\S]*?</table>)')

        def extract_block(match):
            code_blocks.append(match.group(1))
            return f"\x00CODEBLOCK{len(code_blocks)-1}\x00"

        html = pattern.sub(extract_block, html)

        # Process inline code
        def convert_inline(match):
            code = match.group(1)
            code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return (
                f'<code style="background-color:#f8f9fa;border:1px solid #e9ecef;'
                f'border-radius:3px;padding:2px 6px;font-family:SF Mono,Monaco,Courier New,monospace;'
                f'font-size:13px;color:#212529;">{code}</code>'
            )

        parts = re.split(r'(\x00CODEBLOCK\d+\x00)', html)
        for i, part in enumerate(parts):
            if not part.startswith('\x00CODEBLOCK'):
                parts[i] = re.sub(r"`([^`]+)`", convert_inline, part)

        html = "".join(parts)

        # Restore code blocks
        for i, block in enumerate(code_blocks):
            html = html.replace(f"\x00CODEBLOCK{i}\x00", block)

        return html

    def _process_headers(self, html: str) -> str:
        """Convert markdown headers to styled HTML."""
        styles = {
            'h1': 'font-size:20px;font-weight:bold;margin:20px 0 10px 0;padding-bottom:8px;border-bottom:2px solid #07c160;color:#333;',
            'h2': 'font-size:18px;font-weight:bold;margin:18px 0 8px 0;padding-bottom:6px;border-bottom:1px solid #ddd;color:#444;',
            'h3': 'font-size:16px;font-weight:bold;margin:16px 0 6px 0;color:#555;',
            'h4': 'font-size:15px;font-weight:bold;margin:14px 0 4px 0;color:#666;',
            'h5': 'font-size:14px;font-weight:bold;margin:12px 0 4px 0;color:#777;',
            'h6': 'font-size:14px;font-weight:normal;margin:10px 0 4px 0;color:#888;font-style:italic;',
        }

        for i, (tag, style) in enumerate(styles.items(), 1):
            prefix = '#' * i
            html = re.sub(
                rf"^{prefix} (.+)$",
                rf'<{tag} style="{style}">\1</{tag}>',
                html,
                flags=re.MULTILINE
            )

        return html

    def _process_formatting(self, html: str) -> str:
        """Process bold, italic, links, lists, etc."""
        # Bold
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # Italic
        html = re.sub(r"(?<![\"])\*([^*]+)\*(?![<])", r"<em>\1</em>", html)

        # Links
        html = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

        # Blockquotes
        html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

        # Lists
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"((?:<li>.*?</li>\n?)+)", r"<ul>\1</ul>", html)

        return html

    def _process_paragraphs(self, html: str) -> str:
        """Wrap text in paragraphs."""
        header_pattern = re.compile(r'^<h[1-6]\b')
        block_pattern = re.compile(r'^<(blockquote|ul|ol|img|p|table)\b')
        placeholder_pattern = re.compile(r'\x00CODEBLOCK\d+\x00')

        parts = html.split("\n\n")
        processed = []

        for part in parts:
            part = part.strip()
            if not part:
                continue
            if (placeholder_pattern.match(part) or
                header_pattern.match(part) or
                block_pattern.match(part)):
                processed.append(part)
            else:
                part = part.replace("\n", "<br>")
                processed.append(f"<p>{part}</p>")

        result = "".join(processed)

        # Cleanup
        result = re.sub(r"<p>\s*<p", "<p", result)
        result = re.sub(r"</p>\s*</p>", "</p>", result)
        result = re.sub(r"<p>\s*</p>", "", result)

        return result


class HTMLParser(ContentParser):
    """Parser for HTML files."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith('.html')

    def parse(self, filepath: str) -> ParseResult:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")

        # Extract title
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", content, re.IGNORECASE)
            title = h1_match.group(1).strip() if h1_match else path.stem

        title = title[:64]

        # Extract body
        body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.IGNORECASE | re.DOTALL)
        if body_match:
            html_content = body_match.group(1).strip()
        else:
            html_content = re.sub(r"<html[^>]*>|</html>|<head[\s\S]*?</head>|<!DOCTYPE[^>]*>",
                                  "", content, flags=re.IGNORECASE).strip()

        # Extract cover image
        cover_image = None
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if img_match:
            src = img_match.group(1)
            if src and not src.startswith(("http://", "https://", "data:")):
                img_path = path.parent / src
                if img_path.exists():
                    cover_image = str(img_path.absolute())
            else:
                cover_image = src

        # Extract summary
        summary = None
        p_match = re.search(r"<p[^>]*>([^<]+)", html_content, re.IGNORECASE)
        if p_match:
            summary = re.sub(r"<[^>]+>", "", p_match.group(1)).strip()[:120]

        return ParseResult(
            title=title,
            content=html_content,
            cover_image=cover_image,
            summary=summary,
            base_path=path.parent
        )


class ParserRegistry:
    """Registry of content parsers."""

    def __init__(self):
        self._parsers: list[ContentParser] = [
            MarkdownParser(),
            HTMLParser(),
        ]

    def get_parser(self, filepath: str) -> ContentParser:
        """Get appropriate parser for file."""
        for parser in self._parsers:
            if parser.supports(filepath):
                return parser
        raise ValueError(f"No parser available for file: {filepath}")

    def register(self, parser: ContentParser) -> None:
        """Register a new parser."""
        self._parsers.append(parser)
