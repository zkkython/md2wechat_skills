"""FastAPI backend for MD2WeChat web interface."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Add skills/md2wechat to path
SKILLS_PATH = Path(__file__).parent.parent.parent / "skills"
sys.path.insert(0, str(SKILLS_PATH))

try:
    from md2wechat.scripts.publisher import ArticlePublisher
    from md2wechat.scripts.wechat_client import WeChatAPIClient
except ImportError as e:
    raise ImportError(f"Cannot import md2wechat modules: {e}")

app = FastAPI(title="MD2WeChat API")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check if we have static files (built frontend)
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/api/health")
async def health_check():
    """Check API and WeChat credentials status."""
    publisher = ArticlePublisher()
    try:
        # Try to get access token to verify credentials
        _ = publisher.client.client.access_token
        return {"status": "ok", "wechat": "connected"}
    except Exception as e:
        return {"status": "ok", "wechat": "not_configured", "error": str(e)}


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    style: str = Form("academic_gray"),
    article_type: str = Form("news"),
    comment: bool = Form(False),
    fans_only_comment: bool = Form(False),
    author: str = Form(""),
    title: Optional[str] = Form(None),
):
    """Upload a single markdown file to WeChat."""

    if not file.filename.endswith((".md", ".markdown")):
        return {
            "success": False,
            "error": "Only .md and .markdown files are supported",
            "code": "INVALID_FILE_TYPE",
        }

    # Save uploaded file to temp directory
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Use filename (without extension) as title if not provided
    if title is None:
        title = Path(file.filename).stem

    try:
        publisher = ArticlePublisher()
        result = publisher.publish(
            filepath=tmp_path,
            title=title,
            author=author or None,
            article_type=article_type,
            style=style,
            comment_enabled=comment,
            fans_only_comment=fans_only_comment,
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR",
        }
    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


# Serve static files (built frontend)
if STATIC_DIR.exists():

    @app.get("/")
    async def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = STATIC_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
