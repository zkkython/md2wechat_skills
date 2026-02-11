#!/bin/bash
#
# Install md2wechat as a Claude Code skill
#
# Usage:
#   ./install.sh
#
# This script will:
#   1. Check Python version (3.9+)
#   2. Install Python dependencies (wechatpy)
#   3. Copy skill to ~/.claude/skills/
#   4. Set up .env file if not exists
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="md2wechat"
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    print_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION="3.9"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION is compatible"
}

# Install Python dependencies
install_deps() {
    print_info "Installing Python dependencies..."

    if pip3 install wechatpy; then
        print_success "Dependencies installed"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Install skill to Claude directory
install_skill() {
    print_info "Installing skill to Claude Code..."

    # Create skills directory
    if [ ! -d "$CLAUDE_SKILLS_DIR" ]; then
        mkdir -p "$CLAUDE_SKILLS_DIR"
        print_success "Created Claude skills directory"
    fi

    # Remove existing skill if present
    if [ -d "${CLAUDE_SKILLS_DIR}/${SKILL_NAME}" ]; then
        print_warning "Existing skill found, updating..."
        rm -rf "${CLAUDE_SKILLS_DIR}/${SKILL_NAME}"
    fi

    # Copy skill
    cp -r "${SCRIPT_DIR}/skills/${SKILL_NAME}" "$CLAUDE_SKILLS_DIR/"

    # Make scripts executable
    chmod +x "${CLAUDE_SKILLS_DIR}/${SKILL_NAME}/scripts/"*.py

    print_success "Skill installed to ${CLAUDE_SKILLS_DIR}/${SKILL_NAME}"
}

# Setup environment file
setup_env() {
    print_info "Setting up environment configuration..."

    ENV_FILE="${SCRIPT_DIR}/.env"
    ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"

    if [ -f "$ENV_FILE" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing .env file"
            return
        fi
    fi

    # Copy example file
    cp "$ENV_EXAMPLE" "$ENV_FILE"

    print_success "Created .env file"
    print_info "Please edit .env and add your WeChat credentials:"
    echo ""
    echo "  WECHAT_APPID=your_appid_here"
    echo "  WECHAT_APP_SECRET=your_app_secret_here"
    echo ""
    echo "Get credentials from: https://mp.weixin.qq.com"
    echo "  Settings → Development → Basic Configuration"
    echo ""
}

# Verify installation
verify_install() {
    print_info "Verifying installation..."

    # Check if skill files exist
    if [ ! -f "${CLAUDE_SKILLS_DIR}/${SKILL_NAME}/SKILL.md" ]; then
        print_error "Skill files not found"
        exit 1
    fi

    # Check if wechatpy is installed
    if ! python3 -c "import wechatpy" 2>/dev/null; then
        print_error "wechatpy is not installed properly"
        exit 1
    fi

    print_success "Installation verified"
}

# Print usage instructions
print_usage() {
    echo ""
    echo "=========================================="
    echo "  md2wechat Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Usage:"
    echo ""
    echo "1. Configure your WeChat credentials:"
    echo "   Edit: ${SCRIPT_DIR}/.env"
    echo ""
    echo "2. Test the installation:"
    echo "   python3 ${SCRIPT_DIR}/test_official_api.py"
    echo ""
    echo "3. Publish an article:"
    echo "   python3 ${CLAUDE_SKILLS_DIR}/${SKILL_NAME}/scripts/wechat_official_api.py publish \\"
    echo "     --markdown /path/to/article.md"
    echo ""
    echo "4. Or use Claude Code:"
    echo "   Start Claude Code and say:"
    echo "   'Publish this markdown article to WeChat: article.md'"
    echo ""
    echo "Documentation:"
    echo "   ${SCRIPT_DIR}/README.md"
    echo "   ${CLAUDE_SKILLS_DIR}/${SKILL_NAME}/SKILL.md"
    echo ""
}

# Main installation process
main() {
    echo "=========================================="
    echo "  Installing md2wechat skill"
    echo "=========================================="
    echo ""

    check_python
    install_deps
    install_skill
    setup_env
    verify_install
    print_usage
}

# Run main function
main "$@"
