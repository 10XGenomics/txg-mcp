#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Run development server
run_server() {
    local token="${1:-}"
    local credentials_file="$SCRIPT_DIR/credentials.txt"
    local access_token=""

    # Handle access token
    if [[ -n "$token" ]]; then
        # Token provided as argument
        access_token="$token"

        # Save to credentials file for future use
        echo "$access_token" > "$credentials_file"
        chmod 600 "$credentials_file"  # Restrict permissions
        print_info "Access token saved to credentials.txt"
    elif [[ -f "$credentials_file" ]]; then
        # Read token from credentials file
        access_token=$(cat "$credentials_file")
        print_info "Using access token from credentials.txt"
    else
        # No token available
        print_error "Access token required but not provided"
        print_info "Usage: $0 run-server [access_token]"
        print_info "Or save your token to credentials.txt"
        print_info "Get your token from: https://cloud.10xgenomics.com/account/security"
        return 1
    fi
    export TXG_CLI_ACCESS_TOKEN="$access_token"

    cd "$SCRIPT_DIR"

    # Check if build exists
    if [[ ! -d "build/server" ]] || [[ ! -f "build/server/index.js" ]]; then
        print_warning "Build not found. Running build first..."
        npm run build || {
            print_error "Build failed"
            return 1
        }
    fi

    print_info "Starting MCP server..."

    # Run the server with the access token
    TXG_CLI_ACCESS_TOKEN="$access_token" node build/server/index.js
}

# Prepare build folder for validation (without bin files or bundling)
prepare_build() {
    print_info "Preparing build folder for validation..."

    cd "$SCRIPT_DIR"

    # Ensure build directory exists
    mkdir -p build

    # Copy required assets to build folder
    print_info "Copying assets to build folder..."

    # Copy icon if it exists
    if [[ -f "assets/icon.png" ]]; then
        cp assets/icon.png build/
        print_success "Copied icon.png"
    else
        print_warning "assets/icon.png not found"
    fi

    # Copy package.json
    if [[ -f "package.json" ]]; then
        cp package.json build/
        print_success "Copied package.json"
    else
        print_error "package.json not found"
        return 1
    fi

    # Copy manifest.json
    if [[ -f "manifest.json" ]]; then
        cp manifest.json build/
        print_success "Copied manifest.json"
    else
        print_error "manifest.json not found"
        return 1
    fi

    # Copy USER_GUIDE.md as README.md
    if [[ -f "USER_GUIDE.md" ]]; then
        cp USER_GUIDE.md build/README.md
        print_success "Copied USER_GUIDE.md as README.md"
    else
        print_warning "USER_GUIDE.md not found"
    fi

    # Copy LICENSE
    if [[ -f "LICENSE" ]]; then
        cp LICENSE build/
        print_success "Copied LICENSE"
    else
        print_warning "LICENSE not found"
    fi

    # Check that server folder exists and is non-empty
    if [[ -d "build/server" ]]; then
        if [[ -n "$(ls -A build/server 2>/dev/null)" ]]; then
            print_success "server folder exists and is non-empty"
        else
            print_error "build/server folder is empty"
            return 1
        fi
    else
        print_error "build/server folder not found"
        print_info "Run 'npm run build' first"
        return 1
    fi

    print_success "Build folder prepared for validation"
}

# Create MCP bundle
pack() {
    print_info "Creating MCP bundle..."

    cd "$SCRIPT_DIR"

    # Prepare build folder (copy assets and validate server folder)
    prepare_build || return 1

    # Check that bin folder exists and is non-empty
    if [[ -d "build/bin" ]]; then
        if [[ -n "$(ls -A build/bin 2>/dev/null)" ]]; then
            print_success "bin folder exists and is non-empty"
        else
            print_error "build/bin folder is empty"
            print_info "Run './tasks.sh download-bin' to download TXG CLI binaries"
            return 1
        fi
    else
        print_error "build/bin folder not found"
        print_info "Run './tasks.sh download-bin' to download TXG CLI binaries"
        return 1
    fi

    # Install production dependencies only in build folder
    print_info "Installing production dependencies..."
    if [[ -f "package.json" ]]; then
        # Copy package.json and package-lock.json to build folder temporarily
        cp package.json build/
        if [[ -f "package-lock.json" ]]; then
            cp package-lock.json build/
        fi

        # Install only production dependencies in build folder
        cd build
        npm ci --omit=dev
        cd ..

        # Remove package files from build as they're already copied earlier
        rm -f build/package-lock.json

        print_success "Installed production dependencies"
    else
        print_error "package.json not found"
        return 1
    fi

    # Create bundle with mcpb
    print_info "Packing with mcpb..."
    if command -v mcpb &> /dev/null; then
        mcpb pack build txg-node.mcpb
        print_success "Bundle created: txg-node.mcpb"
    else
        print_error "mcpb not found. Install with: npm install -g @modelcontextprotocol/bundler"
        return 1
    fi
}

