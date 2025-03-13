#!/bin/bash
# Script to run tests for the Jekyll to Substack cross-posting implementation

# Set colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_DIR="$REPO_ROOT/test_env"

# Set variables
PYTHON_SCRIPT="$REPO_ROOT/.github/scripts/publish_to_substack.py"
TEST_SCRIPT="$REPO_ROOT/.github/scripts/tests/test_publish_to_substack.py"

# Parse command line arguments
VERBOSE=false
COVERAGE=false
HTML_REPORT=false
SKIP_SETUP=false

print_help() {
    echo -e "${BOLD}Usage: $0 [options]${NC}"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -v, --verbose       Run tests in verbose mode"
    echo "  -c, --coverage      Show coverage report"
    echo "  --html              Generate HTML coverage report"
    echo "  --skip-setup        Skip environment setup (use existing env)"
    echo ""
}

for arg in "$@"; do
    case $arg in
        -h|--help)
            print_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            ;;
        -c|--coverage)
            COVERAGE=true
            ;;
        --html)
            HTML_REPORT=true
            COVERAGE=true
            ;;
        --skip-setup)
            SKIP_SETUP=true
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            print_help
            exit 1
            ;;
    esac
done

# Setup virtual environment if needed
if [ "$SKIP_SETUP" = false ]; then
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
    fi

    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"

    # Install dependencies if needed
    if ! python -c "import pytest" &> /dev/null; then
        echo -e "${YELLOW}Installing test dependencies...${NC}"
        pip install pytest pytest-cov pyyaml markdown requests python-frontmatter
    fi
else
    # Just activate the virtual environment
    source "$VENV_DIR/bin/activate"
fi

# Prepare test command
TEST_CMD="python -m pytest $TEST_SCRIPT"

if [ "$VERBOSE" = true ]; then
    TEST_CMD="$TEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    # Add coverage options
    TEST_CMD="$TEST_CMD --cov=.github/scripts"
    
    if [ "$HTML_REPORT" = true ]; then
        # Create directory for coverage report
        COVERAGE_DIR="$REPO_ROOT/coverage"
        mkdir -p "$COVERAGE_DIR"
        TEST_CMD="$TEST_CMD --cov-report=html:$COVERAGE_DIR"
        echo -e "${YELLOW}Will generate HTML coverage report in $COVERAGE_DIR${NC}"
    else
        TEST_CMD="$TEST_CMD --cov-report=term-missing"
    fi
fi

# Run the tests
echo -e "${YELLOW}Running tests...${NC}"
cd "$REPO_ROOT" && eval "$TEST_CMD"
TEST_RESULT=$?

# Generate and show the coverage report if requested
if [ "$HTML_REPORT" = true ] && [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}Opening HTML coverage report...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$COVERAGE_DIR/index.html"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v xdg-open > /dev/null; then
            xdg-open "$COVERAGE_DIR/index.html"
        else
            echo -e "${YELLOW}HTML report generated at: $COVERAGE_DIR/index.html${NC}"
        fi
    else
        echo -e "${YELLOW}HTML report generated at: $COVERAGE_DIR/index.html${NC}"
    fi
fi

# Print summary
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}${BOLD}Tests completed successfully!${NC}"
else
    echo -e "${RED}${BOLD}Tests failed!${NC}"
fi

# Deactivate virtual environment
deactivate

exit $TEST_RESULT