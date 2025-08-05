#!/bin/bash
# Test script for Xibo Screen Updater setup in Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

cleanup() {
    print_status "Cleaning up Docker containers and images..."
    docker-compose -f docker-compose.test.yml down --remove-orphans 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
}

# Trap to cleanup on exit
trap cleanup EXIT

echo "🧪 Testing Xibo Screen Updater Setup in Clean Docker Environment"
echo "================================================================"

# Test 1: Minimal dependency test
print_status "Test 1: Testing minimal Python environment with core dependencies"
if docker-compose -f docker-compose.test.yml run --rm test-minimal; then
    print_success "Minimal dependency test passed"
else
    print_error "Minimal dependency test failed"
    exit 1
fi

echo ""

# Test 2: Basic setup test
print_status "Test 2: Testing basic setup script"
if docker-compose -f docker-compose.test.yml run --rm test-setup; then
    print_success "Basic setup test passed"
else
    print_error "Basic setup test failed"
    exit 1
fi

echo ""

# Test 3: Development setup test
print_status "Test 3: Testing development setup script"
if docker-compose -f docker-compose.test.yml run --rm test-setup-dev; then
    print_success "Development setup test passed"
else
    print_error "Development setup test failed"
    exit 1
fi

echo ""

# Test 4: Application import test
print_status "Test 4: Testing application imports after setup"
if docker-compose -f docker-compose.test.yml run --rm test-run; then
    print_success "Application import test passed"
else
    print_error "Application import test failed"
    exit 1
fi

echo ""
print_success "🎉 All tests passed! Setup script works correctly in clean environment."

echo ""
echo "Manual testing options:"
echo "- Interactive shell: docker-compose -f docker-compose.test.yml run --rm test-shell"
echo "- Custom test: docker-compose -f docker-compose.test.yml run --rm test-setup <your-commands>"
