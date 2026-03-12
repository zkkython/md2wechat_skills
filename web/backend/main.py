"""FastAPI backend for MD2WeChat web interface."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

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


def _validate_relative_path(rel_path: str) -> bool:
    """Validate that a relative path is safe (no directory traversal or absolute paths)."""
    if os.path.isabs(rel_path):
        return False
    if ".." in Path(rel_path).parts:
        return False
    return True


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    style: str = Form("academic_gray"),
    article_type: str = Form("news"),
    comment: bool = Form(False),
    fans_only_comment: bool = Form(False),
    author: str = Form(""),
    title: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    image_paths: str = Form("[]"),
):
    """Upload a single markdown file to WeChat, optionally with images."""

    if not file.filename.endswith((".md", ".markdown")):
        return {
            "success": False,
            "error": "Only .md and .markdown files are supported",
            "code": "INVALID_FILE_TYPE",
        }

    # Parse image_paths JSON
    try:
        parsed_image_paths = json.loads(image_paths)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid image_paths JSON",
            "code": "INVALID_PARAMS",
        }

    # Validate image_paths count matches images count
    if len(parsed_image_paths) != len(images):
        return {
            "success": False,
            "error": f"image_paths count ({len(parsed_image_paths)}) does not match images count ({len(images)})",
            "code": "INVALID_PARAMS",
        }

    # Validate all paths are safe
    for rel_path in parsed_image_paths:
        if not _validate_relative_path(rel_path):
            return {
                "success": False,
                "error": f"Unsafe image path rejected: {rel_path}",
                "code": "INVALID_PATH",
            }

    print(f"[DEBUG] Received {len(images)} images, paths: {parsed_image_paths}")

    # Create temp directory and save files
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)

    try:
        # Save markdown file
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)
        print(f"[DEBUG] Saved md to: {tmp_path} ({len(content)} bytes)")

        # Save images with their relative paths
        for img_file, rel_path in zip(images, parsed_image_paths):
            img_dest = os.path.join(tmp_dir, rel_path)
            os.makedirs(os.path.dirname(img_dest), exist_ok=True)
            img_content = await img_file.read()
            with open(img_dest, "wb") as f:
                f.write(img_content)
            print(f"[DEBUG] Saved image: {img_dest} ({len(img_content)} bytes, exists={os.path.exists(img_dest)})")

        # List all files in temp dir for verification
        for root, dirs, filenames in os.walk(tmp_dir):
            for fn in filenames:
                fp = os.path.join(root, fn)
                print(f"[DEBUG] tmp_dir contains: {os.path.relpath(fp, tmp_dir)} ({os.path.getsize(fp)} bytes)")

        # Use filename (without extension) as title if not provided
        if title is None:
            title = Path(file.filename).stem

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
        # Cleanup entire temp directory
        try:
            shutil.rmtree(tmp_dir)
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
