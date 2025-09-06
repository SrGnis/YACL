#!/usr/bin/env python3
"""
Cross-platform build script for YACL using Nuitka
This script can build executables for both Windows and Linux using Nuitka compiler
"""

import os
import sys
import platform
import subprocess
import shutil
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            text=True,
            shell=isinstance(cmd, str)
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_python_version():
    """Check if Python version is sufficient."""
    if sys.version_info < (3, 11):
        print(f"ERROR: Python {sys.version_info.major}.{sys.version_info.minor} is installed, "
                f"but Python 3.11 or higher is required")
        return False
    print(f"Using Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("Installing/updating dependencies...")
    
    # Upgrade pip first
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    if not success:
        print(f"Failed to upgrade pip: {stderr}")
        return False
    
    # Install requirements
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if not success:
        print(f"Failed to install requirements: {stderr}")
        return False
    
    print("Dependencies installed successfully")
    return True


def clean_build_artifacts():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")

    # Remove all files and folders in dist/
    dist_dir = Path("dist")
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


def build_executable(target_platform, onefile=False):
    """Build the executable using Nuitka."""
    build_type = "onefile" if onefile else "standalone"
    print(f"Building {target_platform} {build_type} executable...")

    # Build Nuitka command
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile" if onefile else "--standalone",
        "--output-dir=dist",
        f"--output-filename=yacl",
        "--enable-plugin=tk-inter",
        "--enable-plugin=anti-bloat",
        "--python-flag=-O",
        "--assume-yes-for-downloads",
        "--include-data-dir=src/yacl/resources=resources",
        "src/yacl/main.py"
    ]

    # Add platform-specific options
    if target_platform == "windows":
        nuitka_cmd.extend([
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=src/yacl/resources/assets/icons/yacl.ico" if Path("src/yacl/resources/assets/icons/yacl.ico").exists() else ""
        ])
        # Remove empty icon option if file doesn't exist
        nuitka_cmd = [arg for arg in nuitka_cmd if arg]

    success, stdout, stderr = run_command(nuitka_cmd)

    if not success:
        print(f"Build failed: {stderr}")
        return False

    print("Build completed successfully!")
    return True


def create_distribution_package(target_platform, onefile=False):
    """Create a distribution package from Nuitka's output."""
    print("Creating distribution package...")

    if onefile:
        # For onefile builds, Nuitka creates a single executable in dist/
        exe_extension = ".exe" if target_platform == "windows" else ""
        exe_name = f"yacl{exe_extension}"
        exe_path = Path("dist") / exe_name

        if not exe_path.exists():
            print(f"ERROR: Onefile executable {exe_path} not found")
            return False

        # Create a distribution directory with the executable and docs
        dist_dir = Path("dist") / f"yacl_{target_platform}"
        if dist_dir.exists():
            if dist_dir.is_dir():
                shutil.rmtree(dist_dir)
            else:
                dist_dir.unlink()  # Remove if it's a file
        dist_dir.mkdir(parents=True)

        # Copy the executable
        shutil.copy2(exe_path, dist_dir / exe_name)

        # Copy documentation files
        for doc_file in ["README.md", "LICENSE", "CHANGELOG.md"]:
            doc_path = Path(doc_file)
            if doc_path.exists():
                shutil.copy2(doc_path, dist_dir / doc_file)

    else:
        # For standalone builds, Nuitka creates a directory structure in dist/main.dist/
        nuitka_output_dir = Path("dist") / "main.dist"

        if not nuitka_output_dir.exists():
            print(f"ERROR: Nuitka output directory {nuitka_output_dir} not found")
            return False

        # Create a clean distribution directory
        dist_dir = Path("dist") / f"yacl_{target_platform}"
        if dist_dir.exists():
            if dist_dir.is_dir():
                shutil.rmtree(dist_dir)
            else:
                dist_dir.unlink()  # Remove if it's a file
        dist_dir.mkdir(parents=True)

        # Copy the entire Nuitka standalone directory contents
        for item in nuitka_output_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, dist_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, dist_dir / item.name)

        # Copy documentation files
        for doc_file in ["README.md", "LICENSE", "CHANGELOG.md"]:
            doc_path = Path(doc_file)
            if doc_path.exists():
                shutil.copy2(doc_path, dist_dir / doc_file)

    # Create archive
    if target_platform == "windows":
        # Create a zip file for Windows
        archive_name = f"yacl_{target_platform}.zip"
        shutil.make_archive(
            str(Path("dist") / "yacl_windows"),
            'zip',
            str(Path("dist")),
            f"yacl_{target_platform}"
        )
        print(f"Created {archive_name}")
    else:
        # Create a tar.gz file for Linux
        archive_name = f"yacl_{target_platform}.tar.gz"
        shutil.make_archive(
            str(Path("dist") / f"yacl_{target_platform}"),
            'gztar',
            str(Path("dist")),
            f"yacl_{target_platform}"
        )
        print(f"Created {archive_name}")

    return True


def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Build YACL executable")
    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "auto"],
        default="auto",
        help="Target platform (default: auto-detect)"
    )
    parser.add_argument(
        "--no-package",
        action="store_true",
        help="Skip creating distribution package"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean build artifacts and exit"
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Build a single executable file instead of a standalone directory"
    )
    
    args = parser.parse_args()
    
    # Determine target platform
    if args.platform == "auto":
        current_platform = platform.system().lower()
        if current_platform == "windows":
            target_platform = "windows"
        elif current_platform == "linux":
            target_platform = "linux"
        else:
            print(f"ERROR: Unsupported platform: {current_platform}")
            print("Supported platforms: windows, linux")
            return 1
    else:
        target_platform = args.platform

    build_type = "onefile" if args.onefile else "standalone"
    print("=" * 50)
    print(f"Building YACL for {target_platform} ({build_type})")
    print("=" * 50)

    # Clean build artifacts
    clean_build_artifacts()

    if args.clean_only:
        print("Clean completed.")
        return 0

    # Check Python version
    if not check_python_version():
        return 1

    # Install dependencies
    if not install_dependencies():
        return 1

    # Build executable
    if not build_executable(target_platform, args.onefile):
        return 1

    # Create distribution package
    if not args.no_package:
        create_distribution_package(target_platform, args.onefile)
    
    print()
    print("=" * 50)
    print(f"{target_platform.title()} {build_type} build complete!")
    print("=" * 50)
    print()
    print(f"Distribution location: dist/yacl_{target_platform}/")
    if args.onefile:
        print(f"Single executable file created in the yacl_{target_platform} folder")
        print("Note: Nuitka onefile builds create a single executable with all dependencies included.")
    else:
        print(f"You can distribute the entire yacl_{target_platform} folder to users")
        print("Note: Nuitka creates a standalone distribution with all dependencies included.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
