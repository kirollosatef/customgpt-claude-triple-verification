#!/usr/bin/env bash
# CustomGPT Triple Verification — macOS/Linux/WSL Installer
# Usage: bash install.sh

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m'

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN} CustomGPT Triple Verification Installer${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# WSL Detection
if grep -qEi "(Microsoft|WSL)" /proc/version 2>/dev/null; then
    echo -e "${YELLOW}WARNING: Running inside WSL${NC}"
    echo -e "${GRAY}  Claude Code on Windows runs natively, not through WSL.${NC}"
    echo -e "${GRAY}  If you're using Claude Code on Windows, run install.ps1 instead.${NC}"
    echo -e "${GRAY}  If you're using Claude Code inside WSL, continue.${NC}"
    echo ""
    read -p "Continue with WSL installation? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Step 1: Check Node.js
echo -e "${YELLOW}[1/4] Checking Node.js...${NC}"
if ! command -v node &>/dev/null; then
    echo -e "${RED}ERROR: Node.js not found. Install from https://nodejs.org${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v\([0-9]*\).*/\1/')
if [ "$NODE_MAJOR" -lt 18 ]; then
    echo -e "${RED}ERROR: Node.js >= 18 required (found $NODE_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}  Node.js $NODE_VERSION detected${NC}"

# Step 2: Check Claude Code
echo -e "${YELLOW}[2/4] Checking Claude Code...${NC}"
if command -v claude &>/dev/null; then
    echo -e "${GREEN}  Claude Code detected${NC}"
else
    echo -e "${YELLOW}WARNING: Claude Code CLI not found in PATH${NC}"
    echo -e "${GRAY}  Install from: https://claude.ai/code${NC}"
fi

# Step 3: Install plugin
echo -e "${YELLOW}[3/4] Installing plugin...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_SOURCE="$(dirname "$SCRIPT_DIR")"

CLAUDE_DIR="$HOME/.claude"
PLUGINS_DIR="$CLAUDE_DIR/plugins"
TARGET_DIR="$PLUGINS_DIR/customgpt-triple-verification"

mkdir -p "$PLUGINS_DIR"

if [ -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}  Plugin directory exists, updating...${NC}"
    rm -rf "$TARGET_DIR"
fi

cp -r "$PLUGIN_SOURCE" "$TARGET_DIR"
echo -e "${GREEN}  Plugin installed to: $TARGET_DIR${NC}"

# Step 4: Run verification
echo -e "${YELLOW}[4/4] Running verification...${NC}"
if node "$TARGET_DIR/install/verify.mjs"; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Open any project with Claude Code"
    echo "  2. The triple verification hooks are now active"
    echo "  3. Try: 'Create a Python file with a TODO'"
    echo "  4. Check audit logs in .claude/triple-verify-audit/"
    echo ""
else
    echo -e "${YELLOW}WARNING: Verification had issues, but plugin is installed${NC}"
fi
