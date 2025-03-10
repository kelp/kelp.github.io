# Build Commands
- `bundle install` - Install dependencies
- `bundle exec jekyll serve` - Run local server for development
- `bundle exec jekyll build` - Build site without serving
- `bundle exec jekyll serve --livereload` - Run with live reloading

# Testing
- No formal test suite detected
- Check locally with `bundle exec jekyll serve` before committing

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