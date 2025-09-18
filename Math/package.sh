#!/bin/bash

# Math Hello World MCPB Packaging Script
# Creates a .mcpb package file for distribution

set -e  # Exit on error

EXTENSION_NAME="math-hello-world"
VERSION=$(grep '"version"' manifest.json | sed -E 's/.*"version": "([^"]+)".*/\1/')
PACKAGE_NAME="${EXTENSION_NAME}-${VERSION}.mcpb"

echo "=========================================="
echo "MCPB Extension Packager"
echo "=========================================="
echo "Extension: ${EXTENSION_NAME}"
echo "Version: ${VERSION}"
echo "Output: ${PACKAGE_NAME}"
echo ""

# Check if we're in the right directory
if [ ! -f "manifest.json" ]; then
    echo "Error: manifest.json not found!"
    echo "Please run this script from the Math directory"
    exit 1
fi

# Clean up any previous packages
if [ -f "../${PACKAGE_NAME}" ]; then
    echo "Removing existing package..."
    rm "../${PACKAGE_NAME}"
fi

# Create the package
echo "Creating MCPB package..."
zip -r "../${PACKAGE_NAME}" . \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "*/__pycache__/*" \
    -x ".DS_Store" \
    -x "*.log" \
    -x "venv/*" \
    -x ".venv/*" \
    -x "env/*" \
    -x ".git/*" \
    -x "*.mcpb" \
    -x "test_*.py" \
    -x "package.sh" \
    -x ".gitignore" \
    -x "*.swp" \
    -x "*.swo" \
    -x "*~" \
    -x ".idea/*" \
    -x ".vscode/*" \
    -x ".pytest_cache/*" \
    -x "htmlcov/*" \
    -x ".coverage"

echo ""
echo "✓ Package created successfully!"
echo ""
echo "Package location: ../${PACKAGE_NAME}"
echo "Size: $(du -h "../${PACKAGE_NAME}" | cut -f1)"
echo ""
echo "=========================================="
echo "Deployment Instructions:"
echo "=========================================="
echo ""
echo "1. For Claude Desktop:"
echo "   - Open Claude Desktop"
echo "   - Go to Settings > Developer > MCP Servers"
echo "   - Click 'Install from MCPB'"
echo "   - Select the ${PACKAGE_NAME} file"
echo ""
echo "2. For manual installation:"
echo "   - Unzip ${PACKAGE_NAME} to your MCP extensions folder"
echo "   - Configure your application to recognize the extension"
echo ""
echo "3. For development/testing:"
echo "   - Install Python dependencies: pip install -r requirements.txt"
echo "   - Run directly: python server/main.py"
echo ""
echo "=========================================="