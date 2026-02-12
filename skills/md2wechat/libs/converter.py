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
    code_bg_color: str = "#F8F9FA"
    code_border_color: str = "#E9ECEF"
    code_text_color: str = "#212529"
    # Inline code styles
    inline_code_bg_color: str = "#F1F3F5"
    inline_code_text_color: str = "#E83E8C"
    # Paragraph styles
    paragraph_font_size: str = "16px"
    paragraph_line_height: str = "1.75"
    paragraph_color: str = "#333333"
    # Blockquote styles
    blockquote_bg_color: str = "#F8F9FA"
    blockquote_border_color: str = "#DEE2E6"
    blockquote_text_color: str = "#6C757D"
    # Table styles
    table_header_bg_color: str = "#F1F3F5"
    table_border_color: str = "#DEE2E6"
    # Link styles
    link_color: str = "#0066CC"
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
        header_bg_color="#2C3E50",
        header_text_color="#FFFFFF",
        header_font_size="22px",
        card_bg_color="#FFFFFF",
        card_border_color="#E0E0E0",
        card_text_color="#2C3E50",
        h2_h3_card_bg_color="#FAFAFA",
        h2_h3_card_border_color="#E8E8E8",
        h2_title_line_color="#34495E",
        h2_title_text_color="#2C3E50",
        h2_title_font_size="20px",
        h3_title_bg_color="#ECF0F1",
        h3_title_border_color="#34495E",
        h3_title_text_color="#34495E",
        h3_title_font_size="17px",
        code_bg_color="#F8F9FA",
        code_border_color="#E9ECEF",
        code_text_color="#2C3E50",
        inline_code_bg_color="#F1F3F5",
        inline_code_text_color="#C0392B",
        paragraph_font_size="16px",
        paragraph_line_height="1.8",
        paragraph_color="#2C3E50",
        blockquote_bg_color="#F8F9FA",
        blockquote_border_color="#BDC3C7",
        blockquote_text_color="#5D6D7E",
        table_header_bg_color="#ECF0F1",
        table_border_color="#BDC3C7",
        link_color="#2980B9",
        meta_text_color="#7F8C8D",
        meta_font_size="13px",
        source_text_color="#95A5A6",
        source_font_size="12px",
    ),
    "festival": StyleConfig(
        name="节日快乐色彩系",
        header_bg_color="#E74C3C",
        header_text_color="#FFFFFF",
        header_font_size="22px",
        card_bg_color="#FFF8E1",
        card_border_color="#F39C12",
        card_text_color="#5D4037",
        h2_h3_card_bg_color="#FFFDE7",
        h2_h3_card_border_color="#F39C12",
        h2_title_line_color="#E74C3C",
        h2_title_text_color="#C0392B",
        h2_title_font_size="20px",
        h3_title_bg_color="#FFE082",
        h3_title_border_color="#E74C3C",
        h3_title_text_color="#C0392B",
        h3_title_font_size="17px",
        code_bg_color="#FFF8E1",
        code_border_color="#F39C12",
        code_text_color="#5D4037",
        inline_code_bg_color="#FFECB3",
        inline_code_text_color="#E65100",
        paragraph_font_size="16px",
        paragraph_line_height="1.8",
        paragraph_color="#4E342E",
        blockquote_bg_color="#FFF8E1",
        blockquote_border_color="#FFB74D",
        blockquote_text_color="#6D4C41",
        table_header_bg_color="#FFE082",
        table_border_color="#FFB74D",
        link_color="#D84315",
        meta_text_color="#8D6E63",
        meta_font_size="13px",
        source_text_color="#A1887F",
        source_font_size="12px",
    ),
    "tech": StyleConfig(
        name="科技产品介绍色彩系",
        header_bg_color="#1565C0",
        header_text_color="#FFFFFF",
        header_font_size="22px",
        card_bg_color="#E3F2FD",
        card_border_color="#42A5F5",
        card_text_color="#0D47A1",
        h2_h3_card_bg_color="#E8F4FD",
        h2_h3_card_border_color="#42A5F5",
        h2_title_line_color="#1565C0",
        h2_title_text_color="#0D47A1",
        h2_title_font_size="20px",
        h3_title_bg_color="#BBDEFB",
        h3_title_border_color="#1565C0",
        h3_title_text_color="#0D47A1",
        h3_title_font_size="17px",
        code_bg_color="#E3F2FD",
        code_border_color="#64B5F6",
        code_text_color="#0D47A1",
        inline_code_bg_color="#BBDEFB",
        inline_code_text_color="#1565C0",
        paragraph_font_size="16px",
        paragraph_line_height="1.8",
        paragraph_color="#0D47A1",
        blockquote_bg_color="#E3F2FD",
        blockquote_border_color="#64B5F6",
        blockquote_text_color="#1565C0",
        table_header_bg_color="#BBDEFB",
        table_border_color="#64B5F6",
        link_color="#0277BD",
        meta_text_color="#546E7A",
        meta_font_size="13px",
        source_text_color="#78909C",
        source_font_size="12px",
    ),
    "announcement": StyleConfig(
        name="重大事情告知色彩系",
        header_bg_color="#C0392B",
        header_text_color="#FFFFFF",
        header_font_size="22px",
        card_bg_color="#FEF5E7",
        card_border_color="#E67E22",
        card_text_color="#922B21",
        h2_h3_card_bg_color="#FEF9E7",
        h2_h3_card_border_color="#E67E22",
        h2_title_line_color="#C0392B",
        h2_title_text_color="#922B21",
        h2_title_font_size="20px",
        h3_title_bg_color="#FAD7A0",
        h3_title_border_color="#C0392B",
        h3_title_text_color="#922B21",
        h3_title_font_size="17px",
        code_bg_color="#FEF5E7",
        code_border_color="#E67E22",
        code_text_color="#922B21",
        inline_code_bg_color="#FAD7A0",
        inline_code_text_color="#C0392B",
        paragraph_font_size="16px",
        paragraph_line_height="1.8",
        paragraph_color="#7B241C",
        blockquote_bg_color="#FEF5E7",
        blockquote_border_color="#E67E22",
        blockquote_text_color="#A04000",
        table_header_bg_color="#FAD7A0",
        table_border_color="#E67E22",
        link_color="#C0392B",
        meta_text_color="#A04000",
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

        # Get colors from config
        bg_color = self.style_config.code_bg_color
        border_color = self.style_config.code_border_color
        text_color = getattr(self.style_config, 'code_text_color', '#212529')

        # Process lines - use <pre> for better WeChat editor compatibility
        # WeChat respects <pre> tag styles more than <div>
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
            content = content.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')
            content = content.replace('  ', '&nbsp;&nbsp;')

            # Add line number with improved styling - use span with fixed-width font
            if show_line_numbers:
                # Use pre tag for each line to ensure font-size is respected
                line_num = f'<span style="color:#868E96;display:inline-block;width:2.5em;text-align:right;margin-right:0.8em;font-size:12px;">{i}</span>'
                processed_lines.append(f'{line_num}{content}')
            else:
                processed_lines.append(content)

        # Join with newline - use <br> for line breaks since we're using pre
        code_text = '<br>\n'.join(processed_lines)

        # Outer container with pre tag for better font-size control
        # Use pre tag with specific styling to prevent WeChat from overriding
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:16px 0;">'
            f'<tr><td style="background-color:{bg_color};border:1px solid {border_color};padding:16px;border-radius:8px;">'
            f'<pre style="margin:0;padding:0;font-family:SF Mono,Monaco,monospace,Consolas,Courier New;font-size:13px;line-height:1.7;color:{text_color};white-space:pre-wrap;word-wrap:break-word;">{code_text}</pre>'
            f'</td></tr></table>'
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

        if level == 1:
            # H1: Large centered heading with accent color
            return (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0 20px;">'
                f'<tr><td align="center">'
                f'<h1 style="font-size:26px;font-weight:bold;color:{self.style_config.h2_title_text_color};margin:0;padding:0;line-height:1.4;">'
                f'{text}'
                f'</h1>'
                f'</td></tr></table>'
            )
        elif level == 2:
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
        """Convert paragraph to HTML with improved styling."""
        text = self._inline_format(text)
        # Convert newlines to <br> tags for line breaks within paragraphs
        text = text.replace('\n', '<br>')

        # Get styles from config
        font_size = getattr(self.style_config, 'paragraph_font_size', '16px')
        line_height = getattr(self.style_config, 'paragraph_line_height', '1.8')
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')

        style = f'margin:16px 0;line-height:{line_height};font-size:{font_size};color:{text_color};letter-spacing:0.3px;text-align:justify;'
        if is_reference:
            style += 'font-size:0.85em;color:#888888;'
        return f'<p style="{style}">{text}</p>'

    def _convert_horizontal_rule(self) -> str:
        """Convert horizontal rule to HTML with elegant styling."""
        # Get border color from config or use default
        border_color = getattr(self.style_config, 'table_border_color', '#DEE2E6')
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0;">'
            f'<tr><td style="border-top:1px solid {border_color};height:0;font-size:0;line-height:0;"></td></tr>'
            f'</table>'
        )

    def _convert_blockquote(self, text: str, is_reference: bool = False) -> str:
        """Convert blockquote to HTML using table for WeChat compatibility."""
        text = self._inline_format(text)
        # Get styles from config
        bg_color = getattr(self.style_config, 'blockquote_bg_color', '#F8F9FA')
        border_color = getattr(self.style_config, 'blockquote_border_color', '#DEE2E6')
        text_color = getattr(self.style_config, 'blockquote_text_color', '#6C757D')

        # Use table with left border for better WeChat editor compatibility
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:16px 0;">'
            f'<tr><td style="background-color:{bg_color};padding:16px 20px;border-left:4px solid {border_color};border-radius:0 8px 8px 0;">'
            f'<p style="color:{text_color};font-size:15px;line-height:1.8;margin:0;font-style:italic;">{text}</p>'
            f'</td></tr></table>'
        )

    def _convert_list(self, list_structure: List, is_ordered: bool, is_reference: bool = False) -> str:
        """Convert list structure to HTML with improved styling."""
        tag = 'ol' if is_ordered else 'ul'

        # Get text color from config
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')

        style = f'margin:16px 0;padding-left:28px;color:{text_color};' + ('font-size:0.85em;color:#888888;' if is_reference else '')

        items_html = []
        for text, nested, nested_ordered in list_structure:
            item_text = self._inline_format(text)

            if nested:
                nested_html = self._convert_list(nested, nested_ordered, is_reference)
                items_html.append(f'<li style="margin:10px 0;line-height:1.8;font-size:15px;">{item_text}{nested_html}</li>')
            else:
                items_html.append(f'<li style="margin:10px 0;line-height:1.8;font-size:15px;">{item_text}</li>')

        return f'<{tag} style="{style}">{"".join(items_html)}</{tag}>'

    def _convert_table(self, table_rows: List[Tuple[List[str], bool]], alignments: List[str], is_reference: bool = False) -> str:
        """Convert table to HTML with improved styling."""
        if not table_rows:
            return ""

        # Get styles from config
        header_bg = getattr(self.style_config, 'table_header_bg_color', '#F1F3F5')
        border_color = getattr(self.style_config, 'table_border_color', '#DEE2E6')
        text_color = getattr(self.style_config, 'paragraph_color', '#333333')

        # Build table HTML
        header_html = ''
        body_html = ''

        for idx, (cells, is_header) in enumerate(table_rows):
            row_cells = []
            row_bg = '#FFFFFF' if idx % 2 == 0 else '#F8F9FA'  # Zebra striping

            for col_idx, cell in enumerate(cells):
                align = alignments[col_idx] if col_idx < len(alignments) else 'left'
                cell_text = self._inline_format(cell)
                align_style = f'text-align:{align};'
                padding = 'padding:12px 16px;'
                border = f'border:1px solid {border_color};'

                if is_header:
                    style = f'{padding}{border}{align_style}background-color:{header_bg};font-weight:bold;color:{text_color};font-size:15px;'
                    row_cells.append(f'<th style="{style}">{cell_text}</th>')
                else:
                    style = f'{padding}{border}{align_style}background-color:{row_bg};color:{text_color};font-size:14px;line-height:1.6;'
                    row_cells.append(f'<td style="{style}">{cell_text}</td>')

            row_html = f'<tr>{"".join(row_cells)}</tr>'
            if is_header:
                header_html = row_html
            else:
                body_html += row_html

        # Combine with rounded corners container
        table_content = '<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;">'
        if header_html:
            table_content += f'<thead>{header_html}</thead>'
        if body_html:
            table_content += f'<tbody>{body_html}</tbody>'
        table_content += '</table>'

        # Wrap in container for better styling
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0;">'
            f'<tr><td style="border-radius:8px;overflow:hidden;border:1px solid {border_color};">'
            f'{table_content}'
            f'</td></tr></table>'
        )

    def _inline_format(self, text: str) -> str:
        """Apply inline formatting (bold, italic, code, links)."""
        # Handle Markdown escape sequences first (before HTML escaping)
        # \# -> #, \* -> *, \_ -> _, etc.
        text = re.sub(r'\\([\#\*\_\[\]\(\)\`\\])', r'\1', text)
        # Handle HTML entities like &#x20; (space), &#x27; (')
        text = html.unescape(text)

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
        # Use rounded corners and better colors from config
        inline_code_bg = getattr(self.style_config, 'inline_code_bg_color', '#F1F3F5')
        inline_code_color = getattr(self.style_config, 'inline_code_text_color', '#E83E8C')

        def code_replace(match):
            code = match.group(1)
            return f'<code style="background-color:{inline_code_bg};padding:2px 6px;border-radius:3px;font-family:SF Mono,Monaco,monospace;font-size:0.9em;color:{inline_code_color};font-weight:500;">{code}</code>'
        text = re.sub(r'`([^`]+)`', code_replace, text)

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

    def _generate_html(self, title: str, date: str, tags: List[str], body_html: str, source: str) -> str:
        """Generate complete HTML document using table-based layout for WeChat editor compatibility."""
        parts = []

        # Build header using table with background in style attribute (not bgcolor)
        # WeChat editor filters bgcolor attribute but supports style background-color
        if title:
            header_bg = self.style_config.header_bg_color
            parts.append(
                f'<table width="100%" cellpadding="20" cellspacing="0" border="0" '
                f'style="margin-bottom:16px;background-color:{header_bg};">'
                f'<tr><td style="color:{self.style_config.header_text_color};'
                f'font-size:{self.style_config.header_font_size};font-weight:bold;">'
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

        # Return content directly without outer table wrapper
        # WeChat editor may render empty table cells with borders
        full_html = "".join(parts)

        return full_html
