"""Markdown to WeChat HTML Converter.


"""

import re
import base64
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import html


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)


@dataclass
class StyleConfig:
    """Style configuration for WeChat HTML output."""
    name: str
    # Header styles
    header_bg_color: str = "#3C3C3C"
    header_text_color: str = "#FFFFFF"
    header_font_size: str = "20px"
    # Card styles
    card_bg_color: str = "#FFFFFF"
    card_border_color: str = "#D9D9D9"
    card_text_color: str = "#333333"
    # H2/H3 card styles
    h2_h3_card_bg_color: str = "#FAFAFA"  # Solid color for WeChat editor compatibility
    h2_h3_card_border_color: str = "#E8E8E8"
    # H2 title styles
    h2_title_line_color: str = "#333333"
    h2_title_text_color: str = "#333333"
    h2_title_font_size: str = "18px"
    # H3 title styles
    h3_title_bg_color: str = "#F5F5F5"
    h3_title_border_color: str = "#3C3C3C"
    h3_title_text_color: str = "#333333"
    h3_title_font_size: str = "16px"
    # Code block styles
    code_bg_color: str = "#F4F4F4"
    code_border_color: str = "#E0E0E0"
    # Meta info styles
    meta_text_color: str = "#888888"
    meta_font_size: str = "12px"
    # Source styles
    source_text_color: str = "#999999"
    source_font_size: str = "12px"


