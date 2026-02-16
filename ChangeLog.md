# ChangeLog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed

- **H1 headings missing in converted HTML** - Fixed a bug in `skills/md2wechat/libs/converter.py` where H1 headings (and H4+ headings) were being dropped during Markdown to HTML conversion. The `_convert_section` method's non-card content handling branch was missing the `heading` item type, causing all H1 titles to be lost in the output.
  - Affected: `_convert_section()` method in `converter.py`
  - Root cause: Missing `elif item_type == 'heading'` handler in the else branch (line 866+)
  - Fix: Added heading type handling to properly convert H1-H6 headings outside of card sections

## [2.0.0] - 2025-02-16

### Added

- Initial release of md2wechat
- WeChat Official Account draft API integration
- 4 visual styles: academic_gray, festival, tech, announcement
- Markdown to WeChat HTML conversion
- Image upload and processing
- Comment support with fans-only option
