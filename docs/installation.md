# Installation Guide

This document provides detailed installation instructions for the Xibo Screen Updater.

## Prerequisites

- Python 3.8 or higher
- NextCloud server with WebDAV access
- Xibo CMS with API access
- OAuth2 credentials for Xibo

## Installation Methods

### Method 1: Automated Setup Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/71walceli/XiboScreenUpdater.git
cd XiboScreenUpdater

# Run the setup script
./setup.sh

# For development environment
./setup.sh --dev
```

### Method 2: Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# For development dependencies
pip install -e ".[dev]"
```

### Method 3: Using Make

```bash
# See available commands
make help

# Setup for development
make setup-dev

# Basic setup
make setup
```

## Verification

After installation, verify everything works:

```bash
# Test that modules can be imported
python -c "import main, nextcloud_client, xibo_client; print('✅ All modules imported successfully')"

# Check console scripts are available
xibo-screen-updater --help
test-nextcloud --help
test-xibo --help
```

## Docker Installation

Test the installation in a clean environment:

```bash
# Test basic setup
docker run -it --rm -v $(pwd):/app -w /app python:3.12 bash -c "chmod +x setup.sh && ./setup.sh"

# Test module imports
make test-docker
```

## Troubleshooting

### Common Issues

1. **Python Version Error**
   ```bash
   # Check Python version
   python3 --version
   # Should be 3.8 or higher
   ```

2. **pip Installation Issues**
   ```bash
   # Upgrade pip
   pip install --upgrade pip
   
   # Clear cache if needed
   pip cache purge
   ```

3. **Permission Issues**
   ```bash
   # Don't use sudo with pip in virtual environment
   # Make sure you're in the virtual environment
   source .venv/bin/activate
   ```

4. **Missing Dependencies**
   ```bash
   # Install system dependencies (Ubuntu/Debian)
   sudo apt-get update
   sudo apt-get install python3-dev python3-pip python3-venv
   ```

### Virtual Environment Issues

```bash
# Remove and recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Next Steps

After successful installation:

1. Go to [Configuration Guide](configuration.md)
2. Set up your configuration file
3. Test connections with [Testing Guide](testing.md)
4. Start using the application with [Usage Guide](usage.md)