# Generate capabilities reference documentation
generate_capabilities() {
    local credentials_file="$SCRIPT_DIR/credentials.txt"
    local script_path="$SCRIPT_DIR/scripts/query-capabilities.js"
    local reference_dir="$SCRIPT_DIR/reference"
    local output_file="$reference_dir/mcp_capabilities_reference.json"
    local access_token=""

    print_info "Generating MCP capabilities reference..."

    # Check if build exists
    if [[ ! -d "build/server" ]] || [[ ! -f "build/server/index.js" ]]; then
        print_warning "Build not found. Running build first..."
        npm run build || {
            print_error "Build failed"
            return 1
        }
    fi

    # Get access token if available
    if [[ -f "$credentials_file" ]]; then
        access_token=$(cat "$credentials_file")
        print_info "Using access token from credentials.txt"
    else
        access_token=""
        print_info "No credentials.txt found, proceeding without access token"
    fi

    # Create reference directory if it doesn't exist
    mkdir -p "$reference_dir"

    # Run the query script
    print_info "Starting script..."

    if node "$script_path" "$access_token" "$output_file"; then
        # Verify the output file was created
        if [[ -f "$output_file" ]]; then
            # Count capabilities using node
            local counts=$(node -e "
                const data = require('$output_file');
                console.log(\`\${data.tools?.length || 0} tools, \${data.resources?.length || 0} resources, \${data.prompts?.length || 0} prompts\`);
            " 2>/dev/null || echo "Unable to count")

            print_success "Done"
        else
            print_error "Output file was not created"
            return 1
        fi
    else
        print_error "Failed to query server capabilities"
        return 1
    fi
}

# Download TXG CLI binaries
download_bin() {
    local version="${1:-latest}"
    local bin_dir="$SCRIPT_DIR/build/bin"
    local temp_dir="/tmp/txg-cli-download-$$"

    print_info "Downloading TXG CLI binaries (version: $version)..."

    # Check if binaries already exist
    local files_exist=false
    if [[ -f "$bin_dir/darwin/txg" ]] || [[ -f "$bin_dir/linux/txg" ]] || [[ -f "$bin_dir/windows/txg.exe" ]]; then
        files_exist=true
        print_warning "Some binary files already exist in package/bin/"
        read -p "Do you want to overwrite existing files? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Download cancelled"
            return 0
        fi
    fi

    # Get the actual version if "latest" was specified
    if [[ "$version" == "latest" ]]; then
        print_info "Fetching latest version from GitHub..."

        # Use gh CLI to get latest release from internal repo
        if command -v gh &> /dev/null; then
            version=$(gh release list --repo 10XDev/rickover-cli --limit 1 | awk '{print $3}')
            if [[ -n "$version" ]]; then
                print_info "Latest version is $version"
            else
                print_warning "Could not fetch latest version using gh CLI"
                version="v3.0.1"
                print_info "Using fallback version $version"
            fi
        else
            print_warning "GitHub CLI (gh) not found. Install it for automatic latest version detection."
            print_info "Using fallback version v3.0.1"
            version="v3.0.1"
        fi
    fi

    # Clean version (ensure it starts with v)
    if [[ ! "$version" =~ ^v ]]; then
        version="v$version"
    fi

    # Create temp directory
    mkdir -p "$temp_dir"
    cd "$temp_dir"

    # Download from GitHub using gh CLI
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is required to download from internal GitHub repo"
        print_info "Install it with: brew install gh"
        rm -rf "$temp_dir"
        return 1
    fi

    # Download all three platform binaries using gh CLI
    print_info "Downloading macOS binary from GitHub..."
    if ! gh release download "$version" --repo 10XDev/rickover-cli --pattern "txg-macos-$version.zip" --dir . 2>/dev/null; then
        print_error "Failed to download macOS binary. Make sure you're authenticated with gh auth login"
        rm -rf "$temp_dir"
        return 1
    fi

    print_info "Downloading Linux binary from GitHub..."
    if ! gh release download "$version" --repo 10XDev/rickover-cli --pattern "txg-linux-$version.tar.gz" --dir . 2>/dev/null; then
        print_error "Failed to download Linux binary"
        rm -rf "$temp_dir"
        return 1
    fi

    print_info "Downloading Windows binary from GitHub..."
    if ! gh release download "$version" --repo 10XDev/rickover-cli --pattern "txg-windows-$version.zip" --dir . 2>/dev/null; then
        print_error "Failed to download Windows binary"
        rm -rf "$temp_dir"
        return 1
    fi

    # Extract and copy binaries
    print_info "Extracting and installing binaries..."

    # macOS
    print_info "Extracting macOS binary..."
    unzip -q "txg-macos-$version.zip"
    # Check if txg is in root or in a subdirectory
    if [[ -f "txg" ]]; then
        mkdir -p "$bin_dir/darwin"
        cp txg "$bin_dir/darwin/"
        chmod +x "$bin_dir/darwin/txg"
    elif [[ -f "txg-macos-$version/txg" ]]; then
        mkdir -p "$bin_dir/darwin"
        cp "txg-macos-$version/txg" "$bin_dir/darwin/"
        chmod +x "$bin_dir/darwin/txg"
    else
        # List contents to debug
        print_error "Could not find txg binary after extraction. Archive contents:"
        ls -la
        rm -rf "$temp_dir"
        return 1
    fi

    # Linux
    print_info "Extracting Linux binary..."
    tar -xzf "txg-linux-$version.tar.gz"
    if [[ -f "txg" ]]; then
        mkdir -p "$bin_dir/linux"
        cp txg "$bin_dir/linux/"
        chmod +x "$bin_dir/linux/txg"
    elif [[ -f "txg-linux-$version/txg" ]]; then
        mkdir -p "$bin_dir/linux"
        cp "txg-linux-$version/txg" "$bin_dir/linux/"
        chmod +x "$bin_dir/linux/txg"
    else
        print_error "Could not find Linux txg binary after extraction"
        rm -rf "$temp_dir"
        return 1
    fi

    # Windows
    print_info "Extracting Windows binary..."
    unzip -q "txg-windows-$version.zip"
    if [[ -f "txg.exe" ]]; then
        mkdir -p "$bin_dir/windows"
        cp txg.exe "$bin_dir/windows/"
    elif [[ -f "txg-windows-$version/txg.exe" ]]; then
        mkdir -p "$bin_dir/windows"
        cp "txg-windows-$version/txg.exe" "$bin_dir/windows/"
    else
        print_error "Could not find Windows txg.exe binary after extraction"
        rm -rf "$temp_dir"
        return 1
    fi

    # Clean up
    cd - > /dev/null
    rm -rf "$temp_dir"

    print_success "Successfully downloaded and installed TXG CLI binaries ($version)"
    print_info "Binaries installed to:"
    print_info "  - macOS: $bin_dir/darwin/txg"
    print_info "  - Linux: $bin_dir/linux/txg"
    print_info "  - Windows: $bin_dir/windows/txg.exe"
}

# Show help
show_help() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
    download-bin [version]    Download TXG CLI binaries for all platforms
    prepare-build             Prepare build folder for validation (copy assets)
    pack                      Create MCP bundle (.mcpb file)
    run-server [token]        Run the MCP server locally for testing
                              Optional: access token (saved to credentials.txt)
    generate-capabilities     Generate capabilities reference documentation
    help                      Show this help message

    Examples:
    $0 download-bin            # Download latest version
    $0 download-bin v3.0.1     # Download specific version
    $0 prepare-build           # Prepare build folder for validation
    $0 pack                    # Create .mcpb bundle
    $0 run-server              # Run server (uses saved token from credentials.txt)
    $0 run-server TOKEN123     # Run server with new token
    $0 generate-capabilities   # Generate capabilities JSON reference

EOF
}

# Main command handler
main() {
    local command="${1:-}"
    shift || true

    case "$command" in
        run-server)
            run_server "$@"
            ;;
        prepare-build)
            prepare_build "$@"
            ;;
        pack)
            pack "$@"
            ;;
        download-bin)
            download_bin "$@"
            ;;
        generate-capabilities)
            generate_capabilities "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_error "No command specified\n"
            show_help
            exit 1
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"