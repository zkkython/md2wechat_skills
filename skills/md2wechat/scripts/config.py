"""Configuration management for md2wechat."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration manager for WeChat API credentials."""

    def __init__(self, env_path: Optional[str] = None):
        self._appid: Optional[str] = None
        self._app_secret: Optional[str] = None
        self._load_env_file(env_path)

    def _load_env_file(self, env_path: Optional[str] = None) -> None:
        """Load environment variables from .env file."""
        if env_path:
            env_file = Path(env_path)
        else:
            current = Path.cwd()
            env_file = None
            for _ in range(5):
                candidate = current / ".env"
                if candidate.exists():
                    env_file = candidate
                    break
                current = current.parent

        if env_file and env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value:
                            os.environ.setdefault(key, value)

    @property
    def appid(self) -> str:
        """Get WeChat AppID."""
        if self._appid is None:
            self._appid = os.environ.get("WECHAT_APPID")
            if not self._appid:
                raise ValueError(
                    "WECHAT_APPID not found. Please set it in .env file or environment variable.\n"
                    "Example: echo 'WECHAT_APPID=wx1234567890abcdef' > .env"
                )
        return self._appid

    @property
    def app_secret(self) -> str:
        """Get WeChat AppSecret."""
        if self._app_secret is None:
            self._app_secret = os.environ.get("WECHAT_APP_SECRET")
            if not self._app_secret:
                raise ValueError(
                    "WECHAT_APP_SECRET not found. Please set it in .env file or environment variable.\n"
                    "Example: echo 'WECHAT_APP_SECRET=your_secret_here' >> .env"
                )
        return self._app_secret

    def validate_credentials(self) -> None:
        """Validate that credentials are set and have correct format."""
        appid = self.appid
        app_secret = self.app_secret

        # Check AppID format (typically 18 characters, starts with wx)
        if not appid.startswith("wx") and not appid.startswith("gh"):
            print(f"Warning: WECHAT_APPID '{appid[:6]}...' doesn't start with 'wx' or 'gh'")
            print("Make sure you're using the correct AppID from mp.weixin.qq.com")

        # Check AppSecret length (typically 32 characters)
        if len(app_secret) < 20:
            print(f"Warning: WECHAT_APP_SECRET seems too short ({len(app_secret)} chars)")
            print("Make sure you're using the AppSecret, not the AppID")

        print(f"✓ Using AppID: {appid[:6]}...")
        print(f"✓ AppSecret loaded ({len(app_secret)} chars)")
