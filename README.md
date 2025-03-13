# kelp.github.io

[![Test Coverage: 99%](https://img.shields.io/badge/test%20coverage-99%25-brightgreen.svg)](https://github.com/kelp.github.io)
[![Tests: Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/kelp.github.io)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Jekyll to Substack Cross-posting

This Jekyll site has an automated workflow that cross-posts blog content to Substack whenever new posts are pushed to the repository.

### How It Works

1. When you push changes to posts in the `_posts` directory, a GitHub Actions workflow is triggered.
2. The workflow identifies which posts were changed in the latest commit.
3. It processes these posts and publishes them to your Substack publication.

### Configuration

#### GitHub Secrets

To make this work, you need to add the following secrets to your GitHub repository:

1. Go to your repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add the following secrets:
   - `SUBSTACK_API_KEY`: Your Substack API key
   - `SUBSTACK_PUBLICATION`: Your Substack publication name (e.g., "yourpublication")
   - `MAX_PUBLICATIONS_PER_DAY`: (Optional) Maximum number of posts to publish per day (default: 1)

#### Post Frontmatter Options

You can control how posts are published to Substack by adding the following frontmatter options:

```yaml
---
title: My Blog Post
layout: post
date: 2025-03-12
# Substack specific options
substack_status: 'draft'    # 'draft' or 'published' (default: 'draft')
substack_audience: 'everyone'  # 'everyone', 'only_paid', or 'only_free' (default: 'everyone')
skip_substack: false        # Set to true to completely skip publishing to Substack
---
```

Posts marked as drafts in Jekyll (`draft: true` or `published: false`) will be skipped and not published to Substack.

### Anti-Spam Safeguards

The workflow includes several safeguards to prevent accidental spam:

1. **Rate Limiting**: By default, only 1 post is published per day. You can change this by setting the `MAX_PUBLICATIONS_PER_DAY` secret.
2. **Duplicate Detection**: The system won't publish the same content twice.
3. **Title Checking**: Posts with identical titles to existing Substack posts are skipped.
4. **Content Hashing**: Each published post is tracked to prevent republishing if edited.

You can bypass these limits for specific cases:

1. Manually run the workflow from Actions tab with "Force publish" option enabled
2. Set the `skip_substack: true` frontmatter to completely skip specific posts

### Troubleshooting

If you encounter issues with the cross-posting workflow:

1. Check the GitHub Actions logs for details about any errors.
2. Verify that your Substack API key and publication name are correct.
3. Ensure your posts have valid frontmatter.
4. If posts aren't being published due to rate limits, check the workflow logs or manually run with "Force publish" enabled.

### Testing

[![Tests: 29 passing](https://img.shields.io/badge/tests-29%20passing-brightgreen.svg)](https://github.com/kelp.github.io)
[![Main Script Coverage: 98%](https://img.shields.io/badge/script%20coverage-98%25-brightgreen.svg)](https://github.com/kelp.github.io)
[![Overall Coverage: 99%](https://img.shields.io/badge/overall%20coverage-99%25-brightgreen.svg)](https://github.com/kelp.github.io)

The cross-posting script includes comprehensive tests to ensure it works correctly without actually posting to Substack. We've provided several ways to run the tests:

#### Using Make Commands

The simplest way to run tests is with Make:

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage reporting
make test-cov

# Run tests with HTML coverage report (opens in browser)
make test-html

# Set up the test environment
make setup-test

# Clean up the test environment
make clean-test

# Show help
make help
```

#### Using Shell Script Directly

You can also run tests with more options using the provided shell script:

```bash
# Run basic tests
./.github/scripts/tests/run_tests.sh

# See all available options
./.github/scripts/tests/run_tests.sh --help

# Run with verbose output
./.github/scripts/tests/run_tests.sh --verbose

# Run with coverage report
./.github/scripts/tests/run_tests.sh --coverage

# Generate HTML coverage report
./.github/scripts/tests/run_tests.sh --coverage --html

# Skip environment setup (faster if already set up)
./.github/scripts/tests/run_tests.sh --skip-setup
```

#### Manually Running Tests

If you prefer, you can run the tests manually:

```bash
# Create and activate virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install dependencies
pip install pytest pytest-cov pyyaml markdown requests python-frontmatter

# Run tests
python -m pytest .github/scripts/tests/test_publish_to_substack.py -v

# Run tests with coverage
python -m pytest .github/scripts/tests/test_publish_to_substack.py -v --cov-report term --cov=.github/scripts
```

The tests verify:
- Correct processing of frontmatter and markdown
- Proper rate limiting and cache management
- Safe API interaction (without making actual calls)
- Handling of draft posts, duplicate detection, etc.

Tests are also automatically run in GitHub Actions when changes are made to the script or test files.