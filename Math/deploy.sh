#!/bin/bash

# Math Hello World MCPB Deployment Helper
# Helps with installation and setup of the extension

set -e  # Exit on error

EXTENSION_NAME="math-hello-world"
VERSION=$(grep '"version"' manifest.json | sed -E 's/.*"version": "([^"]+)".*/\1/')

echo "=========================================="
echo "MCPB Extension Deployment Helper"
echo "=========================================="
echo "Extension: ${EXTENSION_NAME}"
echo "Version: ${VERSION}"
echo ""

# Function to check Python installation
check_python() {
    echo "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ Python not found! Please install Python 3.8 or higher"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo "✓ Python $PYTHON_VERSION found"
    echo ""
}

# Function to install dependencies
install_deps() {
    echo "Installing dependencies..."
    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements.txt --quiet
        echo "✓ Dependencies installed"
    else
        echo "❌ requirements.txt not found"
        exit 1
    fi
    echo ""
}

# Function to test the server
test_server() {
    echo "Testing server..."
    if [ -f "test_server.py" ]; then
        $PYTHON_CMD test_server.py
    else
        echo "⚠️  Test script not found, skipping tests"
    fi
    echo ""
}

# Function to package the extension
package_extension() {
    echo "Packaging extension..."
    if [ -f "package.sh" ]; then
        ./package.sh
    else
        echo "Creating package manually..."
        PACKAGE_NAME="${EXTENSION_NAME}-${VERSION}.mcpb"
        zip -r "../${PACKAGE_NAME}" . -x "*.pyc" -x "__pycache__/*" -x ".DS_Store" -x "venv/*" -x ".git/*" > /dev/null 2>&1
        echo "✓ Package created: ../${PACKAGE_NAME}"
    fi
    echo ""
}

# Function to show deployment options
show_deployment() {
    echo "=========================================="
    echo "Deployment Options:"
    echo "=========================================="
    echo ""
    echo "1. LOCAL DEVELOPMENT (Recommended for testing)"
    echo "   Run the server directly:"
    echo "   $ $PYTHON_CMD server/main.py"
    echo ""
    echo "2. CLAUDE DESKTOP"
    echo "   a. Package the extension first"
    echo "   b. Open Claude Desktop settings"
    echo "   c. Navigate to Developer > MCP Servers"
    echo "   d. Click 'Install from MCPB'"
    echo "   e. Select the .mcpb file"
    echo ""
    echo "3. MANUAL CONFIGURATION"
    echo "   Add to your MCP client config:"
    echo "   {"
    echo "     \"name\": \"${EXTENSION_NAME}\","
    echo "     \"command\": \"$PYTHON_CMD\","
    echo "     \"args\": [\"$(pwd)/server/main.py\"]"
    echo "   }"
    echo ""
}

# Main menu
echo "Select deployment option:"
echo "1) Install dependencies only"
echo "2) Test the server"
echo "3) Package for distribution"
echo "4) Full setup (install, test, package)"
echo "5) Show deployment instructions"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        check_python
        install_deps
        ;;
    2)
        check_python
        test_server
        ;;
    3)
        package_extension
        ;;
    4)
        check_python
        install_deps
        test_server
        package_extension
        show_deployment
        ;;
    5)
        show_deployment
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo "✓ Done!"