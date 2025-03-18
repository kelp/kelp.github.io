---
layout: post
title:  "Creating webdown"
date:   2025-03-16 15:48:00 -0700
categories: projects
draft: true
---

# Creating webdown with Claude Code

This post documents my journey creating [webdown](https://github.com/tcole/webdown), a Python CLI tool for converting web pages to clean, readable Markdown format - perfect for feeding into LLMs like Claude. The entire project was built through collaboration with Claude Code, without me writing a single line of code myself.

## The Inspiration

My journey began after reading Simon Willison's blog post on [using LLMs for coding](https://simonwillison.net/2025/Mar/11/using-llms-for-code/), where he mentioned:

> I was trying out a new-to-me tool called [monolith](https://github.com/Y2Z/monolith), a CLI tool written in Rust which downloads a web page and all of its dependent assets (CSS, images etc) and bundles them together into a single archived file.

Simon also discussed his tool called [files-to-prompt](https://github.com/simonw/files-to-prompt) for analyzing codebases and feeding them to LLMs. This sparked an idea: what if I built a tool specifically for converting web pages to Markdown for easy input into LLMs?

## Project Goals

Looking at the TODO list I created for the project, I had several key goals in mind:

1. **Clean Conversions**: Transform web content to readable Markdown with preserved structure
2. **Token Efficiency**: Remove unnecessary elements and formatting to reduce LLM token consumption
3. **Easy to Use**: Simple CLI interface that works across platforms
4. **Configurable**: Customizable options for different content types and output needs
5. **Modern Python**: Use current best practices in Python project structure and tooling

## The Development Process

### Phase 1: Setting Up the Project

The first phase involved setting up a modern Python project structure:

- Creating pyproject.toml with Poetry for dependency management
- Setting up pre-commit hooks for code quality 
- Establishing a testing framework with pytest
- Adding GitHub Actions for CI/CD

As documented in the TODO list, moving to Poetry for environment management was a deliberate choice to use modern Python packaging practices.

### Phase 2: Core Functionality

The heart of webdown consists of several key components:

1. **URL Fetching**: Downloading web content
2. **HTML Parsing**: Processing the HTML structure
3. **Markdown Conversion**: Transforming HTML to clean Markdown
4. **Customization Options**: Extracting specific sections via CSS selectors

The TODO list shows several completed items in this area, including:
- Adding a progress bar for downloads
- Creating a WebdownConfig class for parameter organization
- Supporting advanced HTML-to-Markdown conversion options

### Phase 3: Testing and Quality Control

The project placed strong emphasis on testing and code quality:

- Comprehensive unit tests
- 100% test coverage (as noted in a recent commit)
- Integration tests for real-world scenarios
- Type checking with mypy
- Linting with flake8

The TODO list shows all these items as completed, reflecting the importance placed on code quality.

### Phase 4: Documentation and Packaging

This phase proved to be the most challenging:

- Initially generating API documentation with pdoc
- Switching to MkDocs for better features
- Creating comprehensive README and usage examples
- Publishing to PyPI
- Setting up GitHub Pages with custom domain

The documentation journey required significant effort. We started with pdoc due to its simplicity, but later migrated to MkDocs which offered better theme options, navigation, and search functionality.

Setting up GitHub Actions for documentation deployment was particularly challenging. The GitHub Pages configuration, custom domain setup, and workflow integration required multiple iterations to get right.

## Key Learnings

### The Power of Clear Project Planning

Having a detailed TODO list from the start proved invaluable. It provided structure and helped break complex tasks into manageable chunks.

### Modern Python Best Practices Matter

Following modern Python conventions (Poetry, pyproject.toml, type hints) created a more maintainable and professional codebase.

### Test-Driven Development Works Well with AI

Setting clear expectations through tests helped guide the implementation process. The high test coverage achieved indicates a thorough testing approach.

### The Value of Proper Error Handling

Based on the TODO list, implementing custom exception handling was a priority that improved both debugging and user experience.

## Current Features

Webdown currently offers several key capabilities:

- Converting web pages to clean Markdown
- Extracting specific content using CSS selectors
- Configurable output formatting options
- Progress indication for downloads
- Compact output mode to remove excessive blank lines

## Future Directions

The TODO list includes several planned enhancements:

- Support for custom HTML-to-Markdown converters
- Authentication for accessing private web content
- Batch processing of multiple URLs
- Caching mechanism for frequently accessed pages
- Post-processing to clean and normalize generated Markdown

## Getting Started with webdown

```bash
# Install from PyPI
pip install webdown

# Basic usage
webdown https://example.com > example.md

# Extract specific content using CSS selectors
webdown https://example.com -s "article.main-content" > article.md

# Compact output by removing excessive blank lines
webdown https://example.com --compact > compact.md
```

## Conclusion

Creating webdown with Claude Code demonstrated the potential of AI-assisted development. The project was completed efficiently while maintaining high quality standards for code, testing, and documentation.

The experience highlighted the areas where AI assistance currently works best, as well as where human expertise remains crucial. While the core functionality came together relatively quickly, the documentation system and GitHub Actions configuration presented more significant challenges.

This suggests an effective division of labor: AI can excel at structured coding tasks with clear patterns, while humans can focus on integration challenges, deployment strategies, and documentation architecture.

The project went from concept to published package in considerably less time than traditional development, with comprehensive test coverage and documentation. If you're interested in trying webdown, you can check out the [GitHub repository](https://github.com/tcole/webdown) or install it directly from PyPI.

*This post is still a draft - I'll be expanding it with more specific examples and challenges faced during development.*