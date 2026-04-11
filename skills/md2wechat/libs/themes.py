"""Theme loading and validation for md2wechat."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, fields
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class StyleConfig:
    """Style configuration for WeChat HTML output."""

    name: str
    header_bg_color: str = "#3C3C3C"
    header_text_color: str = "#FFFFFF"
    header_font_size: str = "20px"
    card_bg_color: str = "#FFFFFF"
    card_border_color: str = "#D9D9D9"
    card_text_color: str = "#333333"
    h2_h3_card_bg_color: str = "#FAFAFA"
    h2_h3_card_border_color: str = "#E8E8E8"
    h2_title_line_color: str = "#333333"
    h2_title_text_color: str = "#333333"
    h2_title_font_size: str = "18px"
    h3_title_bg_color: str = "#F5F5F5"
    h3_title_border_color: str = "#3C3C3C"
    h3_title_text_color: str = "#333333"
    h3_title_font_size: str = "16px"
    code_bg_color: str = "#F8F9FA"
    code_border_color: str = "#E9ECEF"
    code_text_color: str = "#212529"
    inline_code_bg_color: str = "#F1F3F5"
    inline_code_text_color: str = "#E83E8C"
    paragraph_font_size: str = "13px"
    paragraph_line_height: str = "1"
    paragraph_color: str = "#333333"
    blockquote_bg_color: str = "#F8F9FA"
    blockquote_border_color: str = "#DEE2E6"
    blockquote_text_color: str = "#6C757D"
    table_header_bg_color: str = "#F1F3F5"
    table_border_color: str = "#DEE2E6"
    link_color: str = "#0066CC"
    meta_text_color: str = "#888888"
    meta_font_size: str = "12px"
    source_text_color: str = "#999999"
    source_font_size: str = "12px"


class ThemeRegistry:
    """Load theme definitions from YAML files and expose lookup helpers."""

    GROUP_FIELDS = {
        "header": {"bg_color", "text_color", "font_size"},
        "card": {"bg_color", "border_color", "text_color"},
        "h2_h3_card": {"bg_color", "border_color"},
        "h2_title": {"line_color", "text_color", "font_size"},
        "h3_title": {"bg_color", "border_color", "text_color", "font_size"},
        "code": {"bg_color", "border_color", "text_color"},
        "inline_code": {"bg_color", "text_color"},
        "paragraph": {"font_size", "line_height", "color"},
        "blockquote": {"bg_color", "border_color", "text_color"},
        "table": {"header_bg_color", "border_color"},
        "link": {"color"},
        "meta": {"text_color", "font_size"},
        "source": {"text_color", "font_size"},
    }

    def __init__(self, theme_source: Optional[Path] = None):
        self.theme_source = theme_source or self._default_theme_dir()
        self._themes: Optional[dict[str, StyleConfig]] = None

    def list_themes(self) -> dict[str, StyleConfig]:
        if self._themes is None:
            self._themes = self._load_themes()
        return self._themes

    def get_theme(self, name: str) -> StyleConfig:
        themes = self.list_themes()
        if name not in themes:
            available = ", ".join(sorted(themes.keys()))
            raise ValueError(f"Unknown style: {name}. Available: [{available}]")
        return themes[name]

    def theme_exists(self, name: str) -> bool:
        return name in self.list_themes()

    def get_theme_names(self) -> dict[str, str]:
        return {name: config.name for name, config in self.list_themes().items()}

    def _default_theme_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "themes"

    def _load_themes(self) -> dict[str, StyleConfig]:
        source = self.theme_source
        if not source.exists():
            raise FileNotFoundError(f"Theme source not found: {source}")

        if source.is_file():
            return {source.stem: self._load_theme_file(source)}

        theme_files = sorted(
            path for path in source.iterdir()
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        )
        if not theme_files:
            raise ValueError(f"No theme YAML files found in: {source}")

        themes: dict[str, StyleConfig] = {}
        for theme_file in theme_files:
            theme_name = theme_file.stem
            if theme_name in themes:
                raise ValueError(f"Duplicate theme name '{theme_name}' from file: {theme_file}")
            themes[theme_name] = self._load_theme_file(theme_file)

        return themes

    def _load_theme_file(self, theme_file: Path) -> StyleConfig:
        with open(theme_file, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f) or {}

        if not isinstance(raw_config, dict) or not raw_config:
            raise ValueError(f"Theme file must define a non-empty mapping: {theme_file}")

        return self._build_style_config(theme_file.stem, raw_config)

    def _build_style_config(self, theme_name: str, raw_config: Any) -> StyleConfig:
        if not isinstance(raw_config, dict):
            raise ValueError(f"Theme '{theme_name}' must be a mapping")

        flat_config = self._flatten_theme_config(theme_name, raw_config)

        values: dict[str, Any] = {}
        for field in fields(StyleConfig):
            if field.name in flat_config:
                value = flat_config[field.name]
            elif field.default is not MISSING:
                value = field.default
            else:
                raise ValueError(f"Theme '{theme_name}' is missing required field '{field.name}'")

            if not isinstance(value, str):
                raise ValueError(
                    f"Theme '{theme_name}' field '{field.name}' must be a string, got {type(value).__name__}"
                )
            values[field.name] = value

        return StyleConfig(**values)

    def _flatten_theme_config(self, theme_name: str, raw_config: dict[str, Any]) -> dict[str, str]:
        flat_config: dict[str, str] = {}

        for key, value in raw_config.items():
            if key == "name":
                flat_config[key] = value
                continue

            if key not in self.GROUP_FIELDS:
                raise ValueError(f"Theme '{theme_name}' contains unknown group '{key}'")
            if not isinstance(value, dict):
                raise ValueError(f"Theme '{theme_name}' group '{key}' must be a mapping")

            allowed_fields = self.GROUP_FIELDS[key]
            unknown_fields = sorted(set(value.keys()) - allowed_fields)
            if unknown_fields:
                raise ValueError(
                    f"Theme '{theme_name}' group '{key}' contains unknown fields: {', '.join(unknown_fields)}"
                )

            for child_key, child_value in value.items():
                flat_config[f"{key}_{child_key}"] = child_value

        return flat_config


_REGISTRY = ThemeRegistry()


def get_theme_registry() -> ThemeRegistry:
    return _REGISTRY


def get_available_styles() -> dict[str, str]:
    return get_theme_registry().get_theme_names()


def get_default_style() -> StyleConfig:
    return get_theme_registry().get_theme("academic_gray")


def load_themes() -> dict[str, StyleConfig]:
    return get_theme_registry().list_themes()
