#!/bin/bash
# Setup script for Xibo Screen Updater

set -e

echo "🚀 Setting up Xibo Screen Updater..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_success "Python $python_version is compatible (>= $required_version)"
else
    print_error "Python $python_version is not compatible. Please install Python >= $required_version"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 not found. Please install pip3"
    exit 1
fi

VENV=".venv"
# Create virtual environment if it doesn't exist
if [ ! -d ${VENV} ]; then
    print_status "Creating virtual environment..."
    python3 -m venv ${VENV}
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source ${VENV}/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
print_status "Installing Xibo Screen Updater in development mode..."
pip install -e .

# Install development dependencies if requested
if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
    print_status "Installing development dependencies..."
    pip install -e ".[dev]"
    
    # Install pre-commit hooks
    print_status "Setting up pre-commit hooks..."
    pre-commit install
    print_success "Pre-commit hooks installed"
fi

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    print_status "Creating config directory..."
    mkdir -p config
fi

# Copy example config if it doesn't exist
if [ ! -f "config.yaml" ] && [ -f "config/example.yaml" ]; then
    print_status "Creating config.yaml from example..."
    cp config/example.yaml config.yaml
    print_warning "Please edit config.yaml with your actual credentials"
elif [ ! -f "config.yaml" ]; then
    print_warning "No config.yaml found. Please create one from config/example.yaml"
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    print_status "Creating data directory..."
    mkdir -p data
fi

# Create logs directory
if [ ! -d "logs" ]; then
    print_status "Creating logs directory..."
    mkdir -p logs
fi

print_success "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Edit config.yaml with your credentials"
echo "3. Test connections:"
echo "   - test-nextcloud"
echo "   - test-xibo"
echo "4. Run the application:"
echo "   - xibo-screen-updater                    # Uses ./config.yaml"
echo "   - xibo-screen-updater -c /path/to/config.yaml"
echo "   - CONFIG_PATH=/path/to/config.yaml xibo-screen-updater"
echo ""
echo "For development:"
echo "- Run tests: pytest"
echo "- Format code: black ."
echo "- Check linting: flake8 ."
echo "- Type checking: mypy ."
