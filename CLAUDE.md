# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **WeChat Official Account Article Publisher** - a tool to publish Markdown or HTML articles to WeChat Official Account (微信公众号) drafts via API. It is designed as a Claude AI skill located in `skills/md2wechat/`.

## Development Commands

### Testing
```bash
python test_official_api.py
```

### Setup
```bash
# Install dependency
pip install wechatpy

# Configure credentials
cp .env.example .env
# Edit .env with WECHAT_APPID and WECHAT_APP_SECRET
```

### Usage
```bash
# Publish from markdown
python skills/md2wechat/scripts/publish.py --markdown /path/to/article.md

# Publish from HTML
python skills/md2wechat/scripts/publish.py --html /path/to/article.html

# With options
python skills/md2wechat/scripts/publish.py --markdown article.md --type newspic
```

## Architecture

### Content Processing Pipeline
```
Markdown/HTML File → Parser → Image Processing → API Client → WeChat Draft
```

### Key Components

**`skills/md2wechat/scripts/publish.py`** - CLI entry point

**`skills/md2wechat/scripts/publisher.py`** - Main publish orchestrator
- `ArticlePublisher` - Coordinates parsing, image processing, and API calls
- `publish()` - Main method to publish articles from files

**`skills/md2wechat/scripts/parsers.py`** - Content parsers
- `MarkdownParser` - Parses markdown files with WeChat-compatible HTML output
- `HTMLParser` - Parses existing HTML files
- `ParserRegistry` - Plugin system for adding new parsers

**`skills/md2wechat/scripts/image_processor.py`** - Image handling
- `ImageProcessor` - Uploads images to WeChat and replaces URLs

**`skills/md2wechat/scripts/wechat_client.py`** - WeChat API wrapper
- `WeChatAPIClient` - Wraps wechatpy SDK for upload and draft operations

**`skills/md2wechat/scripts/config.py`** - Configuration
- `Config` - Loads WECHAT_APPID and WECHAT_APP_SECRET from .env

**`test_official_api.py`** - Test suite covering all modules

### Image Handling Strategy
- Local images: resolved relative to source file, uploaded via `material.add("image", f)`
- Remote URLs: downloaded to temp file, then uploaded
- Cover image: first image in content auto-extracted if not specified
- WeChat media URLs use format: `https://mmbiz.qpic.cn/mmbiz_jpg/{media_id}`

### API Authentication
- Credentials loaded from `.env` file (searches up to 5 parent directories)
- Uses `WeChatClient(appid, app_secret)` from wechatpy
- Access tokens auto-managed by wechatpy
- Draft API endpoint: `POST draft/add`

### Article Types
- `news` (default): Standard WeChat article with full HTML support
- `newspic` (小绿书): Image-focused format, max 20 images, text limited to 1000 chars

### Critical Constraints
- Title max 64 characters (enforced by truncation)
- Cover image is **required** - API call fails without it
- Only verified WeChat Official Accounts can use the draft API
- Code blocks converted to `<table>` with bgcolor for WeChat editor compatibility
- Tables converted to text representation (WeChat doesn't support `<table>` for data)

## Configuration

Environment variables in `.env`:
- `WECHAT_APPID` - From mp.weixin.qq.com → Settings → Development → Basic Configuration
- `WECHAT_APP_SECRET` - Same location

## Error Handling Patterns

The API client returns structured results:
```python
{"success": True, "data": {"media_id": "...", "status": "published"}}
{"success": False, "error": "...", "code": "..."}
```

Common error codes from WeChat:
- `MISSING_COVER_IMAGE` - No cover image provided
- `40001` - Invalid credentials (check AppID/Secret)
- `404` - Draft API unavailable (account not verified)
