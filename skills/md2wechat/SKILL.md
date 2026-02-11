---
name: md2wechat
description: Publish Markdown/HTML articles to WeChat Official Account (微信公众号) drafts via API with multiple visual styles
---

# WeChat Article Publisher

Publish Markdown or HTML content to WeChat Official Account drafts via API, with automatic format conversion and multiple visual styles.

## Prerequisites

- Python 3.9+
- **Official WeChat API (wechatpy)**
- WECHAT_APPID and WECHAT_APP_SECRET from .env file
- Get from https://mp.weixin.qq.com → Settings → Development → Basic Configuration
- Install dependency: `pip install wechatpy`

## Features

- **Multiple Visual Styles**: Choose from 4 professionally designed styles
  - `academic_gray` (默认): 学术灰风格 - 适合技术文档和学术论文
  - `festival`: 节日快乐色彩系 - 温暖红金配色，适合节日祝福
  - `tech`: 科技产品介绍色彩系 - 蓝色科技风，适合产品介绍
  - `announcement`: 重大事情告知色彩系 - 警示橙红配色，适合重要通知
- **Enhanced Markdown Rendering**: Based on MD2WeChat project
  - Code blocks with line numbers and syntax highlighting
  - Full HTML table support (not text fallback)
  - H2/H3 card-style section layouts
  - Nested lists support
  - Styled blockquotes
- **Automatic Image Upload**: Local and remote images uploaded to WeChat
- **Comment Support**: Enable/disable comments, with option for fans-only commenting

## Testing

```bash
python test_official_api.py
```

## Installation

### Method 1: PyPI Package (Standalone CLI)

```bash
pip install md2wechat

# Configure credentials
cat > .env << EOF
WECHAT_APPID=your_appid_here
WECHAT_APP_SECRET=your_app_secret_here
EOF
```

### Method 2: Source Installation (Claude Skill)

```bash
# Clone repository
git clone https://github.com/zkkython/md2wechat.git
cd md2wechat
pip install -e .

# Install as Claude skill
mkdir -p ~/.claude/skills
cp -r skills/md2wechat ~/.claude/skills/
```

## Usage

### Command Line (PyPI)

```bash
# After pip install
md2wechat --markdown /path/to/article.md
md2wechat --html /path/to/article.html

# With style option
md2wechat --markdown article.md --style tech
md2wechat --markdown article.md --style festival --type newspic
```

### Command Line (Source/Claude)

```bash
# Basic usage
python skills/md2wechat/scripts/publish.py --markdown /path/to/article.md

# With style selection
python skills/md2wechat/scripts/publish.py --markdown article.md --style tech
python skills/md2wechat/scripts/publish.py --markdown article.md --style announcement

# View all options
python skills/md2wechat/scripts/publish.py --help
```

### As Claude Skill

Once installed in `~/.claude/skills/`, use natural language:
```
Publish this markdown article to WeChat: /path/to/article.md

Use the tech style for this article
```

## Visual Styles

| Style | Description | Best For |
|-------|-------------|----------|
| `academic_gray` | 学术灰风格，简洁专业 | 技术文档、学术论文 |
| `festival` | 节日快乐色彩系，温暖红金 | 节日祝福、庆祝内容 |
| `tech` | 科技蓝配色，现代感强 | 产品介绍、科技文章 |
| `announcement` | 警示橙红配色，醒目突出 | 重要通知、公告 |

## Common Errors

### Error 40001: AppSecret 无效

**原因：**
- WECHAT_APP_SECRET 不正确
- AppSecret 已被重置（重新生成后旧 Secret 会失效）
- 使用了 AppID 而不是 AppSecret

