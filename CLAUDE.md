# Build Commands

## Using Makefile
- `make help` - Show all available commands
- `make install` - Install dependencies
- `make serve` - Run local server for development
- `make serve-live` - Run with live reloading
- `make build` - Build site without serving
- `make clean` - Clean the build directory
- `make draft` - Run Jekyll with drafts enabled
- `make new-post title="My New Post"` - Create a new blog post
- `make deploy` - Push changes to GitHub Pages

## Direct Commands
- `bundle install` - Install dependencies
- `bundle exec jekyll serve` - Run local server for development
- `bundle exec jekyll build` - Build site without serving
- `bundle exec jekyll serve --livereload` - Run with live reloading

# Testing
## Jekyll Site
- Check locally with `make serve` or `bundle exec jekyll serve` before committing
- Run `make check` to check for broken links

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

# Communication Guidelines
- Do not hallucinate or make up information
- Be explicit when you're not sure about how to do something
- Admit when you don't know the answer to a question
- Ask clarifying questions when needed

