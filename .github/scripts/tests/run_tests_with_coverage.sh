#!/bin/bash
# Helper script to run tests with coverage for the Jekyll to Substack cross-posting implementation

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Check if virtual environment exists
VENV_DIR="$REPO_ROOT/test_env"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    cd "$REPO_ROOT" && python3 -m venv test_env
fi

# Activate virtual environment and install dependencies if needed
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if ! python -c "import pytest_cov" &> /dev/null; then
    echo "Installing test dependencies..."
    pip install pytest pytest-cov pyyaml markdown requests python-frontmatter
fi

# Run tests with coverage
cd "$REPO_ROOT"
echo "Running tests with coverage..."
python -m pytest .github/scripts/tests/test_publish_to_substack.py -v --cov-report term --cov=.github/scripts

# Deactivate virtual environment
deactivate

echo -e "\nTests with coverage completed!"