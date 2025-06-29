#!/bin/bash

# Claude Code Helper Commands - Installation Script
# Downloads and installs Claude Code helper commands to ~/.claude/commands

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/niekcandaele/claude-helpers"
BRANCH="main"
INSTALL_DIR="$HOME/.claude/commands"
TEMP_DIR=$(mktemp -d)

# Functions
print_status() {
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

cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Cleanup on exit
trap cleanup EXIT

main() {
    echo "🤖 Claude Code Helper Commands Installer"
    echo "========================================"
    echo

    # Check if commands directory already exists
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Commands directory already exists at $INSTALL_DIR"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installation cancelled."
            exit 0
        fi
        print_status "Backing up existing commands to ${INSTALL_DIR}.backup"
        mv "$INSTALL_DIR" "${INSTALL_DIR}.backup"
    fi

    # Create Claude directory structure
    print_status "Creating directory structure..."
    mkdir -p "$(dirname "$INSTALL_DIR")"

    # Download and extract
    print_status "Downloading commands from $REPO_URL..."
    cd "$TEMP_DIR"
    
    if command -v curl >/dev/null 2>&1; then
        curl -L "${REPO_URL}/archive/${BRANCH}.tar.gz" | tar -xz --strip-components=1
    elif command -v wget >/dev/null 2>&1; then
        wget -O- "${REPO_URL}/archive/${BRANCH}.tar.gz" | tar -xz --strip-components=1
    else
        print_error "Neither curl nor wget is available. Please install one of them."
        exit 1
    fi

    # Check if commands directory was extracted
    if [ ! -d "commands" ]; then
        print_error "Commands directory not found in downloaded archive."
        exit 1
    fi

    # Move commands to installation directory
    print_status "Installing commands to $INSTALL_DIR..."
    mv commands "$INSTALL_DIR"

    # Verify installation
    COMMAND_COUNT=$(find "$INSTALL_DIR" -name "*.md" | wc -l)
    
    print_success "Successfully installed $COMMAND_COUNT commands!"
    echo
    echo "📋 Available commands:"
    find "$INSTALL_DIR" -name "*.md" -exec basename {} .md \; | sed 's/^/  - /'
    echo
    echo "🚀 Usage:"
    echo "  Use commands in Claude Code with: /command-name"
    echo "  Example: /create-prd Add user authentication"
    echo
    echo "📖 Documentation: $REPO_URL"
    echo
    print_success "Installation complete! 🎉"
}

main "$@"