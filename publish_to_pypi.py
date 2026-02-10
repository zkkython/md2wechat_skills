#!/usr/bin/env python3
"""
Publish md2wechat to PyPI.

Usage:
    python publish_to_pypi.py --test    # Publish to TestPyPI
    python publish_to_pypi.py --prod    # Publish to Production PyPI
    python publish_to_pypi.py --check   # Only run checks, don't publish
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=None, check=True):
    """Run a shell command and print output."""
    if description:
        print(f"\n{'='*60}")
        print(f"📦 {description}")
        print(f"{'='*60}")

    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}", file=sys.stderr)
        sys.exit(1)

    return result.returncode == 0


def check_tools():
    """Check if required tools are installed."""
    print("\n" + "="*60)
    print("🔍 Checking required tools...")
    print("="*60)

    # Check system commands
    tools = ["python", "pip", "twine"]
    missing = []

    for tool in tools:
        result = subprocess.run(f"which {tool}", shell=True, capture_output=True)
        if result.returncode != 0:
            missing.append(tool)
            print(f"  ❌ {tool}: NOT FOUND")
        else:
            print(f"  ✓ {tool}: OK")

    # Check Python modules (build is a Python module, not a CLI tool)
    result = subprocess.run("python -c 'import build'", shell=True, capture_output=True)
    if result.returncode != 0:
        missing.append("build")
        print(f"  ❌ build: NOT FOUND (Python module)")
    else:
        print(f"  ✓ build: OK (Python module)")

    if missing:
        print(f"\n❌ Missing tools: {', '.join(missing)}")
        print("\nInstall missing tools:")
        print("  pip install twine build")
        sys.exit(1)

    print("\n✓ All required tools are installed")


def check_credentials(pypi_type="test"):
    """Check PyPI credentials."""
    print("\n" + "="*60)
    print("🔐 Checking PyPI credentials...")
    print("="*60)

    if pypi_type == "test":
        # Check for TestPyPI token in ~/.pypirc or environment
        pypirc = Path.home() / ".pypirc"
        if pypirc.exists():
            content = pypirc.read_text()
            if "testpypi" in content:
                print("  ✓ TestPyPI config found in ~/.pypirc")
                return True

        if os.environ.get("TWINE_USERNAME") and os.environ.get("TWINE_PASSWORD"):
            print("  ✓ TWINE_USERNAME and TWINE_PASSWORD environment variables set")
            return True

        print("  ⚠️  No TestPyPI credentials found")
        print("\nSetup options:")
        print("  1. Create ~/.pypirc with TestPyPI token")
        print("  2. Set environment variables:")
        print("     export TWINE_USERNAME=__token__")
        print("     export TWINE_PASSWORD=pypi-your-test-token")
        return False

    else:  # production
        pypirc = Path.home() / ".pypirc"
        if pypirc.exists():
            content = pypirc.read_text()
            if "pypi" in content and "testpypi" not in content.lower():
                print("  ✓ PyPI config found in ~/.pypirc")
                return True

        if os.environ.get("TWINE_USERNAME") and os.environ.get("TWINE_PASSWORD"):
            print("  ✓ TWINE_USERNAME and TWINE_PASSWORD environment variables set")
            return True

        print("  ⚠️  No PyPI credentials found")
        print("\nSetup options:")
        print("  1. Create ~/.pypirc with PyPI token")
        print("  2. Set environment variables:")
        print("     export TWINE_USERNAME=__token__")
        print("     export TWINE_PASSWORD=pypi-your-production-token")
        return False


def run_tests():
    """Run test suite."""
    print("\n" + "="*60)
    print("🧪 Running tests...")
    print("="*60)

    if not Path("test_official_api.py").exists():
        print("  ⚠️  test_official_api.py not found, skipping tests")
        return True

    result = subprocess.run("python test_official_api.py", shell=True)
    if result.returncode != 0:
        print("\n❌ Tests failed! Fix before publishing.", file=sys.stderr)
        return False

    print("\n✓ All tests passed")
    return True


def clean_build():
    """Clean old build files."""
    print("\n" + "="*60)
    print("🧹 Cleaning old build files...")
    print("="*60)

    dirs_to_clean = ["dist", "build", "*.egg-info"]

    for pattern in dirs_to_clean:
        result = subprocess.run(f"rm -rf {pattern}", shell=True, capture_output=True)
        print(f"  Cleaned: {pattern}")

    # Find and remove __pycache__ directories
    result = subprocess.run("find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true",
                          shell=True, capture_output=True)
    print(f"  Cleaned: __pycache__ directories")

    print("\n✓ Build directory cleaned")


def build_package():
    """Build the package."""
    print("\n" + "="*60)
    print("🔨 Building package...")
    print("="*60)

    run_command("python -m build", "Building distribution packages")

    # List built files
    print("\nBuilt files:")
    dist_dir = Path("dist")
    if dist_dir.exists():
        for f in sorted(dist_dir.iterdir()):
            size = f.stat().st_size / 1024  # KB
            print(f"  {f.name} ({size:.1f} KB)")

    print("\n✓ Package built successfully")


def check_package():
    """Check the package with twine."""
    print("\n" + "="*60)
    print("📋 Checking package with twine...")
    print("="*60)

    run_command("twine check dist/*", "Validating package")

    print("\n✓ Package validation passed")


def upload_to_pypi(pypi_type="test"):
    """Upload to PyPI."""
    print("\n" + "="*60)

    if pypi_type == "test":
        print("📤 Uploading to TestPyPI...")
        print("="*60)
        cmd = "twine upload --repository testpypi dist/*"
    else:
        print("📤 Uploading to Production PyPI...")
        print("="*60)
        cmd = "twine upload dist/*"

    print(f"\nCommand: {cmd}")
    print("\n⚠️  You will be prompted for credentials if not configured.")
    print("   For API tokens, username: __token__")
    print("   Password: pypi-your-token-here")
    print()

    confirm = input("Continue with upload? [y/N]: ")
    if confirm.lower() != 'y':
        print("Upload cancelled.")
        return False

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("\n❌ Upload failed", file=sys.stderr)
        return False

    print("\n✓ Upload completed")
    return True


def verify_install(pypi_type="test", version=None):
    """Verify the package can be installed."""
    print("\n" + "="*60)
    print("✅ Verifying package installation...")
    print("="*60)

    if pypi_type == "test":
        index_url = "https://test.pypi.org/simple/"
        pkg_name = "md2wechat"
    else:
        index_url = "https://pypi.org/simple/"
        pkg_name = "md2wechat"

    print(f"\nTo install from {pypi_type}:")
    if pypi_type == "test":
        print(f"  pip install --index-url {index_url} {pkg_name}")
    else:
        print(f"  pip install {pkg_name}")

    print("\nTo verify:")
    print(f"  md2wechat --help")

    print("\n✓ Verification instructions printed")


def main():
    parser = argparse.ArgumentParser(
        description="Publish md2wechat to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python publish_to_pypi.py --check    # Run all checks without publishing
  python publish_to_pypi.py --test     # Publish to TestPyPI
  python publish_to_pypi.py --prod     # Publish to Production PyPI

Setup:
  1. Get PyPI API token from https://pypi.org/manage/account/token/
  2. Configure credentials in ~/.pypirc or environment variables:
     export TWINE_USERNAME=__token__
     export TWINE_PASSWORD=pypi-your-token-here
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--test",
        action="store_true",
        help="Publish to TestPyPI (test.pypi.org)"
    )
    group.add_argument(
        "--prod",
        action="store_true",
        help="Publish to Production PyPI (pypi.org)"
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Only run checks, don't publish"
    )

    args = parser.parse_args()

    # Determine target
    if args.test:
        pypi_type = "test"
    elif args.prod:
        pypi_type = "prod"
    else:
        pypi_type = "check"

    print("\n" + "="*60)
    print("🚀 md2wechat PyPI Publisher")
    print("="*60)
    print(f"\nTarget: {'TestPyPI' if pypi_type == 'test' else 'Production PyPI' if pypi_type == 'prod' else 'Checks only'}")

    # Step 1: Check tools
    check_tools()

    # Step 2: Run tests
    if not run_tests():
        sys.exit(1)

    # If only checking, stop here
    if pypi_type == "check":
        print("\n" + "="*60)
        print("✅ All checks passed! Package is ready for publishing.")
        print("="*60)
        sys.exit(0)

    # Step 3: Check credentials
    if not check_credentials(pypi_type):
        print("\n❌ PyPI credentials not configured.", file=sys.stderr)
        sys.exit(1)

    # Step 4: Clean build directory
    clean_build()

    # Step 5: Build package
    build_package()

    # Step 6: Check package
    check_package()

    # Step 7: Upload
    if not upload_to_pypi(pypi_type):
        sys.exit(1)

    # Step 8: Verify
    verify_install(pypi_type)

    print("\n" + "="*60)
    print("🎉 Publishing complete!")
    print("="*60)

    if pypi_type == "test":
        print("\n📦 Package published to TestPyPI")
        print("   Install with: pip install --index-url https://test.pypi.org/simple/ md2wechat")
    else:
        print("\n📦 Package published to Production PyPI")
        print("   Install with: pip install md2wechat")

    print("\n⚠️  Note: It may take a few minutes for the package to be available.")


if __name__ == "__main__":
    main()
