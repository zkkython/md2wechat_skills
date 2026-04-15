"""Markdown to WeChat HTML Converter.


"""

import re
import base64
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import html

from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
from pygments.token import Token
from pygments.util import ClassNotFound

try:
    from .themes import (
        StyleConfig,
        get_available_styles,
        get_default_style,
        get_theme_registry,
        load_themes,
    )
except ImportError:
    from themes import (
        StyleConfig,
        get_available_styles,
        get_default_style,
        get_theme_registry,
        load_themes,
    )


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)

def _escape_html_text(text: str) -> str:
    """Escape HTML text-node chars, but keep quotes/apostrophes unchanged."""
    return html.escape(text, quote=False)


def _has_visible_html_content(fragment: str) -> bool:
    """Return True when an HTML fragment contains visible content, not just empty tags/whitespace."""
    text_only = re.sub(r'<[^>]+>', '', fragment)
    text_only = html.unescape(text_only).strip()
    return bool(text_only)

STYLES = load_themes()


class MarkdownParser:
    """Parse markdown front matter and body."""

    def __init__(self, md_content: str):
        self.content = md_content
        self.front_matter = {}
        self.body = ""
        self._parse_front_matter()

    def _parse_front_matter(self):
        """Parse YAML front matter."""
        if not self.content.startswith("---"):
            self.body = self.content
            return

        lines = self.content.split("\n")
        if lines[0].strip() != "---":
            self.body = self.content
            return

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.body = self.content
            return

        # Parse front matter
        fm_lines = lines[1:end_idx]
        i = 0
        while i < len(fm_lines):
            line = fm_lines[i].strip()
            if not line:
                i += 1
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Handle list values
                if not value and i + 1 < len(fm_lines):
                    # Check if next lines are list items
                    list_items = []
                    j = i + 1
                    while j < len(fm_lines) and fm_lines[j].strip().startswith("-"):
                        item = fm_lines[j].strip()[1:].strip()
                        list_items.append(item)
                        j += 1
                    if list_items:
                        self.front_matter[key] = list_items
                        i = j
                        continue

                self.front_matter[key] = value
            i += 1

        self.body = "\n".join(lines[end_idx + 1:])

    def get_front_matter(self, key: str, default: any = None) -> any:
        """Get front matter value by key."""
        return self.front_matter.get(key, default)