**解决方法：**
1. 登录 [mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 设置 → 开发 → 基本配置
3. 重置 AppSecret（重置后需立即更新 .env 文件）
4. 确保使用的是 AppSecret，不是 AppID

### Error 40013: AppID 无效

**原因：**
- WECHAT_APPID 不正确
- AppID 格式错误

**解决方法：**
- AppID 应以 `wx` 开头，例如：`wx1234567890abcdef`
- 确保使用的是 AppID，不是 AppSecret

### Error 40164: IP 不在白名单

**原因：**
- 当前服务器 IP 不在微信公众平台的白名单中

**解决方法：**
1. 登录 [mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 设置 → 开发 → 基本配置 → IP 白名单
3. 添加当前服务器 IP 地址

### Error 404: 草稿箱 API 不可用

**原因：**
- 公众号未认证（仅认证服务号/订阅号可用草稿箱 API）
- API 路径错误

**解决方法：**
- 确保公众号已完成微信认证
- 检查公众号类型是否支持使用草稿箱功能

### Error 45166: 内容安全检查失败

**原因：**
- 内容包含微信不允许的 HTML（如锚点链接 `<a href="#xxx">`）
- HTML 格式嵌套错误

**解决方法：**
- 使用本工具的 Markdown 转换功能，会自动处理这些问题
- 避免手动编写包含锚点链接的 HTML

### Using in Python Code
```python
from skills.md2wechat.scripts.publisher import ArticlePublisher

publisher = ArticlePublisher()

# With default style (academic_gray)
result = publisher.publish("/path/to/article.md")

# With specific style
result = publisher.publish("/path/to/article.md", style="tech")

# With comments enabled
result = publisher.publish(
    "/path/to/article.md",
    style="tech",
    comment_enabled=True,
    fans_only_comment=False  # True = only fans can comment
)

print(result)
```

## Architecture (New Version)

The refactored version uses a modular architecture with MD2WeChat integration:

```
skills/md2wechat/
├── lib/
│   └── md2wechat/           # MD2WeChat integration (from Mapoet/MD2WeChat)
│       ├── __init__.py
│       └── converter.py     # Core Markdown to WeChat HTML converter
└── scripts/
    ├── publish.py           # CLI entry point
    ├── config.py            # Configuration management
    ├── wechat_client.py     # WeChat API client wrapper
    ├── parsers.py           # Markdown/HTML parsers (uses MD2WeChat)
    ├── image_processor.py   # Image upload handler
    └── publisher.py         # Main publish orchestrator
```

### Markdown Processing Pipeline

```
Markdown File → MD2WeChat Converter → Styled HTML → Image Upload → WeChat Draft
```

The MD2WeChat converter provides:
- **Front Matter Support**: YAML front matter for title, date, tags
- **Code Blocks**: Syntax highlighting with line numbers
- **Tables**: Full HTML table rendering with alignment
- **Lists**: Nested ordered/unordered lists
- **Typography**: Bold, italic, inline code, links, blockquotes
- **Styling**: 4 built-in visual themes

## Workflow

**Strategy: "API-First Publishing"**

Unlike browser-based publishing, this skill uses direct API calls for reliable, fast publishing.

1. Load WECHAT_APPID and WECHAT_APP_SECRET from .env file
2. Parse Markdown with MD2WeChat converter (apply selected style)
3. Upload images to WeChat media server
4. Call draft/add API to create draft in WeChat
5. Report success with draft details

**Supported File Formats:**
- `.md` files → Parsed by MD2WeChat, styled HTML output
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

**Publish Markdown with style:**
```bash
python skills/md2wechat/scripts/publish.py \
  --markdown /path/to/article.md \
  --style tech
```

**Available options:**
```bash
python skills/md2wechat/scripts/publish.py \
  --markdown article.md \
  --style academic_gray|festival|tech|announcement \
  --type news|newspic \
  --title "Custom Title" \
  --author "Author Name"

# Enable comments
python skills/md2wechat/scripts/publish.py \
  --markdown article.md \
  --comment

# Enable comments (fans only)
python skills/md2wechat/scripts/publish.py \
  --markdown article.md \
  --comment --fans-only-comment
```

**Features:**
- Automatic image upload (local paths and URLs)
- No `--appid` needed (uses WECHAT_APPID from .env)
- Direct connection to WeChat servers
- Multiple visual styles

## API Reference

### Official WeChat API (wechatpy)

Uses `wechatpy` SDK to call official WeChat APIs directly.

**Authentication:** AppID + AppSecret → Access Token (auto-managed by wechatpy)

**Key APIs Used:**
- `POST /cgi-bin/token` - Get access token
- `POST /cgi-bin/media/upload` - Upload images
- `POST /cgi-bin/draft/add` - Create draft

See: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html

### MD2WeChat Converter

Based on https://github.com/Mapoet/MD2WeChat (MIT License)

**Features:**
- Front matter parsing (title, date, tags)
- Code blocks with line numbers
- Full table support
- Nested lists
- 4 visual styles

## Critical Rules

1. **NEVER auto-publish** - Only save to drafts, user publishes manually
2. **Validate credentials first** - Fail fast if WECHAT_APPID/WECHAT_APP_SECRET not configured
3. **Handle errors gracefully** - Show clear error messages
4. **Preserve original content** - Don't modify user's markdown unnecessarily

## Supported Formats

### Markdown Files (.md)

- YAML Front Matter (`---`):
  - `title`: Article title
  - `date`: Publication date
  - `tags`: List of tags
  - `permalink`: Source URL
- H1 header (# ) → Article title
- H2/H3 headers (##, ###) → Card-style section headers
- Bold (**text**)
- Italic (*text*)
- Links [text](url) → Anchor links removed, external links preserved
- Blockquotes (> )
- Inline code (`` `code` ``) → Styled inline
- Code blocks (``` ... ```) → With line numbers
- Lists (- or 1.) → Nested supported
- Tables (| col | col |) → Full HTML tables
- Images ![alt](url) → Auto-uploaded

### HTML Files (.html)
- `<title>` or `<h1>` → Article title
- All HTML formatting preserved
- `<img>` tags → Images auto-uploaded
- First `<p>` → Auto-extracted as summary

## Article Types

### news (普通文章)
- Standard WeChat article format
- Full Markdown/HTML support
- Rich text with images

### newspic (小绿书/图文消息)
- Image-focused format (like Instagram posts)
- Maximum 20 images extracted from content
- Text content limited to 1000 characters

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
4. **Portability**: Works on any system with Python

### Content Guidelines

1. **Images**: Use public URLs when possible; local images will be uploaded
2. **Title**: Keep under 64 characters
3. **Summary**: Auto-extracted from first paragraph if not provided
4. **Cover**: First image in markdown becomes cover if not specified
5. **Style Selection**:
   - Use `academic_gray` for technical content
   - Use `tech` for product announcements
   - Use `festival` for holiday greetings
   - Use `announcement` for important notices

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

#### Q: "Error: invalid content hint (45166)"?
A: This error occurs when:
- HTML contains anchor links (`<a href="#xxx">`)
- HTML structure is invalid

Our MD2WeChat converter automatically handles these issues. Make sure you're using the latest version.

#### Q: Which style should I use?
A:
- **academic_gray**: Technical documentation, research papers
- **tech**: Product launches, tech blogs
- **festival**: Holiday greetings, celebrations
- **announcement**: Important notices, urgent updates

### General

#### Q: Images not showing in WeChat?
A: Ensure images are accessible URLs. Local images are auto-uploaded but may fail if path is incorrect.

#### Q: Title is too long?
A: WeChat limits titles to 64 characters. The script will use the first 64 chars.

#### Q: What's the difference between news and newspic?
A: `news` is standard article format; `newspic` (小绿书) is image-focused with limited text.

## Credits

- **MD2WeChat Integration**: Based on [Mapoet/MD2WeChat](https://github.com/Mapoet/MD2WeChat) (MIT License)
- **WeChat API**: Uses [wechatpy](https://github.com/wechatpy/wechatpy) SDK
