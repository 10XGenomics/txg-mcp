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
    local token="${1:-}"
    local credentials_file="$SCRIPT_DIR/credentials.txt"
    local server_script="$SCRIPT_DIR/package/server/main.py"
    local lib_dir="$SCRIPT_DIR/package/lib"
    local access_token=""

    print_info "Starting MCP server..."

    # Check if server script exists
    if [[ ! -f "$server_script" ]]; then
        print_error "Server script not found: $server_script"
        return 1
    fi

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        return 1
    fi

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

    # Check if lib directory exists
    if [[ ! -d "$lib_dir" ]]; then
        print_warning "Dependencies directory not found: $lib_dir"
        print_info "Run 'install-requirements' first to install dependencies"
        read -p "Do you want to continue anyway? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi

    # Set up environment variables
    export PYTHONPATH="$lib_dir:${PYTHONPATH:-}"
    export ACCESS_TOKEN="$access_token"

    print_info "Environment setup:"
    print_info "  PYTHONPATH: $lib_dir"
    print_info "  ACCESS_TOKEN: ***${access_token: -4}"  # Show only last 4 chars

    # Trap to handle Ctrl+C gracefully
    trap 'print_info "Shutting down server..."; exit 0' INT TERM

    # Run the server
    print_info "Starting server (Press Ctrl+C to stop)..."
    print_info "Running: python3 $server_script"

    cd "$SCRIPT_DIR/package"
    python3 "$server_script"

    # Reset trap
    trap - INT TERM
}

# Generate capabilities reference documentation
generate_capabilities() {
    local credentials_file="$SCRIPT_DIR/credentials.txt"
    local server_script="$SCRIPT_DIR/package/server/main.py"
    local lib_dir="$SCRIPT_DIR/package/lib"
    local reference_dir="$SCRIPT_DIR/reference"
    local output_file="$reference_dir/mcp_capabilities_reference.json"
    local access_token=""

    print_info "Generating MCP capabilities reference..."

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        return 1
    fi

    # Check if server script exists
    if [[ ! -f "$server_script" ]]; then
        print_error "Server script not found: $server_script"
        return 1
    fi

    # Get access token from credentials file
    if [[ -f "$credentials_file" ]]; then
        access_token=$(cat "$credentials_file")
    else
        print_error "Access token required. Run 'run-server' with a token first to save credentials"
        return 1
    fi

    # Check if lib directory exists
    if [[ ! -d "$lib_dir" ]]; then
        print_error "Dependencies directory not found: $lib_dir"
        print_info "Run 'install-requirements' first to install dependencies"
        return 1
    fi

    # Create reference directory if it doesn't exist
    mkdir -p "$reference_dir"

    # Path to the query script
    local query_script="$SCRIPT_DIR/scripts/query_mcp_capabilities.py"

    # Check if query script exists
    if [[ ! -f "$query_script" ]]; then
        print_error "Query script not found: $query_script"
        return 1
    fi

    # Run the query script
    print_info "Querying server capabilities..."

    export PYTHONPATH="$lib_dir:${PYTHONPATH:-}"

    if python3 "$query_script" "$server_script" "$lib_dir" "$access_token" > "$output_file" 2>/tmp/mcp_query_error_$$.log; then
        # Clean up temp error log
        rm -f /tmp/mcp_query_error_$$.log

        # Pretty print and validate the output
        if python3 -m json.tool "$output_file" > "$output_file.tmp" 2>/dev/null; then
            mv "$output_file.tmp" "$output_file"

            # Count capabilities
            local tools_count=$(python3 -c "import json; print(len(json.load(open('$output_file')).get('tools', [])))" 2>/dev/null || echo "0")
            local resources_count=$(python3 -c "import json; print(len(json.load(open('$output_file')).get('resources', [])))" 2>/dev/null || echo "0")
            local prompts_count=$(python3 -c "import json; print(len(json.load(open('$output_file')).get('prompts', [])))" 2>/dev/null || echo "0")

            print_success "Successfully generated capabilities reference: $output_file"
            print_info "Found: $tools_count tools, $resources_count resources, $prompts_count prompts"
        else
            print_error "Generated file is not valid JSON"
            return 1
        fi
    else
        print_error "Failed to query server capabilities"
        print_info "Error log: /tmp/mcp_query_error_$$.log"

        # Show error log if exists
        if [[ -f /tmp/mcp_query_error_$$.log ]]; then
            print_error "Error details:"
            cat /tmp/mcp_query_error_$$.log
            rm -f /tmp/mcp_query_error_$$.log
        fi

        return 1
    fi
}

