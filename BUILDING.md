# Building YACL

This document provides instructions for building YACL executables from source.

## Overview

YACL uses Nuitka as the primary build system to create, standalone executables. Nuitka compiles Python code to C++ and creates native executables with better performance and easier distribution.

### Why Nuitka?

I tried first PyInstaller, it work fine, but Windows keep flagging the executable as a virus. Since I didn't want to deal with that, I decided to try Nuitka. It worked pretty well without much configuration, and it doesn't flag the executable as a virus. The only downside is that the build process is more slower than PyInstaller but since we dont plan to build often, it's not a big deal. 

## Prerequisites

### System Requirements

- **Python**: 3.11.9 ( For now we focus in on 3.11.9, but other versions should work as well)
- **Operating System**: Windows 10+ or Linux (Debian 12 or derivative)

### Required Tools

We use [Nuitka](https://nuitka.net/) for creating the standalone executables. Requirements for building with Nuitka are just Python and a C++ compiler.

#### Linux

Linux usually comes with Python and gcc. pyenv is recommended for managing Python versions.
- Python 3.11.9
- GCC (usually pre-installed)
- pyenv (optional but recommended for managing Python versions)

#### Windows

For running Nuitka on Windows you just need Python that you can download from the [official website](https://www.python.org/downloads/windows/). Nuitka will download and install the required C++ compiler automatically. But you can use different ones as specified in the [Nuitka documentation](https://nuitka.net/user-documentation/user-manual.html#c-compiler).

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-username/yacl.git
cd yacl
# Initialize submodules (Azure-ttk-theme)
git submodule update --init --recursive
```

### 2. Python Environment
```bash
# Using pyenv (recommended)
pyenv install 3.11.9
pyenv shell 3.11.9

# Create virtual environment
python -m venv .venv

# Activate environment
source .venv/bin/activate  # Linux
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install YACL
```bash
pip install -e .
```

## Building Process

Just run the build.py script. It will detect the platform and build the executable.

```bash
python build.py
```

More advanced build options are in progress.

## Build Artifacts

### Output Structure

After building, you'll find:

```
dist/
├── main.build/                 # Build cache (can be deleted)
├── main.dist/                  # Standalone distribution
├── yacl_{platform}.zip|tar.gz  # Distribution package
```

