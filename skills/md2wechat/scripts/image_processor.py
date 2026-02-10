"""Image processing and upload handler."""

import re
from pathlib import Path
from typing import Optional

try:
    from .wechat_client import WeChatAPIClient
except ImportError:
    from wechat_client import WeChatAPIClient


class ImageProcessor:
    """Process and upload images in content."""

    def __init__(self, client: WeChatAPIClient, base_path: Path):
        self.client = client
        self.base_path = base_path
        self.uploaded_media_ids: list[str] = []

    def process_content(self, html_content: str) -> tuple[str, list[str]]:
        """Find and upload all images in HTML content."""
        img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)

        def replace_image(match):
            full_tag = match.group(0)
            src = match.group(1)

            # Skip data URIs and already-uploaded images
            if src.startswith(("data:", "https://mmbiz.qpic.cn", "https://mmbiz.qlogo.cn")):
                return full_tag

            if not src or not src.strip():
                return full_tag

            try:
                print(f"  Uploading image: {src[:50]}...")

                if src.startswith(("http://", "https://")):
                    result = self.client.upload_image_from_url(src)
                else:
                    img_path = self.base_path / src
                    if not img_path.exists():
                        print(f"Warning: Image not found: {img_path}")
                        return full_tag
                    result = self.client.upload_image(str(img_path))

                media_id = result.get("media_id")
                wechat_url = result.get("url", "")

                if not media_id:
                    print(f"Warning: No media_id returned for image: {src}")
                    return full_tag

                self.uploaded_media_ids.append(media_id)

                # Replace src with WeChat URL
                src_escaped = re.escape(src)
                if wechat_url:
                    new_tag = re.sub(
                        rf'src=["\']{src_escaped}["\']',
                        f'src="{wechat_url}"',
                        full_tag
                    )
                    print(f"    ✓ Uploaded, URL: {wechat_url[:50]}...")
                else:
                    new_tag = full_tag

                return new_tag

            except Exception as e:
                print(f"Warning: Failed to process image {src}: {e}")
                return match.group(0)

        result_html = img_pattern.sub(replace_image, html_content)
        return result_html, self.uploaded_media_ids

    def upload_cover(self, cover_path: Optional[str]) -> Optional[str]:
        """Upload cover image and return media_id."""
        if not cover_path:
            return None

        try:
            print(f"Uploading cover image...")

            if cover_path.startswith(("http://", "https://")):
                result = self.client.upload_image_from_url(cover_path)
            else:
                result = self.client.upload_image(cover_path)

            media_id = result.get("media_id")
            if media_id:
                print(f"  ✓ Cover uploaded: {media_id[:20]}...")
                return media_id

        except Exception as e:
            print(f"Warning: Failed to upload cover image: {e}")

        return None
