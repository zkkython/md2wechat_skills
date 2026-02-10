# md2wechat

Publish Markdown or HTML articles to WeChat Official Account (微信公众号) drafts via API.

## Features

- **Markdown Support**: Convert Markdown to WeChat-compatible HTML with automatic formatting
- **HTML Support**: Publish existing HTML files directly
- **Image Upload**: Automatic upload of local and remote images to WeChat's media server
- **Draft Only**: Never auto-publishes; articles are saved to drafts for manual review
- **Official API**: Uses official WeChat API via `wechatpy` SDK

## Installation

### Prerequisites

- Python 3.9+
- WeChat Official Account (verified service or subscription account)

### Install as Claude Skill

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/md2wechat.git
cd md2wechat

# Install Python dependency
pip install wechatpy

# Copy skill to Claude Code skills directory
mkdir -p ~/.claude/skills
cp -r skills/md2wechat ~/.claude/skills/

# Configure credentials
cp .env.example .env
# Edit .env with your WECHAT_APPID and WECHAT_APP_SECRET
```

### Get WeChat Credentials

1. Login to [mp.weixin.qq.com](https://mp.weixin.qq.com)
2. Go to Settings → Development → Basic Configuration
3. Copy AppID and generate AppSecret
4. Add your server IP to the whitelist

## Usage

### Command Line

```bash
# Publish from markdown
python skills/md2wechat/scripts/publish.py --markdown article.md

# Publish from HTML
python skills/md2wechat/scripts/publish.py --html article.html

# Publish as 小绿书 (image-focused format)
python skills/md2wechat/scripts/publish.py --markdown article.md --type newspic

# With custom title
python skills/md2wechat/scripts/publish.py --markdown article.md --title "Custom Title"
```

### As Claude Skill

Once installed in `~/.claude/skills/`, you can use natural language:

```
Publish this markdown article to WeChat: article.md
```

## Testing

```bash
python test_official_api.py
```

## Project Structure

```
md2wechat/
├── README.md            # This file
├── LICENSE              # Apache 2.0
├── pyproject.toml       # Python dependencies
├── .env.example         # Environment template
├── example_article.md   # Example markdown article
├── test_official_api.py # Test suite
├── CLAUDE.md            # Claude Code guidance
└── skills/md2wechat/    # Claude skill
    ├── SKILL.md         # Skill metadata & docs
    └── scripts/
        ├── __init__.py         # Package exports
        ├── __main__.py         # Module entry point
        ├── publish.py          # CLI entry point
        ├── config.py           # Configuration management
        ├── wechat_client.py    # WeChat API client wrapper
        ├── parsers.py          # Markdown/HTML parsers
        ├── image_processor.py  # Image upload handler
        └── publisher.py        # Main publish orchestrator
```

## Supported Markdown

- `# Title` → Article title (H1)
- `## Section` → Section headers
- `**bold**` → Bold text
- `*italic*` → Italic text
- `[link](url)` → Links
- `> quote` → Blockquotes
- `` `code` `` → Inline code
- ````code block```` → Code blocks (styled table with border)
- `- item` / `1. item` → Lists
- `![alt](image.jpg)` → Images (auto-uploaded)

## Article Types

| Type | Description |
|------|-------------|
| `news` (default) | Standard WeChat article |
| `newspic` | 小绿书 format - image-focused, max 20 images |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `40001` | Invalid credentials | Check AppID/AppSecret |
| Missing cover | No images in article | Add at least one image |
| `404` | API unavailable | Account must be verified |

## License

Apache 2.0
