# Publishing to PyPI

This document describes how to publish md2wechat to PyPI (Python Package Index).

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org)
2. **API Token**: Generate an API token at [pypi.org/manage/account/token](https://pypi.org/manage/account/token)
3. **Required Tools**:
   ```bash
   pip install twine build
   ```

## Quick Start

### Option 1: Using the Publish Script (Recommended)

```bash
# Run checks only (no publishing)
python publish_to_pypi.py --check

# Publish to TestPyPI (for testing)
python publish_to_pypi.py --test

# Publish to Production PyPI
python publish_to_pypi.py --prod
```

### Option 2: Manual Steps

```bash
# 1. Run tests
python test_official_api.py

# 2. Clean build directory
rm -rf dist build *.egg-info

# 3. Build package
python -m build

# 4. Check package
 twine check dist/*

# 5. Upload to TestPyPI
 twine upload --repository testpypi dist/*

# 6. Upload to Production PyPI
 twine upload dist/*
```

## Configuration

### Method 1: Environment Variables (Recommended for CI/CD)

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

### Method 2: ~/.pypirc File

Copy the example file and fill in your tokens:

```bash
cp .pypirc.example ~/.pypirc
# Edit ~/.pypirc with your tokens
```

**~/.pypirc format:**
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-production-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

## Publishing Workflow

### 1. Test on TestPyPI First

```bash
python publish_to_pypi.py --test
```

Test the installation:
```bash
pip install --index-url https://test.pypi.org/simple/ md2wechat
md2wechat --help
```

### 2. Fix Any Issues

If there are issues:
1. Fix the code
2. Update version in `pyproject.toml`
3. Rebuild and re-upload

### 3. Publish to Production

```bash
python publish_to_pypi.py --prod
```

### 4. Verify Production Package

```bash
pip install md2wechat
md2wechat --help
```

## Version Management

Update version in `pyproject.toml` before each release:

```toml
[project]
name = "md2wechat"
version = "1.0.1"  # Increment this
```

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- `1.0.0` → `1.0.1` (bug fix)
- `1.0.0` → `1.1.0` (new feature)
- `1.0.0` → `2.0.0` (breaking change)

## Troubleshooting

### Error: "Invalid distribution file"

Solution: Clean and rebuild
```bash
rm -rf dist build
python -m build
```

### Error: "File already exists"

You cannot upload the same version twice. Increment the version number in `pyproject.toml`.

### Error: "Invalid or non-existent authentication"

1. Check your API token is correct
2. Ensure you're using `__token__` as username
3. Verify `~/.pypirc` or environment variables are set

### Error: "HTTPError: 403 Forbidden"

Your token may not have the right permissions. Create a new token with "Upload packages" scope.

## GitHub Actions (Optional)

To automate publishing on GitHub releases, create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Then add `PYPI_API_TOKEN` to your GitHub repository secrets.

## Checklist Before Publishing

- [ ] All tests pass
- [ ] Version number updated in `pyproject.toml`
- [ ] README.md is up to date
- [ ] CHANGELOG.md updated (if you have one)
- [ ] Tested on TestPyPI
- [ ] Credentials configured
- [ ] Git tag created (optional): `git tag v1.0.0`
