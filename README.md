# YACL - Yet Another Cataclysm Launcher

A cross-platform desktop application for managing and launching Cataclysm game installations.

## Overview

YACL is a launcher that simplifies the process of downloading, installing, and managing all the different versions of Cataclysm games. Built with Python and Tkinter, inspired by [Catapult](https://github.com/qrrk/Catapult) by [qrrk](https://github.com/qrrk).

## Features

Right now, YACL is a work in progress. The initial features are:

- Data driven game support
- Full history list of Cataclysm games releases using [cataclysm-db](https://github.com/SrGnis/cataclysm-db)
- Download and install game releases
- Game installation and version management
- Game launching

More features are planned, including:

- Backup and restore
- Mod support
- Soundpack support
- Font support

## Requirements

- OS: Windows or Linux

The releases are built using [Nuitka](https://nuitka.net/) and are provided as standalone executables. They should run on any system with the appropriate operating system.

NOTE: Regarding MacOS: I don't own a Mac, so I have no way to test or build for MacOS. If you are a MacOS user and want to contribute, please feel free to do so. I would be happy to accept any pull requests that add MacOS support.

## Quick Start

### Installation

#### Releases

Releases are available on the [releases page](https://github.com/SrGnis/yacl/releases).

Download the latest release and run the executable directly.

#### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/yacl.git
   cd yacl
   # Initialize submodules (Azure-ttk-theme)
   git submodule update --init --recursive
   ```

2. Set up the environment:
   ```bash
   # Using pyenv (recommended but not required)
   pyenv install 3.11.9
   pyenv shell 3.11.9
   
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. Install the application:
   ```bash
   pip install .
   ```

4. Run the application:
   ```bash
   yacl
   ```

## Building

For more detailed build instructions, see [BUILDING.md](BUILDING.md).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Licenses

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This project also uses the [Azure-ttk-theme](https://github.com/rdbende/Azure-ttk-theme) by [rdbende](https://github.com/rdbende) which is licensed under the MIT License.
