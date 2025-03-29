.PHONY: help install serve build clean draft new-post deploy check check-links check-html check-markdown lint lint-html lint-markdown format

# Colors for output
RESET = \033[0m
BOLD = \033[1m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
MAGENTA = \033[35m

help:
	@echo "$(BOLD)Jekyll Site Management$(RESET)"
	@echo ""
	@echo "Available commands:"
	@echo "  $(GREEN)make help$(RESET)        - Show this help message"
	@echo "  $(GREEN)make install$(RESET)     - Install dependencies"
	@echo "  $(GREEN)make serve$(RESET)       - Run Jekyll locally (http://localhost:4000)"
	@echo "  $(GREEN)make serve-live$(RESET)  - Run Jekyll with live reload"
	@echo "  $(GREEN)make build$(RESET)       - Build the site to _site/ directory"
	@echo "  $(GREEN)make clean$(RESET)       - Clean the build directory"
	@echo "  $(GREEN)make draft$(RESET)       - Run Jekyll with drafts enabled"
	@echo "  $(GREEN)make new-post$(RESET)    - Create a new post (use with title=...)"
	@echo "  $(GREEN)make deploy$(RESET)      - Deploy to GitHub Pages (git push)"
	@echo "  $(GREEN)make check$(RESET)       - Run all checks"
	@echo "  $(GREEN)make check-links$(RESET) - Check for broken links"
	@echo "  $(GREEN)make lint$(RESET)        - Run all linters"
	@echo "  $(GREEN)make format$(RESET)      - Format markdown posts to wrap at 78 characters"
	@echo ""
	@echo "Examples:"
	@echo "  $(YELLOW)make new-post title=\"My New Blog Post\"$(RESET)"
	@echo "  $(YELLOW)make serve$(RESET)"

install:
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	bundle install

serve:
	@echo "$(BLUE)Starting Jekyll server...$(RESET)"
	@echo "$(YELLOW)Site will be available at http://localhost:4000$(RESET)"
	bundle exec jekyll serve

serve-live:
	@echo "$(BLUE)Starting Jekyll server with live reload...$(RESET)"
	@echo "$(YELLOW)Site will be available at http://localhost:4000$(RESET)"
	bundle exec jekyll serve --livereload

build:
	@echo "$(BLUE)Building site...$(RESET)"
	JEKYLL_ENV=production bundle exec jekyll build

clean:
	@echo "$(BLUE)Cleaning build directory...$(RESET)"
	bundle exec jekyll clean
	rm -rf .jekyll-cache

draft:
	@echo "$(BLUE)Starting Jekyll server with drafts...$(RESET)"
	@echo "$(YELLOW)Site will be available at http://localhost:4000$(RESET)"
	bundle exec jekyll serve --drafts

new-post:
	@if [ -z "$(title)" ]; then \
		echo "$(MAGENTA)Error: Missing title parameter$(RESET)"; \
		echo "Usage: make new-post title=\"My New Blog Post\""; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating new post: $(title)$(RESET)"
	@date_prefix=`date +%Y-%m-%d`; \
	slug=`echo "$(title)" | tr '[:upper:]' '[:lower:]' | sed -e 's/[^[:alnum:]]/-/g' -e 's/--*/-/g' -e 's/^-//' -e 's/-$$//'`; \
	filename="_posts/$${date_prefix}-$${slug}.markdown"; \
	echo "---" > $$filename; \
	echo "layout: post" >> $$filename; \
	echo "title: \"$(title)\"" >> $$filename; \
	echo "date: `date +%Y-%m-%d`" >> $$filename; \
	echo "categories: []" >> $$filename; \
	echo "---" >> $$filename; \
	echo "" >> $$filename; \
	echo "Write your post content here." >> $$filename; \
	echo "$(GREEN)Created new post: $$filename$(RESET)"

deploy:
	@echo "$(BLUE)Deploying to GitHub Pages...$(RESET)"
	git push origin main

check: check-links

check-links:
	@echo "$(BLUE)Checking for broken links...$(RESET)"
	bundle exec jekyll build
	bundle exec jekyll doctor

lint: lint-markdown

lint-markdown:
	@echo "$(BLUE)Checking markdown formatting with Prettier...$(RESET)"
	@echo "$(YELLOW)Note: This requires prettier installed via npm$(RESET)"
	@if command -v prettier > /dev/null; then \
		prettier --check "_posts/*.markdown" *.md --prose-wrap=always --print-width=78 || echo "$(MAGENTA)Formatting issues found$(RESET)"; \
	else \
		echo "$(MAGENTA)prettier not found. Install with: npm install -g prettier$(RESET)"; \
	fi

format:
	@echo "$(BLUE)Formatting markdown files with Prettier...$(RESET)"
	@if command -v prettier > /dev/null; then \
		prettier --write "_posts/*.markdown" --prose-wrap=always --print-width=78; \
		echo "$(GREEN)Markdown files formatted successfully$(RESET)"; \
	else \
		echo "$(MAGENTA)prettier not found. Install with: npm install -g prettier$(RESET)"; \
	fi

lint-html:
	@echo "$(BLUE)Linting HTML files...$(RESET)"
	@echo "$(YELLOW)Note: This requires htmlhint installed via npm$(RESET)"
	@if command -v htmlhint > /dev/null; then \
		find _site -name "*.html" -print0 | xargs -0 htmlhint || echo "$(MAGENTA)HTML linting found issues$(RESET)"; \
	else \
		echo "$(MAGENTA)htmlhint not found. Install with: npm install -g htmlhint$(RESET)"; \
	fi
