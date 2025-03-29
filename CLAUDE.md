# Jekyll Site Guide (kelp.github.io)

## Build Commands
- `make serve` - Run local development server
- `make build` - Build site without serving
- `make new-post title="My Post"` - Create new blog post
- `make format` - Format markdown with 72-char line wrapping
- `make lint` - Check markdown formatting
- `make check` - Check for broken links

## Testing
- Test locally: `make serve` (http://localhost:4000)
- Run `make check` to verify link integrity

## Style Guidelines
- **Markdown**: GitHub Flavored Markdown with 72-char line wrapping
- **Front Matter**: Required for all content (title, layout, date for posts)
- **Content Structure**: 
  - Posts: _posts/YYYY-MM-DD-title.markdown
  - Pages: root directory with .md extension
- **Formatting**: Use prettier for consistent formatting
- **Naming**: kebab-case for files, snake_case for variables

## Content Best Practices
- Follow consistent pattern in existing posts
- Include appropriate categories
- Keep line length to 72 characters for readability
- Test all links before committing

## Deployment
- Site deploys automatically via GitHub Pages
- Manual deploy: `make deploy` (git push origin main)