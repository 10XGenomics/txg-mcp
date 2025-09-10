#!/bin/bash

# Build script for TXG MCP Desktop Extension (TypeScript version)

set -e

echo "Building TXG MCP Desktop Extension (TypeScript)..."

# Clean previous builds
rm -rf dist/ build/ *.mcpb

# Install dependencies
echo "Installing dependencies..."
npm install

# Build TypeScript
echo "Compiling TypeScript..."
npm run build

# Create build directory
mkdir -p build

# Copy distribution files
echo "Copying distribution files..."
cp -r dist/* build/
cp manifest.json build/
cp package.json build/

# Install production dependencies in build directory
echo "Installing production dependencies..."
cd build
npm install --production --no-package-lock
cd ..

# Create a simple icon if it doesn't exist
if [ ! -f icon.png ]; then
    echo "Creating placeholder icon..."
    # Create a simple 64x64 PNG icon using base64 encoded data
    echo "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABmJLR0QA/wD/AP+gvaeTAAADpklEQVR4nO2bTWgTQRTHf5tsmmjTpn6gVqsIHkQQPHjwIIIHL4IHL4IHLx48eBDEgwcPHjx48OBBBMGDB0EQRBAEQRAEQVCxWq1Wq9XWr7RJm6RJmjTZ9eBMss1mdjKb3U0K+cNjl5n33rz/zLz3ZnYXioqKioqKCgtcBvqBr0AaSOXJbAH6gHNAg53GdwEvtQYzJplMAqAD6KLJXo6Lge9Ygx6BiUVOAs4BQ5i3+VfJJqLRKMFgkGAw6IThrGSDW1tbef369UwDPsCFU6yQl+9EIoHf7wdgZWWFvr4+lpeXHe6Oi9iRMgCrq6sMDQ05aaxmuJy+YGZmhvHxcZLJJOl02ulue91AABCLxZiZmXG6dS8K4N5YGBsbY3Jy0snWDwKvhFi3+R7X/BTA7mNSz0RHR4fd170KPAO6kZxnA4Ab4D7wB3iDOPuKdl5HoG5yAbhJfiCUBt4Ct5AMhJ6sFjdwA3gBLCGGvdRAGeFk3C5YjIVCIUJAJzBuok4mE9wBDuv9uVTWqxWcJJRpXgC8BU5h4huyoaWlhdnZ2dwfu4AzWt1YNEooFA42NDS01NXVtQH9QGctXCCbSCSCoihtiqK4gROa7F3gFtlRHktGVlZWmJ+f7/V6vV9cLtc+YBNwiOyOT01woRDJZJJgMOjL/O/3+xkdHe1VFOURTvv/5uZmIpFIQ319/XFgs12NGoEpATJutkcIcYk9jh9dCLGnUGHNh8A2M7q1iG0CGN2mtDbtC0AKUecBh8y4PqBsz6vBnYJacBr4rnWkkZEOIQax51j7AJhFLFaW17JqYQBwAvim16nfiqIsm7n4nh8CyLSa6vG8HkBGz7yiKGY3J2oidTLJGwm59LtOzQDNEOh0qEPOTMz2QP4gmAwGEfP7AzDsUIdc5oRxEdgHvEd43lV1UoqN7EdcBvSQ8YJIJBKIRCIVGy8zBUqLUK4LLCwsDGiXdZXxgEy1CuUGQiBAOBzuz/m7w9B0rKEAz6JQxu/3B4RxRYmbNy3tBJX8PUFOvXp6ejh48CDxeJzh4WEWFxfZsGED3d3dbN++HYB4PM7IyAgDAwPE43E2bdrE0aNH2bJlCwsLC4yMjPD27Vui0SgA27Zt4/Dhw2zevJnFxUVGR0d59+4doVCI+vp6du3axYEDB2hrayMajTI+Ps7Hjx+ZnZ0lmUzS0tLCnj172Lt3L21tbUSjUSYmJvj06RPBYJBEItHwD0iXrD5/n5K5AAAAAElFTkSuQmCC" | base64 -d > icon.png
fi

# Copy icon if it exists
if [ -f icon.png ]; then
    cp icon.png build/
fi

# Update manifest.json in build to point to correct server path
cd build
# Update server paths in manifest to point to compiled JS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's|"entry_point": "dist/server/index.js"|"entry_point": "server/index.js"|' manifest.json
    sed -i '' 's|"main": "dist/server/index.js"|"main": "server/index.js"|' package.json
else
    # Linux
    sed -i 's|"entry_point": "dist/server/index.js"|"entry_point": "server/index.js"|' manifest.json
    sed -i 's|"main": "dist/server/index.js"|"main": "server/index.js"|' package.json
fi
cd ..

# Create the .mcpb file (zip archive)
echo "Creating .mcpb bundle..."
cd build
zip -r ../txg-mcp.mcpb * -x "*.DS_Store" -x "__MACOSX/*" -x "*.ts" -x "*.map"
cd ..

# Clean up build directory
rm -rf build/

echo "Build complete! Extension bundle created: txg-mcp.mcpb"
echo ""
echo "To install this extension:"
echo "1. Open Claude Desktop"
echo "2. Go to Settings > Extensions"
echo "3. Click 'Install from file' and select txg-mcp.mcpb"