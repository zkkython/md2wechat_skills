"""Content parsers for different input formats."""

import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

# Add libs directory to path for MD2WeChat
_lib_path = Path(__file__).parent.parent / "libs"
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

from converter import MarkdownToWeChatConverter, STYLES


class ContentParser(ABC):
    """Abstract base class for content parsers."""

    @abstractmethod
    def parse(self, filepath: str, style: str = "academic_gray", title: Optional[str] = None) -> "ParseResult":
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
    """Parser for Markdown files using MD2WeChat converter."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith('.md')

    def parse(self, filepath: str, style: str = "academic_gray", title: Optional[str] = None) -> ParseResult:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")

        # Extract cover image before conversion
        cover_image = self._extract_first_image(content, path.parent)

        # Extract summary from first paragraph
        summary = self._extract_summary(content)

        # Use MD2WeChat converter
        converter = MarkdownToWeChatConverter(style=style, base_dir=str(path.parent))

        # Extract title from front matter or filename (if external title not provided)
        if title is None:
            title = self._extract_title(content, path)

        # Convert to HTML
        html_content = converter.convert(content, title=title)

        return ParseResult(
            title=title,
            content=html_content,
            cover_image=cover_image,
            summary=summary,
            base_path=path.parent
        )

    def _extract_title(self, content: str, path: Path) -> str:
        """Extract title from front matter, H1 heading, or filename."""
        # Check front matter for title
        if content.startswith("---"):
            lines = content.split("\n")
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    break
                if line.strip().startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if title:
                        return title[:64]

        # Check for H1 heading (# Title)
        lines = content.split("\n")
        in_front_matter = False
        for line in lines:
            stripped = line.strip()
            # Skip front matter
            if stripped == "---":
                in_front_matter = not in_front_matter
                continue
            if in_front_matter:
                continue
            # Check for H1
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                if title:
                    return title[:64]
            # Stop at first non-empty, non-comment line if not H1
            if stripped and not stripped.startswith("#"):
                break

        # Fall back to filename
        return path.stem.replace("_", " ").replace("-", " ").title()[:64]

    def _extract_first_image(self, content: str, base_path: Path) -> Optional[str]:
        """Extract first image from markdown content."""
        pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
        match = pattern.search(content)
        if match:
            src = match.group(1).split()[0]  # Get URL part only, not title
            if src and not src.startswith(("http://", "https://")):
                img_path = base_path / src
                if img_path.exists():
                    return str(img_path.absolute())
            return src
        return None

    def _extract_summary(self, content: str) -> Optional[str]:
        """Extract summary from first paragraph."""
        in_front_matter = False
        for line in content.split("\n"):
            stripped = line.strip()

            # Skip front matter
            if stripped == "---":
                in_front_matter = not in_front_matter
                continue
            if in_front_matter:
                continue

            # Skip empty lines and special markdown
            if stripped and not stripped.startswith(("#", "!", ">", "-", "*", "`", "|")):
                # Remove markdown formatting
                text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', stripped)  # Links
                text = re.sub(r'[*_`]', '', text)  # Bold, italic, code
                return text[:120]
        return None


class HTMLParser(ContentParser):
    """Parser for HTML files."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith('.html')

    def parse(self, filepath: str, style: str = "academic_gray", title: Optional[str] = None) -> ParseResult:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")

        # Extract title (use external title if provided)
        if title is None:
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


def get_available_styles() -> dict[str, str]:
    """Get available style names and descriptions."""
    return {name: config.name for name, config in STYLES.items()}
