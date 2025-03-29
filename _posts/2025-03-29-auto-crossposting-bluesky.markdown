---
layout: post
title: "Vibe Coding: Auto-Crossposting from Jekyll to Bluesky"
date: 2025-03-29
categories: [ai, projects, tools]
---

Last night I automated cross-posting from my Jekyll blog to my Bluesky account
using GitHub Actions and a Python script. This was a straightforward project
done entirely with
[Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview),
which is Anthropic's coding agent, released on February 24th, 2025.

## The Requirements

I wanted a system that would:

1. Detect new posts in my Jekyll blog, hosted on GitHub Pages
2. Create a Bluesky post with a clickable link to my blog
3. Include a brief summary of the post
4. Skip any draft posts
5. Only post each article once

## The Solution: GitHub Actions + atproto

I asked Claude Code to design a solution using
[ATProto](https://atproto.blue/) and discuss it with me before we started
writing code. We went back and forth about how to track what had already been
posted, but settled on a simple solution: have GitHub Actions commit a JSON
file that tracks posts.

For this project, we built:

1. A GitHub Actions workflow (`.github/workflows/bluesky-crosspost.yml`)
2. A Python script for the cross-posting logic
   (`.github/scripts/crosspost_to_bluesky.py`)
3. A JSON tracking file (`.github/bluesky-published.json`) committed to git by
   the GitHub Action

I didn't write a line of code myself - Claude handled everything from the
workflow configuration to the Python implementation.

### The GitHub Action Workflow

```yaml
name: Cross-post to Bluesky

on:
  push:
    branches: [main]
    paths:
      - "_posts/**"

  # Allow manual triggering
  workflow_dispatch:

# Set permissions for the GITHUB_TOKEN
permissions:
  contents: write # Needed to push the updated JSON file

jobs:
  crosspost:
    runs-on: ubuntu-latest
    # Run for push events or manual triggers
    if:
      github.event_name == 'push' || github.event_name == 'workflow_dispatch'

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Fetch all history
          token: ${{ github.token }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: |
            .github/requirements.txt

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r .github/requirements.txt

      - name: Find changed posts
        id: changed-posts
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            # When manually triggered, use the latest post
            LATEST_POST=$(find _posts -type f -name "*.markdown" -o -name "*.md" | sort -r | head -n1)
            echo "Using latest post: $LATEST_POST"
            echo "changed_files=$LATEST_POST" >> $GITHUB_OUTPUT
          else
            # Get list of changed files from the push event
            CHANGED_FILES=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} | grep "_posts/" | tr '\n' ' ')
            echo "Changed files: $CHANGED_FILES"
            echo "changed_files=$CHANGED_FILES" >> $GITHUB_OUTPUT
          fi

      - name: Crosspost to Bluesky
        if: steps.changed-posts.outputs.changed_files != ''
        env:
          BLUESKY_IDENTIFIER: ${{ secrets.BLUESKY_IDENTIFIER }}
          BLUESKY_PASSWORD: ${{ secrets.BLUESKY_PASSWORD }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python .github/scripts/crosspost_to_bluesky.py ${{ steps.changed-posts.outputs.changed_files }}

      - name: Commit updated published list
        if: steps.changed-posts.outputs.changed_files != ''
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add .github/bluesky-published.json
          git commit -m "Update Bluesky published posts list [skip ci]" || echo "No changes to commit"
          git push
```

The workflow is triggered either when changes are pushed to the `_posts/`
directory or when manually triggered. It identifies which post files were
changed, runs the Python script to cross-post them, and then commits the
updated tracking file.

### Python Dependencies

```text
atproto>=0.0.31
PyYAML>=6.0
python-frontmatter>=1.0.0
markdown>=3.4.0
anthropic>=0.5.0
```

### The Cross-posting Script

The most interesting part of the implementation is the creation of a rich text
link in Bluesky, which uses a feature called "facets":

```python
def post_to_bluesky(client, title, summary, post_url, categories):
    """Post to Bluesky with the blog post summary and link."""
    try:
        # Format post with title as clickable link
        intro = "A new post on my blog:\n\n"
        post_text = f"{intro}{title}\n\n{summary}"

        # Create rich text facets for the title to make it a clickable link
        intro_bytes_length = len(intro.encode('utf-8'))
        title_bytes_length = len(title.encode('utf-8'))

        facets = [
            {
                "index": {
                    "byteStart": intro_bytes_length,
                    "byteEnd": intro_bytes_length + title_bytes_length
                },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        "uri": post_url
                    }
                ]
            }
        ]

        # Create the post with rich text
        client.com.atproto.repo.create_record({
            "repo": client.me.did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": post_text,
                "facets": facets,
                "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            }
        })

        return True
    except Exception as e:
        print(f"Error posting to Bluesky: {e}")
        return False
```

The script also detects whether I'm commenting on someone else's blog post or
writing original content, and formats the summary accordingly.

## Generating Summaries with Claude

At first we were just using the first few lines of the post for a summary, but
I didn't like the result and realized we could use AI to make the summary.

So we added summarization using the Anthropic API. I asked Claude Chat to
recommend a model for this use case, and it suggested Claude Haiku 3.5 for its
low cost and speed. The first few tries sounded like pretty bad marketing
speak, so we had to iterate several times on the prompt. We settled on
something that I think works pretty well.

This creates more natural-sounding summaries that match my writing style:

```python
def generate_summary_with_claude(title, content, max_length):
    """Generate a summary using Claude via the Anthropic API."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Detect if this is commenting on someone else's post
    has_quotes = '>' in content
    attribution_pattern = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+) on \[(.*?)\]', content)

    if has_quotes or attribution_pattern:
        # Format prompt for reference posts
        # ...
    else:
        # Format prompt for original content
        # ...

    response = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=300,
        temperature=0.2,
        system="You extract only the core facts in plainest possible language",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()
```

## Results

Posts on Bluesky now look like:

```text
A new post on my blog:

Automated Cross-posting from Jekyll to Bluesky

A GitHub Action that detects new blog posts and cross-posts them to Bluesky
with clickable links and AI-generated summaries.
```

The title becomes a clickable link to the original blog post, and the summary
is generated automatically using Claude.

## Challenges and Learnings

Claude thinks the most challenging part was:

> ...getting the Bluesky facets (rich text) working correctly. The byte
> indexing for the clickable link was tricky, and we had to handle UTF-8
> encoding properly.

But I basically asked it to write the code, then asked it to check for bugs,
which prompted Claude to change a lot of things. Then we tested the workflow
live. It failed on the first try, but Claude Code used the GitHub `gh` CLI to
check the GitHub Action run for errors. It fixed the issues and then we had
things working.

The AI summary took about 15 minutes to refine. We settled on a system prompt
("extract only the core facts in plainest possible language") that generates
direct, factual summaries matching my writing style.

## Trying It Yourself

If you want to implement this for your own Jekyll blog, you'll need:

1. A GitHub repository with Jekyll
2. A Bluesky account
3. GitHub repository secrets for BLUESKY_IDENTIFIER and BLUESKY_PASSWORD
4. Optional: An Anthropic API key for better summaries

The full code is available in
[my blog's repository](https://github.com/kelp/kelp.github.io).
