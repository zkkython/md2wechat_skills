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
            # Validate credentials before creating client
            self.config.validate_credentials()
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

        try:
            with open(path, "rb") as f:
                result = self.client.material.add("image", f)
                return result
        except WeChatClientException as e:
            errcode = getattr(e, 'errcode', None)
            if errcode == 40001:
                raise WeChatClientException(
                    errcode=40001,
                    errmsg="图片上传失败：AppSecret 无效。请检查 .env 文件中的 WECHAT_APP_SECRET 是否正确。"
                )
            raise

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
            errcode = getattr(e, 'errcode', None)
            errmsg = getattr(e, 'errmsg', str(e))

            # Error 40001: AppSecret 无效
            if errcode == 40001:
                raise WeChatClientException(
                    errcode=40001,
                    errmsg=(
                        "AppSecret 无效 (errcode 40001)。可能原因：\n"
                        "1. WECHAT_APP_SECRET 不正确\n"
                        "2. AppSecret 已被重置（重新生成后旧 Secret 会失效）\n"
                        "3. 使用了 AppID 而不是 AppSecret\n\n"
                        "解决方法：\n"
                        "1. 登录 mp.weixin.qq.com\n"
                        "2. 设置 → 开发 → 基本配置\n"
                        "3. 重置 AppSecret（重置后需立即更新 .env 文件）\n"
                        "4. 确保使用的是 AppSecret，不是 AppID"
                    )
                )

            # Error 40013: AppID 无效
            if errcode == 40013:
                raise WeChatClientException(
                    errcode=40013,
                    errmsg=(
                        "AppID 无效 (errcode 40013)。可能原因：\n"
                        "1. WECHAT_APPID 不正确\n"
                        "2. AppID 格式错误\n\n"
                        "AppID 应以 wx 开头，例如：wx1234567890abcdef"
                    )
                )

            # Error 40164: IP 不在白名单
            if errcode == 40164:
                raise WeChatClientException(
                    errcode=40164,
                    errmsg=(
                        "当前服务器 IP 不在白名单中 (errcode 40164)。\n\n"
                        "解决方法：\n"
                        "1. 登录 mp.weixin.qq.com\n"
                        "2. 设置 → 开发 → 基本配置 → IP 白名单\n"
                        "3. 添加当前服务器 IP 地址"
                    )
                )

            # Error 404: API 路径不存在
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
