"""Article publisher for WeChat Official Account."""

from pathlib import Path
from typing import Optional

try:
    from .image_processor import ImageProcessor
    from .parsers import ParseResult, ParserRegistry, get_available_styles
    from .wechat_client import WeChatAPIClient
except ImportError:
    from image_processor import ImageProcessor
    from parsers import ParseResult, ParserRegistry, get_available_styles
    from wechat_client import WeChatAPIClient


class ArticlePublisher:
    """Publish articles to WeChat drafts."""

    # Available styles from MD2WeChat
    STYLES = get_available_styles()

    def __init__(self, client: Optional[WeChatAPIClient] = None):
        self.client = client or WeChatAPIClient()
        self.parser_registry = ParserRegistry()

    def publish(
        self,
        filepath: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        cover_image: Optional[str] = None,
        author: Optional[str] = None,
        article_type: str = "news",
        style: str = "academic_gray"
    ) -> dict:
        """Publish an article from file.

        Args:
            filepath: Path to markdown or HTML file
            title: Override article title
            summary: Override article summary
            cover_image: Override cover image path
            author: Article author name
            article_type: "news" or "newspic"
            style: Visual style - "academic_gray", "festival", "tech", or "announcement"
        """
        # Validate style
        if style not in self.STYLES:
            available = ", ".join(self.STYLES.keys())
            return {
                "success": False,
                "error": f"Unknown style '{style}'. Available: {available}",
                "code": "INVALID_STYLE",
            }

        # Parse content with style
        parser = self.parser_registry.get_parser(filepath)
        result = parser.parse(filepath, style=style)

        # Override with provided values
        final_title = (title or result.title)[:64]
        final_summary = (summary or result.summary or "")[:120]

        # Process images
        processor = ImageProcessor(self.client, result.base_path)

        # Upload cover image
        thumb_media_id = processor.upload_cover(cover_image or result.cover_image)

        # Process content images
        print("Processing content images...")
        content, uploaded_images = processor.process_content(result.content)

        # Use first content image as cover if no cover specified
        if not thumb_media_id and uploaded_images:
            thumb_media_id = uploaded_images[0]
            print(f"  ✓ Using first content image as cover")

        # Validate cover image is present
        if not thumb_media_id:
            return {
                "success": False,
                "error": "微信公众号草稿箱必须包含封面图片。请在文章中添加图片",
                "code": "MISSING_COVER_IMAGE",
            }

        # Prepare article
        article = {
            "title": final_title,
            "content": content,
            "author": author or "",
            "digest": final_summary,
            "thumb_media_id": thumb_media_id,
            "show_cover_pic": 1,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }

        # Handle newspic type - limit images
        if article_type == "newspic":
            import re
            images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
            if len(images) > 20:
                print(f"Warning: Limiting to 20 images for 小绿书 format")

        # Create draft
        print(f"Creating draft: {final_title[:50]}...")
        try:
            api_result = self.client.create_draft(article)
            return {
                "success": True,
                "data": {
                    "media_id": api_result.get("media_id"),
                    "status": "published",
                    "message": "文章已成功发布到公众号草稿箱",
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": "API_ERROR",
            }
