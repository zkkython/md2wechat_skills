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

### Option 1: Install from PyPI (Recommended for CLI usage)

```bash
# Install the package
pip install md2wechat

# Configure credentials
cat > .env << EOF
WECHAT_APPID=your_appid_here
WECHAT_APP_SECRET=your_app_secret_here
EOF
```

### Option 2: Install from Source (for Claude Skill)

```bash
# Clone the repository
git clone https://github.com/zkkython/md2wechat.git
cd md2wechat

# Install Python dependency
pip install wechatpy

# Copy skill to Claude Code skills directory (required for Claude integration)
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

## Publishing to PyPI

If you want to publish your own version to PyPI:

```bash
# Install publishing tools
pip install twine build

# Run checks (recommended before publishing)
python publish_to_pypi.py --check

# Publish to TestPyPI (for testing)
python publish_to_pypi.py --test

# Publish to Production PyPI
python publish_to_pypi.py --prod
```

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.

## Usage

### Command Line (PyPI installation)

```bash
# Publish from markdown
md2wechat publish --markdown article.md

# Publish from HTML
md2wechat publish --html article.html

# Publish as 小绿书 (image-focused format)
md2wechat publish --markdown article.md --type newspic

# With custom title
md2wechat publish --markdown article.md --title "Custom Title"
```

### Command Line (Source installation)

```bash
# Publish from markdown
python skills/md2wechat/scripts/publish.py --markdown article.md

# Publish from HTML
python skills/md2wechat/scripts/publish.py --html article.html
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
| `40001` | AppSecret 无效 | 重置 AppSecret，更新 .env 文件 |
| `40013` | AppID 无效 | AppID 应以 `wx` 开头 |
| `40164` | IP 不在白名单 | 添加服务器 IP 到白名单 |
| `404` | API 不可用 | 公众号必须认证才能使用草稿箱 |
| Missing cover | 缺少封面图片 | 文章中添加至少一张图片 |

### Detailed Error Messages

**Error 40001 (AppSecret Invalid):**
```
AppSecret 无效 (errcode 40001)。可能原因：
1. WECHAT_APP_SECRET 不正确
2. AppSecret 已被重置（重新生成后旧 Secret 会失效）
3. 使用了 AppID 而不是 AppSecret
```

**Error 40164 (IP Not in Whitelist):**
```
当前服务器 IP 不在白名单中 (errcode 40164)。
解决方法：登录 mp.weixin.qq.com → 设置 → 开发 → 基本配置 → IP 白名单
```

## License

Apache 2.0
