#!/bin/bash
# Installation script for pass-browser native messaging host

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_NAME="de.zisoft.pass_browser"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}pass-browser Native Messaging Host Installer${NC}"
echo ""

# Check for pass executable
if ! command -v pass &> /dev/null; then
    echo -e "${RED}Error: 'pass' executable not found!${NC}"
    echo "Please install pass first:"
    echo "  macOS: brew install pass"
    echo "  Linux: apt-get install pass (or your distro's package manager)"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found pass: $(which pass)"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found!${NC}"
    echo "Please install Python 3 first."
    exit 1
fi

echo -e "${GREEN}✓${NC} Found Python: $(which python3)"

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo -e "${RED}Error: Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Detected OS: $OS"

# Install directory
INSTALL_DIR="$HOME/.local/share/pass-browser"
mkdir -p "$INSTALL_DIR"

# Copy the host script
echo "Installing native host to $INSTALL_DIR..."
cp "$SCRIPT_DIR/pass_browser_host.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/pass_browser_host.py"

echo -e "${GREEN}✓${NC} Installed native host script"

# Create the manifest file with correct path
MANIFEST_FILE="$SCRIPT_DIR/${HOST_NAME}.json"
TEMP_MANIFEST="/tmp/${HOST_NAME}.json"

# Replace INSTALL_PATH with actual path
sed "s|INSTALL_PATH|$INSTALL_DIR|g" "$MANIFEST_FILE" > "$TEMP_MANIFEST"

# Determine manifest installation location based on OS and browser
install_manifest() {
    local browser=$1
    local manifest_dir=""
    
    if [[ "$OS" == "macos" ]]; then
        case $browser in
            chrome)
                manifest_dir="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
                ;;
            chromium)
                manifest_dir="$HOME/Library/Application Support/Chromium/NativeMessagingHosts"
                ;;
            edge)
                manifest_dir="$HOME/Library/Application Support/Microsoft Edge/NativeMessagingHosts"
                ;;
        esac
    elif [[ "$OS" == "linux" ]]; then
        case $browser in
            chrome)
                manifest_dir="$HOME/.config/google-chrome/NativeMessagingHosts"
                ;;
            chromium)
                manifest_dir="$HOME/.config/chromium/NativeMessagingHosts"
                ;;
            edge)
                manifest_dir="$HOME/.config/microsoft-edge/NativeMessagingHosts"
                ;;
        esac
    fi
    
    if [[ -n "$manifest_dir" ]]; then
        mkdir -p "$manifest_dir"
        cp "$TEMP_MANIFEST" "$manifest_dir/${HOST_NAME}.json"
        echo -e "${GREEN}✓${NC} Installed manifest for $browser: $manifest_dir"
        return 0
    fi
    
    return 1
}

# Try to install for all supported browsers
echo ""
echo "Installing native messaging manifest..."
INSTALLED=false

for browser in chrome chromium edge; do
    if install_manifest "$browser"; then
        INSTALLED=true
    fi
done

# Clean up temp file
rm -f "$TEMP_MANIFEST"

if [[ "$INSTALLED" == "false" ]]; then
    echo -e "${YELLOW}Warning: Could not auto-install manifest. Please install manually.${NC}"
    echo "See README.md for manual installation instructions."
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Load the extension in Chrome/Edge:"
echo "   - Open chrome://extensions/ (or edge://extensions/)"
echo "   - Enable 'Developer mode'"
echo "   - Click 'Load unpacked'"
echo "   - Select: $SCRIPT_DIR/../extension"
echo ""
echo "2. Get the extension ID from the extensions page"
echo ""
echo "3. Update the manifest with your extension ID:"
if [[ "$OS" == "macos" ]]; then
    echo "   For Chrome: ~/Library/Application Support/Google/Chrome/NativeMessagingHosts/${HOST_NAME}.json"
    echo "   For Edge: ~/Library/Application Support/Microsoft Edge/NativeMessagingHosts/${HOST_NAME}.json"
else
    echo "   For Chrome: ~/.config/google-chrome/NativeMessagingHosts/${HOST_NAME}.json"
    echo "   For Edge: ~/.config/microsoft-edge/NativeMessagingHosts/${HOST_NAME}.json"
fi
echo ""
echo "   Replace EXTENSION_ID with your actual extension ID"
echo ""

# Install for Firefox
echo ""
echo "Installing for Firefox..."
FIREFOX_MANIFEST_DIR=""

if [[ "$OS" == "macos" ]]; then
    FIREFOX_MANIFEST_DIR="$HOME/Library/Application Support/Mozilla/NativeMessagingHosts"
elif [[ "$OS" == "linux" ]]; then
    FIREFOX_MANIFEST_DIR="$HOME/.mozilla/native-messaging-hosts"
fi

if [[ -n "$FIREFOX_MANIFEST_DIR" ]]; then
    mkdir -p "$FIREFOX_MANIFEST_DIR"
    sed "s|INSTALL_PATH|$INSTALL_DIR|g" "$SCRIPT_DIR/de.zisoft.pass_browser.firefox.json" > "$FIREFOX_MANIFEST_DIR/de.zisoft.pass_browser.json"
    echo -e "${GREEN}✓${NC} Installed manifest for Firefox: $FIREFOX_MANIFEST_DIR"
    INSTALLED=true
fi
