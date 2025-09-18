#!/usr/bin/env python3

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional
from unittest import result

class TxgCli:
    """Manager for bundled txg CLI binaries"""
    
    def __init__(self):
        self._txg_path = None
        self._platform = self._get_platform()
        self._package_dir = Path(__file__).parent.parent
    
    def _get_platform(self) -> str:
        system = platform.system().lower()
        
        # Raise error if system is not one of the supported platforms
        if system not in ("darwin", "linux", "windows"):
            raise RuntimeError(f"Unsupported operating system: {system}")
        return system
    
    def get_txg_path(self) -> str:
        """Get path to bundled txg CLI binary"""
        if self._txg_path is None:
            self._txg_path = self._find_bundled_binary()
        return self._txg_path
    
    def _find_bundled_binary(self) -> str:
        """Find the appropriate bundled binary for this platform"""
        
        # Construct platform directory name and executable name
        exe_name = "txg.exe" if self._platform == "windows" else "txg"
        
        # Build path to binary
        binary_path = self._package_dir / "bin" / self._platform / exe_name
        
        # Verify the binary exists
        if not binary_path.exists():
            raise RuntimeError(
                f"txg binary not found at {binary_path}. "
            )
        
        # Ensure it's executable on Unix systems
        if self._platform != "windows":
            os.chmod(binary_path, 0o755)
        
        return str(binary_path)
    
    def run_command(self, args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a txg CLI command with the bundled binary"""
        txg_path = self.get_txg_path()
        full_command = [txg_path] + args
        
        try:
            process = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )          

            return process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Command timed out after {timeout}s: {' '.join(full_command)}")
        except Exception as e:
            raise RuntimeError(f"Failed to run command: {e}")

txg_cli = TxgCli()