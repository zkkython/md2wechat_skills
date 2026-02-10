---
name: md2wechat
description: Publish Markdown/HTML articles to WeChat Official Account (微信公众号) drafts via API
---

# WeChat Article Publisher

Publish Markdown or HTML content to WeChat Official Account drafts via API, with automatic format conversion.

## Prerequisites

- Python 3.9+
- **Official WeChat API (wechatpy)**
- WECHAT_APPID and WECHAT_APP_SECRET from .env file
- Get from https://mp.weixin.qq.com → Settings → Development → Basic Configuration
- Install dependency: `pip install wechatpy`

## Testing

```bash
python test_official_api.py
```

## Scripts

Located in `~/.claude/skills/md2wechat/scripts/`:

### publish.py (Recommended)
Refactored modular version with cleaner architecture:
```bash
# Publish from markdown file
python skills/md2wechat/scripts/publish.py --markdown /path/to/article.md

# Publish from HTML file
python skills/md2wechat/scripts/publish.py --html /path/to/article.html

# With options
python skills/md2wechat/scripts/publish.py --markdown article.md --type newspic
```

### Using as Python Module
```bash
# Run as a module
python -m skills.md2wechat.scripts.publish --markdown article.md
```

### Using in Python Code
```python
from skills.md2wechat.scripts.publisher import ArticlePublisher

publisher = ArticlePublisher()
result = publisher.publish("/path/to/article.md")
print(result)
```

## Architecture (New Version)

The refactored version uses a modular architecture:

```
scripts/
├── publish.py           # CLI entry point
├── config.py            # Configuration management
├── wechat_client.py     # WeChat API client wrapper
├── parsers.py           # Markdown/HTML parsers
├── image_processor.py   # Image upload handler
└── publisher.py         # Main publish orchestrator
```

### Extending with Custom Parsers

```python
from skills.md2wechat.scripts.parsers import ContentParser, ParseResult, ParserRegistry

class WordParser(ContentParser):
    def supports(self, filepath: str) -> bool:
        return filepath.endswith('.docx')

    def parse(self, filepath: str) -> ParseResult:
        # Your parsing logic
        return ParseResult(title="...", content="...")

# Register the parser
from skills.md2wechat.scripts.publisher import ArticlePublisher
publisher = ArticlePublisher()
publisher.parser_registry.register(WordParser())
```

## Workflow

**Strategy: "API-First Publishing"**

Unlike browser-based publishing, this skill uses direct API calls for reliable, fast publishing.

1. Load WECHAT_APPID and WECHAT_APP_SECRET from .env file
2. Detect file format (Markdown or HTML) and parse accordingly
3. Upload images to WeChat media server
4. Call draft/add API to create draft in WeChat
5. Report success with draft details

**Supported File Formats:**
- `.md` files → Parsed as Markdown, converted by WeChat API
- `.html` files → Sent as HTML, formatting preserved

## Step-by-Step Guide

### Using Official API (wechatpy) - Recommended for Own Account

#### Step 1: Configure Credentials

```bash
# Edit .env file with your WeChat App credentials
cat > .env << EOF
WECHAT_APPID=your_appid_here
WECHAT_APP_SECRET=your_app_secret_here
EOF
```

Get credentials from: https://mp.weixin.qq.com → Settings → Development → Basic Configuration

#### Step 2: Publish Article

**Publish Markdown:**
```bash
python skills/md2wechat/scripts/wechat_official_api.py publish \
  --markdown /path/to/article.md
```

**Publish HTML:**
```bash
python skills/md2wechat/scripts/wechat_official_api.py publish \
  --html /path/to/article.html
```

**Features:**
- Automatic image upload (local paths and URLs)
- No `--appid` needed (uses WECHAT_APPID from .env)
- Direct connection to WeChat servers

## API Reference

### Official WeChat API (wechatpy)

Uses `wechatpy` SDK to call official WeChat APIs directly.

**Authentication:** AppID + AppSecret → Access Token (auto-managed by wechatpy)