class CodeBlockFormatter:
    """Format code blocks for WeChat."""

    DEFAULT_PYGMENTS_STYLE = "material"
    GITHUB_DARK_BG = "#0d1117"
    GITHUB_DARK_HEADER_BG = "#161b22"
    GITHUB_DARK_BORDER = "#30363d"
    GITHUB_DARK_TEXT = "#c9d1d9"
    GITHUB_DARK_LINE_NUMBER = "#8b949e"

    LANGUAGE_ALIASES = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "tsx",
        "sh": "bash",
        "shell": "bash",
        "zsh": "bash",
        "py": "python",
        "yml": "yaml",
    }

    def __init__(self, style_config: Optional[StyleConfig] = None):
        self.style_config = style_config or get_default_style()
        style_name = getattr(self.style_config, "code_pygments_style", self.DEFAULT_PYGMENTS_STYLE)
        self.pygments_style = self._load_pygments_style(style_name)

    def _load_pygments_style(self, style_name: str):
        try:
            return get_style_by_name(style_name or self.DEFAULT_PYGMENTS_STYLE)
        except ClassNotFound:
            return get_style_by_name(self.DEFAULT_PYGMENTS_STYLE)

    def format_code_block(self, code: str, language: str = "", show_line_numbers: bool = True) -> str:
        """Format code block with proper indentation and optional line numbers."""
        lines = code.split('\n')
        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return ""

        # Calculate minimum indentation (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        if min_indent == float('inf'):
            min_indent = 0

        style_name = getattr(self.style_config, "code_pygments_style", self.DEFAULT_PYGMENTS_STYLE)
        if style_name in {"github-dark", "monokai", "native", "material"}:
            bg_color = self.GITHUB_DARK_BG
            border_color = self.GITHUB_DARK_BORDER
            text_color = self.GITHUB_DARK_TEXT
            header_bg_color = self.GITHUB_DARK_HEADER_BG
            line_number_color = self.GITHUB_DARK_LINE_NUMBER
        else:
            bg_color = self.style_config.code_bg_color
            border_color = self.style_config.code_border_color
            text_color = getattr(self.style_config, 'code_text_color', '#212529')
            header_bg_color = border_color
            line_number_color = "#868E96"

        normalized_lines = []
        for line in lines:
            if len(line) >= min_indent:
                normalized_lines.append(line[min_indent:])
            else:
                normalized_lines.append(line)

        highlighted_lines = self._highlight_lines("\n".join(normalized_lines), language)
        if highlighted_lines is None:
            processed_lines = [self._render_plain_line(line) for line in normalized_lines]
        else:
            processed_lines = highlighted_lines

        if show_line_numbers:
            processed_lines = [
                f'<span style="color:{line_number_color};display:inline-block;width:2.5em;text-align:right;margin-right:0.8em;font-size:12px;">{i}</span>{line}'
                for i, line in enumerate(processed_lines, 1)
            ]

        # Keep real newlines so the code block itself can drive horizontal overflow.
        code_text = '\n'.join(processed_lines)

        return (
            f'<div style="margin:16px 0;width:100%;max-width:100%;overflow:hidden;background:none;border:none !important;">'
            f'<div style="height:30px;display:flex;align-items:center;padding:0 12px;box-sizing:border-box;background-color:{header_bg_color};border:none;border-radius:10px 10px 0 0;">'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:#ff5f56;margin-right:8px;"></span>'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:#ffbd2e;margin-right:8px;"></span>'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:#27c93f;"></span>'
            f'</div>'
            f'<pre style="display:block;width:100%;max-width:100%;overflow-x:auto;overflow-y:hidden;box-sizing:border-box;margin:0;padding:16px;background-color:{bg_color};border:none;border-radius:0 0 10px 10px;font-family:SF Mono,Monaco,monospace,Consolas,Courier New;font-size:12px;line-height:1.5;color:{text_color};white-space:pre;word-wrap:normal;overflow-wrap:normal;-webkit-overflow-scrolling:touch;">{code_text}</pre>'
            f'</div>'
        )

    def _highlight_lines(self, code: str, language: str) -> Optional[List[str]]:
        normalized_language = self._normalize_language(language)
        if not normalized_language:
            return None

        try:
            lexer = get_lexer_by_name(normalized_language)
        except ClassNotFound:
            return None

        rendered_lines = [""]
        for token_type, value in lex(code, lexer):
            if not value:
                continue

            color = self._get_token_color(token_type)
            parts = value.split('\n')
            for index, part in enumerate(parts):
                if part:
                    rendered_lines[-1] += self._render_token_part(part, color)
                if index < len(parts) - 1:
                    rendered_lines.append("")

        while rendered_lines and not rendered_lines[-1]:
            rendered_lines.pop()

        return rendered_lines or [""]

    def _normalize_language(self, language: str) -> str:
        if not language:
            return ""
        normalized = language.strip().lower()
        return self.LANGUAGE_ALIASES.get(normalized, normalized)

    def _get_token_color(self, token_type) -> Optional[str]:
        current = token_type
        while current is not None:
            style = self.pygments_style.style_for_token(current)
            color = style.get("color")
            if color:
                return f"#{color}" if not color.startswith("#") else color
            parent = getattr(current, "parent", None)
            if parent == current:
                break
            current = parent
        return None

    def _render_plain_line(self, line: str) -> str:
        return self._preserve_spacing(_escape_html_text(line))

    def _render_token_part(self, text: str, color: Optional[str]) -> str:
        rendered = self._preserve_spacing(_escape_html_text(text))
        if color:
            return f'<span style="color:{color};">{rendered}</span>'
        return rendered

    def _preserve_spacing(self, text: str) -> str:
        text = text.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        text = text.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')
        text = text.replace('  ', '&nbsp;&nbsp;')
        return text


