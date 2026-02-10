"""WeChat API client wrapper."""

import tempfile
from pathlib import Path
from typing import Optional

import requests
from wechatpy import WeChatClient
from wechatpy.exceptions import WeChatClientException

try:
    from .config import Config
except ImportError:
    from config import Config


class WeChatAPIClient:
    """Wrapper for WeChat API operations."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._client: Optional[WeChatClient] = None

    @property
    def client(self) -> WeChatClient:
        """Get or create WeChat client."""
        if self._client is None:
            self._client = WeChatClient(
                self.config.appid,
                self.config.app_secret
            )
        return self._client

    def upload_image(self, image_path: str) -> dict:
        """Upload local image to WeChat and return media info."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(path, "rb") as f:
            result = self.client.material.add("image", f)
            return result

    def upload_image_from_url(self, url: str) -> dict:
        """Download image from URL and upload to WeChat."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Determine file extension
        content_type = response.headers.get("content-type", "")
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "png" in content_type:
            ext = ".png"
        elif "gif" in content_type:
            ext = ".gif"
        else:
            ext = ".jpg"

        # Save to temp file and upload
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            return self.upload_image(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def create_draft(self, article: dict) -> dict:
        """Create a draft article."""
        try:
            result = self.client.post(
                "draft/add",
                data={"articles": [article]}
            )
            return result
        except WeChatClientException as e:
            response = getattr(e, 'response', None)
            if response and response.status_code == 404:
                raise WeChatClientException(
                    errcode=404,
                    errmsg="草稿箱API不可用。可能原因：\n"
                           "1. 公众号未认证（仅认证服务号/订阅号可用）\n"
                           "2. API路径错误\n"
                           "3. 微信版本过旧"
                )
            raise
