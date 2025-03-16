# Build Commands
- `bundle install` - Install dependencies
- `bundle exec jekyll serve` - Run local server for development
- `bundle exec jekyll build` - Build site without serving
- `bundle exec jekyll serve --livereload` - Run with live reloading

# Testing
## Jekyll Site
- Check locally with `bundle exec jekyll serve` before committing

## Substack Cross-posting
- `make test` - Run tests for Substack cross-posting
- `make test-verbose` - Run tests with verbose output
- `make test-cov` - Run tests with coverage reporting
- `make test-html` - Run tests with HTML coverage report
- `make setup-test` - Set up test environment
- `make clean-test` - Remove test environment
- `./.github/scripts/tests/run_tests.sh --help` - View all test script options

# Style Guidelines
- **Naming**: Use kebab-case for files, snake_case for variables
- **Markdown**: Follow GitHub Flavored Markdown
- **HTML/CSS**: Follow conventions in _includes and _layouts
- **Front Matter**: Required for all content pages
  - title, layout, date for posts
  - title, layout for pages
- **Content Structure**:
  - Posts in _posts/ directory with YYYY-MM-DD-title.markdown naming
  - Pages in root with .md extension
  - Assets in assets/ directory

# CI/CD
- GitHub Actions workflow automatically deploys to GitHub Pages
- IMPORTANT: This repository must remain named `kelp.github.io` for GitHub Pages to function correctly with the custom domain

# Substack Cross-posting
- The site has automated cross-posting to Substack
- Posts in _posts/ can be published to Substack when pushed to the repository
- Configure with `substack_status: 'draft'` or `'published'` in frontmatter
- Set audience with `substack_audience: 'everyone'`, `'only_paid'`, or `'only_free'`
- Skip cross-posting with `skip_substack: true`
- Set a maximum of 1 post published per day (override with GitHub Secret `MAX_PUBLICATIONS_PER_DAY`)
- Force publish using the GitHub Actions workflow dispatch with "Force publish" option