---
layout: post
title:  "Creating webdown"
date:   2025-03-16 15:48:00 -0700
categories: projects
draft: true
---

# Creating webdown with Claude Code

This post documents my journey creating [webdown](https://tcole.net/webdown/), a Python CLI tool for converting web pages to clean, readable Markdown format - all without writing a single line of code myself.

## Project Overview

- **What**: A command-line tool that converts web content to clean Markdown
- **Why**: To extract documentation for feeding into LLMs like Claude
- **How**: Built entirely through collaboration with Claude Code

## The Journey

### Initial Setup
- Conceptualizing the tool's purpose and functionality
- Setting up the repository structure
- Creating the initial Python package scaffolding

### Core Functionality
- Implementing web page fetching and HTML parsing
- Converting HTML to Markdown while preserving semantic structure
- Adding configurable options for output formatting

### CLI Interface
- Building a user-friendly command-line interface
- Adding argument parsing for URLs and configuration options
- Implementing output redirection (stdout, file)

### Refinement and Testing
- Handling edge cases (JavaScript-rendered content, paywalls)
- Improving output quality for various site layouts
- Adding unit tests to ensure reliability

### The Documentation Challenge
- **The hardest part**: Setting up GitHub Pages for documentation
- Fixing Jekyll build issues with GitHub Actions
- Adding the `.nojekyll` file and resolving conflicting workflows
- Getting the custom domain working properly

## Lessons Learned

- The power of AI pair programming with Claude Code
- The importance of clear communication when collaborating with AI
- How to effectively break down tasks for AI assistance
- The unexpected challenges of documentation deployment

## Next Steps

- Adding more formatting options
- Improving handling of complex layouts
- Building a browser extension for easier access