class ImageProcessor:
    """Process images for WeChat."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def process_image(self, src: str, alt: str = "", title: str = "", image_number: int = 0) -> str:
        """Process image and return HTML."""
        # For WeChat API usage, we keep original src and let the API handle upload
        # Return img tag with original src
        alt_attr = f' alt="{_escape_html(alt)}"' if alt else ''
        title_attr = f' title="{_escape_html(title)}"' if title else ''

        # Use table for center alignment (better WeChat editor compatibility)
        # Note: width="100%" on img helps ensure proper sizing in WeChat
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin:16px 0;background:none;border:none !important;">'
            f'<tr style="border:none !important;"><td align="center" style="padding:0;border:none !important;">'
            f'<img src="{src}"{alt_attr}{title_attr} width="100%" style="display:block;" />'
            f'</td></tr></table>'
        )

    def get_image_base64(self, src: str) -> Optional[str]:
        """Convert image to base64 data URL."""
        # Check if it's already a data URL
        if src.startswith('data:'):
            return src

        # Check if it's a remote URL
        if src.startswith(('http://', 'https://')):
            return None  # Return None to indicate remote URL

        # Local file
        try:
            img_path = self.base_dir / src
            if not img_path.exists():
                return None

            mime_type, _ = mimetypes.guess_type(str(img_path))
            if not mime_type:
                mime_type = 'image/png'

            with open(img_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')

            return f'data:{mime_type};base64,{data}'
        except Exception:
            return None


class MarkdownToWeChatConverter:
    """Convert Markdown to WeChat-compatible HTML."""

    def __init__(self, style: str = "academic_gray", base_dir: Optional[str] = None):
        """
        Initialize converter.

        Args:
            style: Style name (academic_gray, festival, tech, announcement)
            base_dir: Base directory for resolving image paths
        """
        registry = get_theme_registry()
        if not registry.theme_exists(style):
            raise ValueError(f"Unknown style: {style}. Available: {list(registry.list_themes().keys())}")

        self.style_config = registry.get_theme(style)
        self.image_processor = ImageProcessor(base_dir)
        self.code_formatter = CodeBlockFormatter(self.style_config)
        self.image_counter = 0

    def convert(self, md_content: str, title: str = "", source: str = "") -> str:
        """
        Convert Markdown to WeChat HTML.

        Args:
            md_content: Markdown content
            title: Article title
            source: Source attribution

        Returns:
            HTML string compatible with WeChat
        """
        # Parse markdown
        parser = MarkdownParser(md_content)
        md_date = parser.get_front_matter("date", "")
        tags = parser.get_front_matter("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        permalink = parser.get_front_matter("permalink", "")

        # Reset image counter
        self.image_counter = 0

        # Convert body
        html_body = self._convert_body(parser.body)

        # Generate full HTML
        return self._generate_html(md_date, tags, html_body, source or permalink)

    def _convert_body(self, md_body: str) -> str:
        """Convert Markdown body to HTML."""
        # Regex patterns
        _ATX_H_RE = re.compile(r'^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$')
        _IMG_RE_1 = re.compile(r'!\[([^\]]*)\]\((\S+?)\s+"([^"]+)"\)')
        _IMG_RE_2 = re.compile(r'!\[([^\]]*)\]\((\S+?)\)')

        def _strip_front_matter(lines):
            """Remove YAML front-matter."""
            if len(lines) >= 3 and lines[0].strip() == '---':
                i = 1
                while i < len(lines) and lines[i].strip() != '---':
                    i += 1
                if i < len(lines) and lines[i].strip() == '---':
                    return lines[i+1:]
            return lines

        lines = md_body.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        lines = _strip_front_matter(lines)

        sections = []
        cur = None

        in_code = False
        code_lang = ""
        buf_code = []
        in_html_comment = False

        preface = []
        parabuf = []

        def flush_para_buffer():
            nonlocal parabuf
            if parabuf:
                text = '\n'.join(parabuf)
                if text.strip():
                    if cur:
                        cur['items'].append(('paragraph', text))
                    else:
                        preface.append(('paragraph', text))
                parabuf = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Code fence
            if line.lstrip().startswith('```'):
                fence = line.strip()
                if not in_code:
                    in_code = True
                    code_lang = fence[3:].strip()
                    buf_code = []
                else:
                    flush_para_buffer()
                    item = ('code', '\n'.join(buf_code), code_lang)
                    if cur:
                        cur['items'].append(item)
                    else:
                        preface.append(item)
                    in_code = False
                    code_lang = ""
                    buf_code = []
                i += 1
                continue

            if in_code:
                buf_code.append(line)
                i += 1
                continue

            # HTML comments should be ignored in rendered article content.
            # Handle both one-line and multi-line comment blocks.
            if in_html_comment:
                if "-->" in line:
                    in_html_comment = False
                i += 1
                continue

            if "<!--" in line:
                comment_start = line.find("<!--")
                comment_end = line.find("-->", comment_start + 4)
                if comment_end == -1:
                    # Keep any visible prefix before the comment marker, then
                    # enter comment mode for following lines.
                    line = line[:comment_start]
                    in_html_comment = True
                else:
                    # Remove inline HTML comment and keep remaining visible text.
                    line = line[:comment_start] + line[comment_end + 3:]

            stripped_line = line.strip()

            # Image
            m = _IMG_RE_1.search(line)
            if m and line.strip().startswith('!['):
                alt = m.group(1) or ""
                src = m.group(2)
                title = m.group(3)
            else:
                m = _IMG_RE_2.search(line)
                if m and line.strip().startswith('!['):
                    alt = m.group(1) or ""
                    src = m.group(2)
                    title = ""
                else:
                    m = None

            if m:
                flush_para_buffer()
                item = ('image', src, alt, title)
                if cur:
                    cur['items'].append(item)
                else:
                    preface.append(item)
                i += 1
                continue

            # ATX Headers
            hm = _ATX_H_RE.match(line)
            if hm:
                flush_para_buffer()
                level = len(hm.group(1))
                text = hm.group(2).strip()

                if level == 1:
                    # H1 is treated as a heading (not ignored)
                    item = ('heading', text, level)
                    if cur:
                        cur['items'].append(item)
                    else:
                        preface.append(item)
                elif level == 2:
                    if cur:
                        sections.append(cur)
                    else:
                        if preface:
                            sections.append({'level': 0, 'title': '', 'items': preface[:]})
                            preface = []
                    cur = {'level': level, 'title': text, 'items': []}
                elif level == 3:
                    if cur:
                        sections.append(cur)
                    else:
                        if preface:
                            sections.append({'level': 0, 'title': '', 'items': preface[:]})
                            preface = []
                    cur = {'level': level, 'title': text, 'items': []}
                else:
                    item = ('heading', text, level)
                    if cur:
                        cur['items'].append(item)
                    else:
                        preface.append(item)
                i += 1
                continue

            # List items
            list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
            if list_match:
                flush_para_buffer()
                indent = len(list_match.group(1))
                marker = list_match.group(2)
                item_text = list_match.group(3)
                is_ordered = marker not in ['-', '*', '+']
                item = ('list_item', item_text, indent, is_ordered)
                if cur:
                    cur['items'].append(item)
                else:
                    preface.append(item)
                i += 1
                continue

            # Table rows
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                stripped = line.strip()
                cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
                # Check if separator row
                is_separator = all(re.match(r'^[\s\-:]+$', cell) and '-' in cell for cell in cells if cell.strip())

                flush_para_buffer()
                if is_separator:
                    alignments = []
                    for cell in cells:
                        cell = cell.strip()
                        if cell.startswith(':') and cell.endswith(':'):
                            alignments.append('center')
                        elif cell.endswith(':'):
                            alignments.append('right')
                        else:
                            alignments.append('left')
                    item = ('table_separator', alignments)
                else:
                    item = ('table_row', cells)

                if cur:
                    cur['items'].append(item)
                else:
                    preface.append(item)
                i += 1
                continue

            # Blockquote
            if line.lstrip().startswith('>'):
                flush_para_buffer()
                quote_text = line.lstrip()[1:].strip()
                item = ('blockquote', quote_text)
                if cur:
                    cur['items'].append(item)
                else:
                    preface.append(item)
                i += 1
                continue

            # Horizontal rule
            if re.match(r'^(\s*[-*_]\s*){3,}$', stripped_line):
                flush_para_buffer()
                item = ('horizontal_rule',)
                if cur:
                    cur['items'].append(item)
                else:
                    preface.append(item)
                i += 1
                continue

            # Regular paragraph line
            if stripped_line:
                parabuf.append(line)

            i += 1

        flush_para_buffer()

        if cur:
            sections.append(cur)
        elif preface:
            sections.append({'level': 0, 'title': '', 'items': preface})

        # Group items and convert
        for sec in sections:
            sec['items'] = self._group_list_and_table_items(sec['items'])

        html = []
        for sec in sections:
            html.append(self._convert_section(sec['level'], sec['title'], sec['items']))

        return ''.join(html)

    def _group_list_and_table_items(self, items: List[Tuple]) -> List[Tuple]:
        """Group consecutive list items and table rows."""
        grouped = []
        i = 0

        while i < len(items):
            item_type, *item_data = items[i]

            if item_type == 'list_item':
                # Collect list items
                list_items = []
                list_indent = item_data[1] if len(item_data) > 1 else 0
                list_ordered = item_data[2] if len(item_data) > 2 else False

                while i < len(items):
                    check_type, *check_data = items[i]
                    if check_type != 'list_item':
                        break
                    indent = check_data[1] if len(check_data) > 1 else 0
                    is_ordered = check_data[2] if len(check_data) > 2 else False

                    if indent < list_indent or (indent == list_indent and is_ordered != list_ordered):
                        break

                    list_items.append((check_data[0], indent))
                    i += 1

                nested_list = self._build_list_structure(list_items, list_indent, list_ordered)
                grouped.append(('list', nested_list, list_ordered))
                continue

            elif item_type in ('table_row', 'table_separator'):
                # Collect table rows
                table_rows = []
                table_alignments = ['left']
                is_header = True

                j = i
                while j < len(items):
                    check_type, *check_data = items[j]
                    if check_type == 'table_separator':
                        table_alignments = check_data[0] if len(check_data) > 0 else ['left']
                        j += 1
                        continue
                    elif check_type == 'table_row':
                        table_rows.append((check_data[0] if len(check_data) > 0 else [], is_header))
                        is_header = False
                        j += 1
                    else:
                        break

                if table_rows:
                    grouped.append(('table', table_rows, table_alignments))
                i = j
                continue

            else:
                grouped.append(items[i])
                i += 1

        return grouped

    def _build_list_structure(self, items: List[Tuple[str, int]], base_indent: int, is_ordered: bool) -> List:
        """Build nested list structure."""
        result = []
        i = 0

        while i < len(items):
            text, indent = items[i]

            if indent > base_indent:
                # Nested list - find all items at this level
                nested_items = []
                nested_indent = indent
                nested_ordered = False

                while i < len(items):
                    text2, indent2 = items[i]
                    if indent2 < nested_indent:
                        break
                    if indent2 == nested_indent:
                        # Check if ordered
                        nested_ordered = False  # Detect from marker
                        nested_items.append((text2, indent2))
                        i += 1
                    else:
                        nested_items.append((text2, indent2))
                        i += 1

                if nested_items:
                    nested_structure = self._build_list_structure(nested_items, nested_indent, nested_ordered)
                    if result:
                        result[-1] = (result[-1][0], nested_structure, nested_ordered)
            else:
                result.append((text, None, None))
                i += 1

        return result

    def _convert_section(self, level: int, title: str, content: List[Tuple]) -> str:
        """Convert a section to HTML."""
        html_parts = []

        # Check if reference section
        is_reference = False
        if title:
            ref_keywords = ['参考文献', 'references', '参考', 'bibliography']
            is_reference = any(kw in title.lower() for kw in ref_keywords)

        # Output title
        if title and level > 0:
            html_parts.append(self._convert_heading(title, level))

        # Wrap content in card for H2/H3 sections
        if level in (2, 3) and content:
            card_content = []
            has_content = False

            for item in content:
                item_type = item[0]
                item_data = item[1:]

                if item_type == 'heading':
                    text = item_data[0] if len(item_data) > 0 else ""
                    lvl = item_data[1] if len(item_data) > 1 else 4
                    card_content.append(self._convert_heading(text, lvl, is_reference))
                    has_content = True
                elif item_type == 'paragraph':
                    text = item_data[0] if len(item_data) > 0 else ""
                    if text.strip():
                        card_content.append(self._convert_paragraph(text, is_reference))
                        has_content = True
                elif item_type == 'code':
                    code = item_data[0] if len(item_data) > 0 else ""
                    lang = item_data[1] if len(item_data) > 1 else ""
                    card_content.append(self.code_formatter.format_code_block(code, lang))
                    has_content = True
                elif item_type == 'image':
                    src = item_data[0] if len(item_data) > 0 else ""
                    alt = item_data[1] if len(item_data) > 1 else ""
                    title = item_data[2] if len(item_data) > 2 else ""
                    self.image_counter += 1
                    card_content.append(self.image_processor.process_image(src, alt, title, self.image_counter))
                    has_content = True
                elif item_type == 'list':
                    list_struct = item_data[0] if len(item_data) > 0 else []
                    ordered = item_data[1] if len(item_data) > 1 else False
                    if list_struct:
                        card_content.append(self._convert_list(list_struct, ordered, is_reference))
                        has_content = True
                elif item_type == 'table':
                    rows = item_data[0] if len(item_data) > 0 else []
                    aligns = item_data[1] if len(item_data) > 1 else ['left']
                    if rows:
                        card_content.append(self._convert_table(rows, aligns, is_reference))
                        has_content = True
                elif item_type == 'horizontal_rule':
                    card_content.append(self._convert_horizontal_rule())
                    has_content = True
                elif item_type == 'blockquote':
                    text = item_data[0] if len(item_data) > 0 else ""
                    card_content.append(self._convert_blockquote(text, is_reference))
                    has_content = True

            if has_content and card_content:
                # Use table for better WeChat editor compatibility
                card_html = ''.join(card_content)
                # Use style config background color (hex without # for bgcolor attribute)
                card_bg = self.style_config.h2_h3_card_bg_color.replace("#", "")
                if is_reference:
                    # Reference section with lighter text
                    html_parts.append(
                        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{card_bg}" style="width:100%;max-width:100%;table-layout:fixed;background:none;border:none !important;">'
                        f'<tr style="border:none !important;"><td style="padding:8px 0;border:none !important;font-size:0.85em;color:#888888;">'
                        f'<div style="padding:0px;border:none !important;">{card_html}</div></td></tr></table>'
                    )
                else:
                    html_parts.append(
                        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{card_bg}" style="width:100%;max-width:100%;table-layout:fixed;background:none;border:none !important;">'
                        f'<tr style="border:none !important;"><td style="padding:8px 0;border:none !important;">'
                        f'<div style="padding:0px;border:none !important;">{card_html}</div></td></tr></table>'
                    )
        else:
            # Non-card content
            for item in content:
                item_type = item[0]
                item_data = item[1:]

                if item_type == 'heading':
                    text = item_data[0] if len(item_data) > 0 else ""
                    lvl = item_data[1] if len(item_data) > 1 else 4
                    html_parts.append(self._convert_heading(text, lvl, is_reference))
                elif item_type == 'paragraph':
                    html_parts.append(self._convert_paragraph(item_data[0], is_reference))
                elif item_type == 'code':
                    code = item_data[0] if len(item_data) > 0 else ""
                    lang = item_data[1] if len(item_data) > 1 else ""
                    html_parts.append(self.code_formatter.format_code_block(code, lang))
                elif item_type == 'image':
                    src = item_data[0] if len(item_data) > 0 else ""
                    alt = item_data[1] if len(item_data) > 1 else ""
                    title = item_data[2] if len(item_data) > 2 else ""
                    self.image_counter += 1
                    html_parts.append(self.image_processor.process_image(src, alt, title, self.image_counter))
                elif item_type == 'list':
                    list_struct = item_data[0] if len(item_data) > 0 else []
                    ordered = item_data[1] if len(item_data) > 1 else False
                    html_parts.append(self._convert_list(list_struct, ordered, is_reference))
                elif item_type == 'table':
                    rows = item_data[0] if len(item_data) > 0 else []
                    aligns = item_data[1] if len(item_data) > 1 else ['left']
                    html_parts.append(self._convert_table(rows, aligns, is_reference))
                elif item_type == 'horizontal_rule':
                    html_parts.append(self._convert_horizontal_rule())
                elif item_type == 'blockquote':
                    text = item_data[0] if len(item_data) > 0 else ""
                    html_parts.append(self._convert_blockquote(text, is_reference))

        return ''.join(html_parts)

    def _convert_heading(self, text: str, level: int, is_reference: bool = False) -> str:
        """Convert heading to HTML."""
        text = self._inline_format(text)
        paragraph_font_size = getattr(self.style_config, 'paragraph_font_size', '16px')

        if level == 1:
            # H1: Large centered heading with accent color
            return (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin:0px;background:none;border:none !important;">'
                f'<tr style="border:none !important;"><td align="center" style="border:none !important;padding:0;">'
                f'<h1 style="font-size:22px;font-weight:bold;color:{self.style_config.h2_title_text_color};margin:0;padding:0;">'
                f'{text}'
                f'</h1>'
                f'</td></tr></table>'
            )
        elif level == 2:
            # H2: Use table for WeChat editor compatibility.
            return (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin:0px;background:none;border:none !important;">'
                f'<tr style="border:none !important;"><td align="center" style="border:none !important;padding:0;">'
                f'<span style="display:inline-block;background:none;color:{self.style_config.h2_title_text_color};padding:6px 20px;font-size:18px;font-weight:bold;border-radius:8px;">'
                f'{text}</span>'
                f'</td></tr></table>'
            )
        elif level == 3:
            # H3: Use table for left-border style (avoid border-radius)
            return (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{self.style_config.h3_title_bg_color.replace("#", "")}" style="width:100%;max-width:100%;table-layout:fixed;margin:0px;background:none;border:none !important;">'
                f'<tr style="border:none !important;"><td style="border:none !important;padding:0;">'
                f'<span style="display:block;padding:8px 8px 8px 0px;font-size:{paragraph_font_size};font-weight:bold;color:{self.style_config.h3_title_text_color};">{text}</span>'
                f'</td></tr></table>'
            )
        else:
            # H4+
            return f'<h{level} style="font-size:{paragraph_font_size};font-weight:bold;margin:14px 0 8px;color:{self.style_config.h3_title_text_color};">{text}</h{level}>'

    def _convert_paragraph(self, text: str, is_reference: bool = False) -> str:
        """Convert paragraph to HTML with improved styling."""
        segments = [self._inline_format(part) for part in text.split('\n')]

        # Get styles from config
        font_size = getattr(self.style_config, 'paragraph_font_size', '16px')
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')

        if is_reference:
            font_size = '0.85em'
            text_color = '#888888'

        paragraph_html = []
        for index, segment in enumerate(segments):
            margin = "0 0 10px 0" if index < len(segments) - 1 else "0"
            style = self._paragraph_style(font_size, text_color, margin=margin)
            paragraph_html.append(f'<p style="{style}">{segment}</p>')

        return ''.join(paragraph_html)

    def _paragraph_style(self, font_size: str, text_color: str, margin: str = "16px 0") -> str:
        """Build a minimal paragraph style shared across paragraph-like blocks."""
        return f'margin:{margin};font-size:{font_size};color:{text_color};'

    def _convert_horizontal_rule(self) -> str:
        """Convert horizontal rule to HTML with elegant styling."""
        # Get border color from config or use default
        border_color = getattr(self.style_config, 'table_border_color', '#DEE2E6')
        divider_html = f'<div style="border:none !important;height:0;font-size:0;line-height:1;"></div>'
        if not _has_visible_html_content(divider_html):
            return divider_html
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin:28px 0;background:none;border:none !important;">'
            f'<tr style="border:none !important;"><td style="padding:0;border:none !important;">'
            f'{divider_html}'
            f'</td></tr>'
            f'</table>'
        )

    def _convert_blockquote(self, text: str, is_reference: bool = False) -> str:
        """Convert blockquote to HTML using table for WeChat compatibility."""
        text = self._inline_format(text)
        # Use a fixed neutral background and theme accent border for citation-like quotes.
        bg_color = '#f0f0f0'
        border_color = getattr(self.style_config, 'h2_title_text_color', '#333333')
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')

        # Use table wrapper for WeChat compatibility, with the visual styling on the inner div.
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin:16px 0;background:none;border:none !important;">'
            f'<tr style="border:none !important;"><td style="padding:0;border:none !important;">'
            f'<div style="background-color:{bg_color};padding:10px;border-left:3px solid {border_color} !important;border:none;"><p style="{self._paragraph_style("13px", text_color, margin="0")}">{text}</p></div>'
            f'</td></tr></table>'
        )

    def _convert_list(self, list_structure: List, is_ordered: bool, is_reference: bool = False) -> str:
        """Convert list structure to HTML with improved styling."""
        tag = 'ol' if is_ordered else 'ul'

        # Get text color from config
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')
        font_size = getattr(self.style_config, 'paragraph_font_size', '13px')

        style = f'margin:16px 0;padding-left:28px;color:{text_color};' + ('font-size:0.85em;color:#888888;' if is_reference else '')

        items_html = []
        for text, nested, nested_ordered in list_structure:
            item_text = self._inline_format(text)

            if nested:
                nested_html = self._convert_list(nested, nested_ordered, is_reference)
                items_html.append(f'<li style="margin:10px 0;padding:0;font-size:{font_size};">{item_text}{nested_html}</li>')
            else:
                items_html.append(f'<li style="margin:10px 0;padding:0;font-size:{font_size};">{item_text}</li>')

        return f'<{tag} style="{style}">{"".join(items_html)}</{tag}>'

    def _convert_table(self, table_rows: List[Tuple[List[str], bool]], alignments: List[str], is_reference: bool = False) -> str:
        """Convert table to HTML with improved styling."""
        if not table_rows:
            return ""

        # Get styles from config
        header_bg = '#e5e5e5'
        border_color = getattr(self.style_config, 'table_border_color', '#DEE2E6')
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')
        header_text_color = getattr(self.style_config, 'h2_title_text_color', '#333333')

        # Build table HTML
        header_html = ''
        body_html = ''

        body_row_index = 0
        for idx, (cells, is_header) in enumerate(table_rows):
            row_cells = []
            row_bg = 'transparent' if body_row_index % 2 == 0 else '#f0f0f0'

            for col_idx, cell in enumerate(cells):
                align = alignments[col_idx] if col_idx < len(alignments) else 'left'
                cell_text = self._inline_format(cell)
                align_style = f'text-align:{align};'
                padding = 'padding:12px 16px;'
                border = f'border-top:1px solid {border_color};border-bottom:1px solid {border_color};border-left:none;border-right:none;'

                if is_header:
                    style = f'{padding}{border}text-align:center;background-color:{header_bg};font-weight:bold;color:{header_text_color};font-size:13px;'
                    row_cells.append(f'<th style="{style}">{cell_text}</th>')
                else:
                    style = f'{padding}{border}{align_style}background-color:{row_bg};color:{text_color};font-size:13px;'
                    row_cells.append(f'<td style="{style}">{cell_text}</td>')

            row_html = f'<tr>{"".join(row_cells)}</tr>'
            if is_header:
                header_html = row_html
            else:
                body_html += row_html
                body_row_index += 1

        # Output the native table directly instead of wrapping it in a decorative table.
        table_content = '<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:13px;">'
        if header_html:
            table_content += f'<thead>{header_html}</thead>'
        if body_html:
            table_content += f'<tbody>{body_html}</tbody>'
        table_content += '</table>'

        return table_content

    def _inline_format(self, text: str) -> str:
        """Apply inline formatting (bold, italic, code, links)."""
        # Handle Markdown escape sequences first (before HTML escaping)
        # \# -> #, \* -> *, \_ -> _, etc.
        text = re.sub(r'\\([\#\*\_\[\]\(\)\`\\])', r'\1', text)
        # Handle HTML entities like &#x20; (space), &#x27; (')
        text = html.unescape(text)
        # Strip legacy <font ...> wrappers from source markdown/html exports.
        # Keep inner text and let theme styles handle final appearance.
        text = re.sub(r'</?font\b[^>]*>', '', text, flags=re.IGNORECASE)

        # Escape HTML first
        text = _escape_html(text)

        # Unescape again to restore characters that shouldn't be escaped in content
        # We want to keep < > & escaped for security, but allow quotes and apostrophes
        text = text.replace('&#x27;', "'").replace('&#39;', "'")

        # Bold: **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Italic: *text* (not inside bold)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Inline code: `code`
        # Use a fixed neutral background for inline code across themes.
        inline_code_bg = '#f0f0f0'
        inline_code_color = getattr(self.style_config, 'inline_code_text_color', '#E83E8C')

        def code_replace(match):
            code = match.group(1)
            trailing_punct = match.group(2) or ""
            # Use span instead of code to avoid WeChat default code-tag overrides
            # that may force unexpected line breaks in list items.
            display_text = f"{code}{trailing_punct}"
            code_span = (
                f'<span style="display:inline;line-height:1;vertical-align:baseline;'
                f'background-color:{inline_code_bg};padding:1px 4px;border-radius:3px;'
                f'font-family:SF Mono,Monaco,monospace;font-size:12px;'
                f'color:{inline_code_color};font-weight:500;">{display_text}</span>'
            )
            return code_span
        text = re.sub(r'`([^`]+)`([：:])?', code_replace, text)

        # Links: [text](url)
        # Use link color from config with underline on hover effect (static)
        link_color = getattr(self.style_config, 'link_color', '#0066CC')

        def link_replace(match):
            link_text = match.group(1)
            url = match.group(2)
            # Skip anchor links
            if url.startswith('#'):
                return link_text
            return f'<a href="{url}" style="color:{link_color};text-decoration:none;font-weight:500;border-bottom:1px solid {link_color};">{link_text}</a>'
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replace, text)

        # Colored text: **text**{color:#xxx} or [text]{color:#xxx}
        text = re.sub(r'\*\*(.+?)\*\*\{color:([^}]+)\}', r'<strong style="color:\2;">\1</strong>', text)
        text = re.sub(r'\[([^\]]+)\]\{color:([^}]+)\}', r'<span style="color:\2;">\1</span>', text)

        return text

    def _generate_html(self, date: str, tags: List[str], body_html: str, source: str) -> str:
        """Generate complete HTML document using table-based layout for WeChat editor compatibility."""
        parts = []

        # Build meta info
        if date or tags:
            meta_parts = []
            if date:
                meta_parts.append(_escape_html(date))
            if tags:
                tag_str = ' '.join(f'#{_escape_html(str(t))}' for t in tags)
                meta_parts.append(tag_str)

            if meta_parts:
                parts.append(
                    f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin-bottom:16px;background:none;border:none !important;">'
                    f'<tr style="border:none !important;"><td style="color:{self.style_config.meta_text_color};font-size:{self.style_config.meta_font_size};padding:0;border:none !important;">'
                    f'{" | ".join(meta_parts)}'
                    f'</td></tr></table>'
                )

        # Body content
        parts.append(body_html)

        # Build source footer
        if source:
            parts.append(
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:100%;table-layout:fixed;margin-top:24px;background:none;border:none !important;">'
                f'<tr style="border:none !important;"><td align="center" style="padding:0;border:none !important;">'
                f'<div style="padding:0px;border:none !important;color:{self.style_config.source_text_color};font-size:{self.style_config.source_font_size};">来源: '
                f'<a href="{_escape_html(source)}" style="color:{self.style_config.source_text_color};">{_escape_html(source)}</a>'
                f'</div>'
                f'</td></tr></table>'
            )

        # Wrap the full article in a page-level container so over-wide content
        # cannot expand the preview/page width.
        full_html = "".join(parts)

        return (
            '<div style="width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;">'
            f'{full_html}'
            '</div>'
        )