# Run tests
run_tests() {
    print_info "Running tests..."

    local tests_dir="$SCRIPT_DIR/tests"
    local lib_dir="$SCRIPT_DIR/package/lib"
    local venv_dir="$SCRIPT_DIR/.venv_test"
    local test_type="${1:-all}"  # Optional test type parameter

    # Check if tests directory exists
    if [[ ! -d "$tests_dir" ]]; then
        print_error "Tests directory not found: $tests_dir"
        return 1
    fi

    # Check if dependencies are installed
    if [[ ! -d "$lib_dir" ]]; then
        print_warning "Dependencies not found in $lib_dir"
        print_info "Installing requirements first..."
        install_requirements || return 1
    fi

    # Create or activate test virtual environment
    if [[ ! -d "$venv_dir" ]]; then
        print_info "Creating test virtual environment..."
        python3 -m venv "$venv_dir"
        if [[ $? -ne 0 ]]; then
            print_error "Failed to create virtual environment"
            return 1
        fi
    fi

    # Activate virtual environment
    source "$venv_dir/bin/activate"

    # Install/upgrade test dependencies
    print_info "Installing test dependencies..."
    pip install --upgrade pip >/dev/null 2>&1
    if ! pip install -r "$tests_dir/requirements.txt" >/dev/null 2>&1; then
        print_error "Failed to install test dependencies"
        deactivate
        return 1
    fi

    # Set environment variables
    export PYTHONPATH="$SCRIPT_DIR:$lib_dir:$SCRIPT_DIR/package:$SCRIPT_DIR/package/server:${PYTHONPATH:-}"
    export ACCESS_TOKEN="${ACCESS_TOKEN:-test_token}"

    # Run pytest based on test type
    case "$test_type" in
        all)
            print_info "Running all tests..."
            pytest "$tests_dir" -v
            ;;
        unit)
            print_info "Running unit tests..."
            pytest "$tests_dir" -v -m "not integration"
            ;;
        integration)
            print_info "Running integration tests..."
            pytest "$tests_dir" -v -m "integration"
            ;;
        coverage)
            print_info "Running tests with coverage..."
            pytest "$tests_dir" -v --cov=package/server --cov-report=term-missing --cov-report=html
            print_success "Coverage report saved to htmlcov/index.html"
            ;;
        quick)
            print_info "Running quick smoke tests..."
            pytest "$tests_dir/test_response_handling.py" "$tests_dir/test_command_building.py" -v
            ;;
        protocol)
            print_info "Running MCP protocol tests..."
            pytest "$tests_dir/test_mcp_protocol.py" -v
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_info "Valid options: all, unit, integration, coverage, quick, protocol"
            return 1
            ;;
    esac

    local exit_code=$?

    # Deactivate virtual environment
    deactivate

    if [[ $exit_code -eq 0 ]]; then
        print_success "✅ All tests passed!"
    else
        print_error "❌ Some tests failed (exit code: $exit_code)"
    fi

    return $exit_code
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
    run-server [token]      Run the MCP server locally for testing
                            Optional: access token (saved to credentials.txt)
    generate-capabilities   Generate capabilities reference documentation
    run-tests [type]        Run test suite
                            Types: all (default), unit, integration, coverage, quick, protocol
    help                    Show this help message

Examples:
    $0 download-bin         # Download latest version
    $0 download-bin v3.0.1  # Download specific version
    $0 install-requirements # Install Python dependencies
    $0 pack                 # Create .mcpb bundle
    $0 run-server           # Run server (uses saved token)
    $0 run-server TOKEN123  # Run server with new token
    $0 run-tests            # Run all tests
    $0 run-tests coverage   # Run tests with coverage report

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
            run_server "${2:-}"
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