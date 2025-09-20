#!/bin/bash

# MCP Bundle Development Tasks Script
# This script provides common development tasks for the TXG MCP bundle

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Download binary files for TXG CLI
download_bin() {
    local version="${1:-latest}"
    local bin_dir="$SCRIPT_DIR/package/bin"
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

# Install Python requirements/dependencies
download_requirements() {
    local requirements_file="$SCRIPT_DIR/package/requirements.txt"
    local lib_dir="$SCRIPT_DIR/package/lib"

    print_info "Installing Python requirements..."

    # Check if requirements.txt exists
    if [[ ! -f "$requirements_file" ]]; then
        print_error "requirements.txt not found at: $requirements_file"
        return 1
    fi

    # Check if Python/pip are available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        return 1
    fi

    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip is required but not found"
        return 1
    fi

    # Determine pip command
    local pip_cmd="pip3"
    if ! command -v pip3 &> /dev/null; then
        pip_cmd="pip"
    fi

    # Check if lib directory exists and has content
    if [[ -d "$lib_dir" ]] && [[ "$(ls -A $lib_dir 2>/dev/null)" ]]; then
        print_warning "Dependencies already exist in package/lib/"
        read -p "Do you want to reinstall/update all dependencies? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Download cancelled"
            return 0
        fi
    fi

    # Create lib directory if it doesn't exist
    mkdir -p "$lib_dir"

    # Install requirements to lib directory
    print_info "Installing dependencies to package/lib/..."
    print_info "Running: $pip_cmd install -r $requirements_file --target $lib_dir --upgrade --force-reinstall"

    if $pip_cmd install -r "$requirements_file" --target "$lib_dir" --upgrade --force-reinstall; then
        print_success "Successfully installed all dependencies to package/lib/"

        # Count installed packages
        local package_count=$(ls -d "$lib_dir"/*.dist-info 2>/dev/null | wc -l | tr -d ' ')
        print_info "Installed $package_count packages to $lib_dir"
    else
        print_error "Failed to install dependencies"
        return 1
    fi
}

# Pack the MCP bundle (.mcpb file)
pack() {
    local package_dir="$SCRIPT_DIR/package"
    local build_dir="$SCRIPT_DIR/build"
    local output_file="$build_dir/txg.mcpb"

    print_info "Packing MCP bundle..."

    # Check if mcpb command is available
    if ! command -v mcpb &> /dev/null; then
        print_error "mcpb command not found. Please install it first."
        print_info "Installation: npm install -g @anthropic-ai/mcpb"
        return 1
    fi

    # Check if package directory exists
    if [[ ! -d "$package_dir" ]]; then
        print_error "Package directory not found: $package_dir"
        return 1
    fi

    # Check if manifest.json exists
    if [[ ! -f "$package_dir/manifest.json" ]]; then
        print_error "manifest.json not found in package directory"
        return 1
    fi

    # Create build directory if it doesn't exist
    mkdir -p "$build_dir"

    # Run mcpb pack command
    print_info "Running: mcpb pack $package_dir $output_file"

    if mcpb pack "$package_dir" "$output_file"; then
        # Get file size
        local file_size=$(ls -lh "$output_file" | awk '{print $5}')
        print_success "Successfully created MCP bundle: $output_file ($file_size)"

        # Verify the bundle is a valid zip
        if unzip -t "$output_file" >/dev/null 2>&1; then
            print_info "Bundle integrity verified"
        else
            print_warning "Bundle created but may have integrity issues"
        fi
    else
        print_error "Failed to create MCP bundle"
        return 1
    fi
}

# Run the MCP server locally for testing
run_server() {
    print_info "Running MCP server..."

    # TODO: Implement server run logic
    # - Set up Python path
    # - Set environment variables
    # - Run python package/server/main.py
    # - Handle graceful shutdown

    print_warning "run-server: Not yet implemented"
}

# Generate capabilities reference documentation
generate_capabilities() {
    print_info "Generating capabilities reference..."

    # TODO: Implement capabilities generation logic
    # - Extract tools from server code
    # - Generate markdown documentation
    # - Include parameter descriptions
    # - Create README or reference doc

    print_warning "generate-capabilities: Not yet implemented"
}

# Run tests
run_tests() {
    print_info "Running tests..."

    # TODO: Implement test runner logic
    # - Discover test files
    # - Run Python tests (pytest/unittest)
    # - Generate coverage report if applicable
    # - Return appropriate exit code

    print_warning "run-tests: Not yet implemented"
}

# Show usage information
show_help() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
    download-bin [version]  Download TXG CLI binary files for all platforms
                            Optional: version (e.g., v3.0.1) or 'latest' (default)
    install-requirements    Install Python dependencies to package/lib
    pack                    Create MCP bundle (.mcpb file) from package directory
    run-server              Run the MCP server locally for testing
    generate-capabilities   Generate capabilities reference documentation
    run-tests               Run test suite
    help                    Show this help message

Examples:
    $0 download-bin         # Download latest version
    $0 download-bin v3.0.1  # Download specific version
    $0 install-requirements # Install Python dependencies
    $0 pack                 # Create .mcpb bundle

EOF
}

# Main command handler
main() {

    # Handle commands
    case "${1:-}" in
        download-bin)
            download_bin "${2:-latest}"
            ;;
        install-requirements|install-reqs)
            download_requirements
            ;;
        pack)
            pack
            ;;
        run-server)
            run_server
            ;;
        generate-capabilities)
            generate_capabilities
            ;;
        run-tests)
            run_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"