# Predefined styles
# Note: Using hex colors only (no rgba) for WeChat editor compatibility
STYLES = {
    "academic_gray": StyleConfig(
        name="学术灰风格",
        header_bg_color="#3C3C3C",
        header_text_color="#FFFFFF",
        header_font_size="20px",
        card_bg_color="#FFFFFF",
        card_border_color="#D9D9D9",
        card_text_color="#333333",
        h2_h3_card_bg_color="#FAFAFA",  # Solid color instead of rgba
        h2_h3_card_border_color="#E8E8E8",
        h2_title_line_color="#333333",
        h2_title_text_color="#333333",
        h2_title_font_size="18px",
        h3_title_bg_color="#F5F5F5",
        h3_title_border_color="#3C3C3C",
        h3_title_text_color="#333333",
        h3_title_font_size="16px",
        code_bg_color="#F4F4F4",
        code_border_color="#E0E0E0",
        meta_text_color="#888888",
        meta_font_size="12px",
        source_text_color="#999999",
        source_font_size="12px",
    ),
    "festival": StyleConfig(
        name="节日快乐色彩系",
        header_bg_color="#FF6B6B",
        header_text_color="#FFFFFF",
        header_font_size="20px",
        card_bg_color="#FFF8E1",
        card_border_color="#FFB74D",
        card_text_color="#5D4037",
        h2_h3_card_bg_color="#FFFDE7",  # Solid light yellow
        h2_h3_card_border_color="#FFB74D",
        h2_title_line_color="#FF6B6B",
        h2_title_text_color="#D32F2F",
        h2_title_font_size="18px",
        h3_title_bg_color="#FFE082",
        h3_title_border_color="#FF6B6B",
        h3_title_text_color="#D32F2F",
        h3_title_font_size="16px",
        code_bg_color="#FFF3E0",
        code_border_color="#FFB74D",
        meta_text_color="#8D6E63",
        meta_font_size="12px",
        source_text_color="#A1887F",
        source_font_size="12px",
    ),
    "tech": StyleConfig(
        name="科技产品介绍色彩系",
        header_bg_color="#1565C0",
        header_text_color="#FFFFFF",
        header_font_size="20px",
        card_bg_color="#E3F2FD",
        card_border_color="#42A5F5",
        card_text_color="#0D47A1",
        h2_h3_card_bg_color="#E8F4FD",  # Solid light blue
        h2_h3_card_border_color="#42A5F5",
        h2_title_line_color="#1565C0",
        h2_title_text_color="#0D47A1",
        h2_title_font_size="18px",
        h3_title_bg_color="#BBDEFB",
        h3_title_border_color="#1565C0",
        h3_title_text_color="#0D47A1",
        h3_title_font_size="16px",
        code_bg_color="#E1F5FE",
        code_border_color="#26C6DA",
        meta_text_color="#546E7A",
        meta_font_size="12px",
        source_text_color="#78909C",
        source_font_size="12px",
    ),
    "announcement": StyleConfig(
        name="重大事情告知色彩系",
        header_bg_color="#D32F2F",
        header_text_color="#FFFFFF",
        header_font_size="22px",
        card_bg_color="#FFF3E0",
        card_border_color="#FF5722",
        card_text_color="#BF360C",
        h2_h3_card_bg_color="#FFF8E1",  # Solid light orange
        h2_h3_card_border_color="#FF5722",
        h2_title_line_color="#D32F2F",
        h2_title_text_color="#BF360C",
        h2_title_font_size="20px",
        h3_title_bg_color="#FFE0B2",
        h3_title_border_color="#D32F2F",
        h3_title_text_color="#BF360C",
        h3_title_font_size="17px",
        code_bg_color="#FFEBEE",
        code_border_color="#EF5350",
        meta_text_color="#8D6E63",
        meta_font_size="12px",
        source_text_color="#A1887F",
        source_font_size="12px",
    ),
}


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

    def __init__(self, style_config: Optional[StyleConfig] = None):
        self.style_config = style_config or STYLES["academic_gray"]

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

        # Process lines
        processed_lines = []
        for i, line in enumerate(lines, 1):
            # Remove common indentation
            if len(line) >= min_indent:
                content = line[min_indent:]
            else:
                content = line

            # Escape HTML
            content = _escape_html(content)
            # Replace spaces with &nbsp; for preservation
            content = content.replace('  ', '&nbsp;&nbsp;')
            content = content.replace(' ', '&nbsp;')

            # Line number - using table-based layout for WeChat compatibility
            if show_line_numbers:
                # Use table row instead of inline-block for better WeChat editor support
                line_num = f'<td style="color:#999;width:2em;text-align:right;padding-right:1em;">{i}</td>'
                processed_lines.append(f'<tr>{line_num}<td>{content}</td></tr>')
            else:
                processed_lines.append(f'<tr><td colspan="2">{content}</td></tr>')

        # Use table-based layout for better WeChat editor compatibility
        # WeChat editor preserves table attributes better than CSS
        code_table = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="font-family:SF Mono,Monaco,monospace;font-size:13px;line-height:1.6;">'
            f'{"".join(processed_lines)}</table>'
        )

        # Outer table for border and background
        return (
            f'<table width="100%" cellpadding="12" cellspacing="0" border="0" '
            f'bgcolor="{self.style_config.code_bg_color.replace("#", "")}">'
            f'<tr><td style="border:1px solid {self.style_config.code_border_color};">'
            f'{code_table}</td></tr></table>'
        )


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
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:16px 0;">'
            f'<tr><td align="center">'
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
        if style not in STYLES:
            raise ValueError(f"Unknown style: {style}. Available: {list(STYLES.keys())}")

        self.style_config = STYLES[style]
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
        md_title = parser.get_front_matter("title", title)
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
        return self._generate_html(md_title, md_date, tags, html_body, source or permalink)

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
                    # H1 is ignored as section divider
                    i += 1
                    continue
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
                        f'<table width="100%" cellpadding="12" cellspacing="0" border="0" bgcolor="{card_bg}">'
                        f'<tr><td style="border:1px solid {self.style_config.h2_h3_card_border_color};line-height:1.9;font-size:0.85em;color:#888888;">'
                        f'{card_html}</td></tr></table>'
                    )
                else:
                    html_parts.append(
                        f'<table width="100%" cellpadding="12" cellspacing="0" border="0" bgcolor="{card_bg}">'
                        f'<tr><td style="border:1px solid {self.style_config.h2_h3_card_border_color};line-height:1.9;">'
                        f'{card_html}</td></tr></table>'
                    )
        else:
            # Non-card content
            for item in content:
                item_type = item[0]
                item_data = item[1:]

                if item_type == 'paragraph':
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

        if level == 2:
            # H2: Use table for WeChat editor compatibility (avoid position:absolute)
            # Use white text on colored background for better visibility
            return (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0 16px;">'
                f'<tr><td align="center" style="border-bottom:2px solid {self.style_config.h2_title_line_color};padding-bottom:8px;">'
                f'<span style="background:{self.style_config.h2_title_line_color};color:#FFFFFF;padding:6px 20px;font-size:{self.style_config.h2_title_font_size};font-weight:bold;">'
                f'{text}</span>'
                f'</td></tr></table>'
            )
        elif level == 3:
            # H3: Use table for left-border style (avoid border-radius)
            return (
                f'<table width="100%" cellpadding="8" cellspacing="0" border="0" bgcolor="{self.style_config.h3_title_bg_color.replace("#", "")}" style="margin:18px 0 12px;">'
                f'<tr><td style="border-left:4px solid {self.style_config.h3_title_border_color};font-size:{self.style_config.h3_title_font_size};font-weight:bold;color:{self.style_config.h3_title_text_color};">'
                f'{text}'
                f'</td></tr></table>'
            )
        else:
            # H4+
            size = max(14, 18 - (level - 4) * 2)
            return f'<h{level} style="font-size:{size}px;font-weight:bold;margin:14px 0 8px;color:{self.style_config.h3_title_text_color};">{text}</h{level}>'

    def _convert_paragraph(self, text: str, is_reference: bool = False) -> str:
        """Convert paragraph to HTML."""
        text = self._inline_format(text)
        style = 'margin:12px 0;line-height:1.8;'
        if is_reference:
            style += 'font-size:0.85em;color:#888888;'
        return f'<p style="{style}">{text}</p>'

    def _convert_horizontal_rule(self) -> str:
        """Convert horizontal rule to HTML using table for WeChat compatibility."""
        return '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0;"><tr><td height="1" bgcolor="#dddddd"></td></tr></table>'

    def _convert_blockquote(self, text: str, is_reference: bool = False) -> str:
        """Convert blockquote to HTML using table for WeChat compatibility."""
        text = self._inline_format(text)
        # Use table with left border for better WeChat editor compatibility
        return (
            f'<table width="100%" cellpadding="8" cellspacing="0" border="0" bgcolor="f9f9f9" style="margin:12px 0;">'
            f'<tr><td style="border-left:4px solid #dddddd;color:#666666;font-style:italic;">'
            f'{text}'
            f'</td></tr></table>'
        )

    def _convert_list(self, list_structure: List, is_ordered: bool, is_reference: bool = False) -> str:
        """Convert list structure to HTML."""
        tag = 'ol' if is_ordered else 'ul'
        style = 'margin:12px 0;padding-left:24px;' + ('font-size:0.85em;color:#888888;' if is_reference else '')

        items_html = []
        for text, nested, nested_ordered in list_structure:
            item_text = self._inline_format(text)

            if nested:
                nested_html = self._convert_list(nested, nested_ordered, is_reference)
                items_html.append(f'<li style="margin:6px 0;line-height:1.7;">{item_text}{nested_html}</li>')
            else:
                items_html.append(f'<li style="margin:6px 0;line-height:1.7;">{item_text}</li>')

        return f'<{tag} style="{style}">{"".join(items_html)}</{tag}>'

    def _convert_table(self, table_rows: List[Tuple[List[str], bool]], alignments: List[str], is_reference: bool = False) -> str:
        """Convert table to HTML."""
        if not table_rows:
            return ""

        # Build table HTML
        header_html = ''
        body_html = ''

        for idx, (cells, is_header) in enumerate(table_rows):
            row_cells = []
            for col_idx, cell in enumerate(cells):
                align = alignments[col_idx] if col_idx < len(alignments) else 'left'
                cell_text = self._inline_format(cell)
                align_style = f'text-align:{align};'
                padding = 'padding:10px 12px;'
                border = 'border:1px solid #ddd;'

                if is_header:
                    style = f'{padding}{border}{align_style}background:#f5f5f5;font-weight:bold;'
                    row_cells.append(f'<th style="{style}">{cell_text}</th>')
                else:
                    style = f'{padding}{border}{align_style}'
                    row_cells.append(f'<td style="{style}">{cell_text}</td>')

            row_html = f'<tr>{"".join(row_cells)}</tr>'
            if is_header:
                header_html = row_html
            else:
                body_html += row_html

        # Combine
        table_html = '<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">'
        if header_html:
            table_html += f'<thead>{header_html}</thead>'
        if body_html:
            table_html += f'<tbody>{body_html}</tbody>'
        table_html += '</table>'

        # Return table directly without overflow wrapper
        # Note: WeChat editor doesn't support overflow-x well
        return table_html

    def _inline_format(self, text: str) -> str:
        """Apply inline formatting (bold, italic, code, links)."""
        # Escape HTML first
        text = _escape_html(text)

        # Bold: **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Italic: *text* (not inside bold)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Inline code: `code`
        # Note: Avoid border-radius as WeChat editor may not support it well
        def code_replace(match):
            code = match.group(1)
            return f'<code style="background:#f4f4f4;padding:2px 6px;font-family:SF Mono,monospace;font-size:0.9em;color:#c7254e;">{code}</code>'
        text = re.sub(r'`([^`]+)`', code_replace, text)

        # Links: [text](url)
        def link_replace(match):
            link_text = match.group(1)
            url = match.group(2)
            # Skip anchor links
            if url.startswith('#'):
                return link_text
            return f'<a href="{url}" style="color:#576b95;text-decoration:none;">{link_text}</a>'
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replace, text)

        # Colored text: **text**{color:#xxx} or [text]{color:#xxx}
        text = re.sub(r'\*\*(.+?)\*\*\{color:([^}]+)\}', r'<strong style="color:\2;">\1</strong>', text)
        text = re.sub(r'\[([^\]]+)\]\{color:([^}]+)\}', r'<span style="color:\2;">\1</span>', text)

        return text

    def _generate_html(self, title: str, date: str, tags: List[str], body_html: str, source: str) -> str:
        """Generate complete HTML document using table-based layout for WeChat editor compatibility."""
        parts = []

        # Build header using table
        if title:
            header_bg = self.style_config.header_bg_color.replace("#", "")
            parts.append(
                f'<table width="100%" cellpadding="20" cellspacing="0" border="0" bgcolor="{header_bg}" style="margin-bottom:16px;">'
                f'<tr><td style="color:{self.style_config.header_text_color};font-size:{self.style_config.header_font_size};font-weight:bold;">'
                f'{_escape_html(title)}'
                f'</td></tr></table>'
            )

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
                    f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:16px;">'
                    f'<tr><td style="color:{self.style_config.meta_text_color};font-size:{self.style_config.meta_font_size};padding:0 4px;">'
                    f'{" | ".join(meta_parts)}'
                    f'</td></tr></table>'
                )

        # Body content
        parts.append(body_html)

        # Build source footer
        if source:
            parts.append(
                f'<table width="100%" cellpadding="16" cellspacing="0" border="0" style="margin-top:24px;">'
                f'<tr><td align="center" style="border-top:1px solid #eeeeee;color:{self.style_config.source_text_color};font-size:{self.style_config.source_font_size};">'
                f'来源: <a href="{_escape_html(source)}" style="color:{self.style_config.source_text_color};">'
                f'{_escape_html(source)}</a>'
                f'</td></tr></table>'
            )

        # Wrap in outer table without border for cleaner look
        # WeChat editor works better with simple table structure
        full_html = f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td>{"".join(parts)}</td></tr></table>'

        return full_html
