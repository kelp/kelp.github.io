.PHONY: test test-verbose test-cov test-html setup-test clean-test help

help:
	@echo "Jekyll to Substack Cross-posting - Make Commands"
	@echo ""
	@echo "Available test commands:"
	@echo "  test           Run all tests"
	@echo "  test-verbose   Run tests with verbose output"
	@echo "  test-cov       Run tests with coverage reporting"
	@echo "  test-html      Run tests with HTML coverage report"
	@echo "  setup-test     Set up the test environment"
	@echo "  clean-test     Remove the test environment"
	@echo "  help           Show this help message"

setup-test:
	@echo "Setting up test environment..."
	@python3 -m venv test_env
	@source test_env/bin/activate && pip install pytest pytest-cov pyyaml markdown requests python-frontmatter
	@echo "Test environment set up successfully!"

test:
	@./.github/scripts/tests/run_tests.sh

test-verbose:
	@./.github/scripts/tests/run_tests.sh --verbose

test-cov:
	@./.github/scripts/tests/run_tests.sh --coverage

test-html:
	@./.github/scripts/tests/run_tests.sh --coverage --html

clean-test:
	@echo "Cleaning up test environment..."
	@rm -rf test_env coverage
	@echo "Test environment removed!"