**Key APIs Used:**
- `POST /cgi-bin/token` - Get access token
- `POST /cgi-bin/media/upload` - Upload images
- `POST /cgi-bin/draft/add` - Create draft

See: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html

## Critical Rules

1. **NEVER auto-publish** - Only save to drafts, user publishes manually
2. **Validate credentials first** - Fail fast if WECHAT_APPID/WECHAT_APP_SECRET not configured
3. **Handle errors gracefully** - Show clear error messages
4. **Preserve original content** - Don't modify user's markdown unnecessarily

## Supported Formats

### Markdown Files (.md)
- H1 header (# ) → Article title
- H2/H3 headers (##, ###) → Section headers
- Bold (**text**)
- Italic (*text*)
- Links [text](url)
- Blockquotes (> )
- Code blocks (``` ... ```)
- Lists (- or 1.)
- Images ![alt](url) → Auto-uploaded to WeChat

### HTML Files (.html)
- `<title>` or `<h1>` → Article title
- All HTML formatting preserved (styles, tables, etc.)
- `<img>` tags → Images auto-uploaded to WeChat
- First `<p>` → Auto-extracted as summary
- Supports inline styles and rich formatting

**HTML Title Extraction Priority:**
1. `<title>` tag content
2. First `<h1>` tag content
3. "Untitled" as fallback

**HTML Content Extraction:**
- If `<body>` exists, uses body content
- Otherwise, strips `<html>`, `<head>`, `<!DOCTYPE>` and uses remaining content

## Article Types

### news (普通文章)
- Standard WeChat article format
- Full Markdown/HTML support
- Rich text with images

### newspic (小绿书/图文消息)
- Image-focused format (like Instagram posts)
- Maximum 20 images extracted from content
- Text content limited to 1000 characters
- Images auto-uploaded to WeChat


## Error Handling

### appsecret is invalid (errcode: 40001)
**Cause**: Invalid credentials or IP not whitelisted
**Solution**: Check WECHAT_APPID and WECHAT_APP_SECRET are correct, and add your server IP to the whitelist in mp.weixin.qq.com

### Missing Cover Image
**Cause**: Article has no images for cover
**Solution**: Add at least one image to the article (e.g., `![alt](image.jpg)`)

### Draft API Unavailable (404)
**Cause**: Account not verified or API permission not granted
**Solution**: Ensure the WeChat account is verified (认证的服务号/订阅号 required for draft API)

### WeChatClientException
**Cause**: Various WeChat API errors
**Solution**: Check the error message and errcode; refer to https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Global_Return_Code.html

## Best Practices

### Why use API instead of browser automation?

1. **Reliability**: Direct API calls are more stable than browser automation
2. **Speed**: No browser startup, page loading, or UI interactions
3. **Simplicity**: Single command to publish
4. **Portability**: Works on any system with Python (no macOS-only dependencies)

### Content Guidelines

1. **Images**: Use public URLs when possible; local images will be uploaded
2. **Title**: Keep under 64 characters
3. **Summary**: Auto-extracted from first paragraph if not provided
4. **Cover**: First image in markdown becomes cover if not specified

## Troubleshooting

### Official API (wechatpy)

#### Q: How do I get WECHAT_APPID and WECHAT_APP_SECRET?
A:
1. Login to https://mp.weixin.qq.com
2. Go to Settings → Development → Basic Configuration
3. Copy AppID and generate AppSecret
4. Add IP whitelist if needed

#### Q: "Error: appsecret is invalid"?
A: Check that:
- AppSecret is correct (will be reset if regenerated)
- Your server IP is in the whitelist
- The account is verified (required for draft API)

#### Q: Which API should I use?
A:
- **Use Official API (wechatpy)** if publishing to your own account - more direct, no third-party dependency


### General

#### Q: Images not showing in WeChat?
A: Ensure images are accessible URLs. Local images are auto-uploaded but may fail if path is incorrect.

#### Q: Title is too long?
A: WeChat limits titles to 64 characters. The script will use the first 64 chars of H1.

#### Q: What's the difference between news and newspic?
A: `news` is standard article format; `newspic` (小绿书) is image-focused with limited text.
