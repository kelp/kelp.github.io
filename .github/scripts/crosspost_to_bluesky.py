#!/usr/bin/env python3
"""
Cross-post Jekyll blog posts to Bluesky.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import frontmatter
import markdown
from atproto import Client

# Constants
SITE_URL = "https://tcole.net"
MAX_SUMMARY_LENGTH = 150       # Characters in summary (keep short)
MAX_TOTAL_POST_LENGTH = 300    # Bluesky's maximum limit for post length
PUBLISHED_FILE = ".github/bluesky-published.json"
REPO_ROOT = os.getcwd()  # GitHub Actions runs in the repo root

def normalize_path(path: str) -> str:
    """Normalize a post path for consistent tracking."""
    # Convert to relative path if it's absolute
    if os.path.isabs(path):
        try:
            # Get path relative to repo root
            rel_path = os.path.relpath(path, REPO_ROOT)
            # Convert Windows backslashes to forward slashes if needed
            return rel_path.replace('\\', '/')
        except ValueError:
            # If path is not relative to REPO_ROOT, just use the basename
            return os.path.basename(path)
    else:
        # Already relative, just normalize slashes
        return path.replace('\\', '/')

def load_published_posts() -> Set[str]:
    """Load the list of already published posts."""
    published_file_path = os.path.join(REPO_ROOT, PUBLISHED_FILE)
    if os.path.exists(published_file_path):
        with open(published_file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Convert all paths to normalized format
                return {normalize_path(p) for p in data.get("published", [])}
            except json.JSONDecodeError:
                return set()
    return set()

def save_published_posts(published: Set[str]) -> None:
    """Save the updated list of published posts."""
    published_file_path = os.path.join(REPO_ROOT, PUBLISHED_FILE)
    os.makedirs(os.path.dirname(published_file_path), exist_ok=True)
    
    # Normalize all paths before saving
    normalized_paths = [normalize_path(p) for p in published]
    
    with open(published_file_path, "w", encoding="utf-8") as f:
        json.dump({"published": sorted(normalized_paths)}, f, indent=2)

def extract_summary(content: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """Extract a summary from the post content."""
    # Convert markdown to plain text
    html = markdown.markdown(content)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # If text is already short enough, return it
    if len(text) <= max_length:
        return text
    
    # Otherwise, truncate to fit within the limit, end at a sentence if possible
    truncated = text[:max_length-3]
    # Try to end at a sentence
    sentence_end = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if sentence_end > max_length * 0.7:  # Only use sentence end if it's not too short
        truncated = truncated[:sentence_end+1]
    
    return truncated + "..."

def post_to_bluesky(
    client: Client,
    title: str,
    summary: str,
    post_url: str,
    categories: List[str]
) -> bool:
    """Post to Bluesky with the blog post summary and link."""
    try:
        # Truncate the title if it's too long
        if len(title) > 70:
            title = title[:67] + "..."
        
        # Format post as "A new post on my blog:" followed by title (as link) and summary
        intro = "A new post on my blog:\n\n"
        
        # Calculate space available for summary
        base_text = f"{intro}{title}\n\n"
        available_space = MAX_TOTAL_POST_LENGTH - len(base_text) - 5  # 5 chars buffer
        
        # Make sure we have some space for summary
        if available_space > 20:
            # If the summary fits in available space, add it
            if len(summary) <= available_space:
                post_text = f"{base_text}{summary}"
            else:
                # Otherwise truncate summary
                truncated_summary = summary[:available_space-3] + "..."
                post_text = f"{base_text}{truncated_summary}"
        else:
            # Not enough space for summary, just use intro and title
            post_text = base_text
        
        # Final check to ensure we're within limits
        if len(post_text) > MAX_TOTAL_POST_LENGTH:
            # Emergency truncation - just intro and shortened title
            post_text = f"{intro}{title[:100]}..."
            
        # Create rich text facets for the title to make it a clickable link
        # Calculate the UTF-8 byte index of the title in the text
        intro_bytes_length = len(intro.encode('utf-8'))
        title_bytes_length = len(title.encode('utf-8'))
        
        # Create a facet (rich text link) that makes the title clickable
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
                "createdAt": datetime.now().isoformat(),
            }
        })
        
        print(f"Successfully posted to Bluesky: {title}")
        return True
    except Exception as e:
        print(f"Error posting to Bluesky: {e}")
        return False

def process_post(post_path: str, published_posts: Set[str]) -> Optional[Dict]:
    """Process a single blog post."""
    try:
        # Normalize the path for consistent tracking
        normalized_path = normalize_path(post_path)
        
        # Skip if already published
        if normalized_path in published_posts:
            print(f"Skipping already published post: {post_path}")
            return None
        
        # Get full path if it's a relative path
        full_post_path = post_path
        if not os.path.isabs(post_path):
            full_post_path = os.path.join(REPO_ROOT, post_path)
        
        # Parse the post with frontmatter
        post = frontmatter.load(full_post_path)
        
        # Skip drafts
        if post.get("draft", False):
            print(f"Skipping draft post: {post_path}")
            return None
        
        # Extract post details
        title = post.get("title", "")
        date_str = post.get("date", "")
        categories = post.get("categories", [])
        
        if isinstance(categories, str):
            categories = [c.strip() for c in categories.split(",")]
        
        # Extract filename without extension and directory
        filename = os.path.basename(post_path)
        slug = os.path.splitext(filename)[0]
        # Check if the slug starts with a date pattern (YYYY-MM-DD-)
        if re.match(r'^\d{4}-\d{2}-\d{2}-', slug):
            # Remove date prefix if it exists
            slug = "-".join(slug.split("-")[3:])
        
        # Construct the post URL
        # Format: YYYY/MM/DD/post-slug.html
        if isinstance(date_str, datetime):
            date_path = date_str.strftime("%Y/%m/%d")
        elif isinstance(date_str, str) and re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_path = date_obj.strftime("%Y/%m/%d")
        else:
            # Use the date from the filename as fallback
            match = re.match(r'(\d{4})-(\d{2})-(\d{2})', filename)
            if match:
                year, month, day = match.groups()
                date_path = f"{year}/{month}/{day}"
            else:
                print(f"Could not determine date for post: {post_path}")
                return None
        
        # Extract the slug without file extension, ensuring we handle both .md and .markdown
        clean_slug = slug.replace('.markdown', '').replace('.md', '')
        
        # Jekyll URL format based on sample posts
        if categories and len(categories) > 0:
            # First category becomes part of the URL (common Jekyll pattern)
            # Based on the sample URLs from the site
            if isinstance(categories, list):
                # When 'categories' is a list, typically from front matter like: categories: [ai, programming, tools]
                category_path = "/".join(categories)
                post_url = f"{SITE_URL}/{category_path}/{date_path}/{clean_slug}.html"
            else:
                # When 'categories' is a single string
                post_url = f"{SITE_URL}/{categories}/{date_path}/{clean_slug}.html"
        else:
            # No categories, use the default Jekyll URL format
            post_url = f"{SITE_URL}/{date_path}/{clean_slug}.html"
        
        # Extract summary
        summary = extract_summary(post.content)
        
        return {
            "path": post_path,
            "title": title,
            "summary": summary,
            "url": post_url,
            "categories": categories
        }
    except Exception as e:
        print(f"Error processing post {post_path}: {e}")
        return None

def main():
    """Main function to process changed posts and crosspost to Bluesky."""
    print("Starting Bluesky cross-posting process...")
    
    # Get Bluesky credentials
    bluesky_id = os.environ.get("BLUESKY_IDENTIFIER")
    bluesky_pw = os.environ.get("BLUESKY_PASSWORD")
    
    if not bluesky_id or not bluesky_pw:
        print("ERROR: Bluesky credentials not found in environment variables.")
        print("Please set BLUESKY_IDENTIFIER and BLUESKY_PASSWORD as repository secrets.")
        sys.exit(1)
    
    # Get changed post files from command line arguments
    changed_files = sys.argv[1:]
    
    if not changed_files:
        print("No files provided. Expecting files from git diff.")
        sys.exit(0)
        
    print(f"Received {len(changed_files)} changed files: {', '.join(changed_files)}")
    
    # Filter for files in _posts directory with markdown extensions
    post_files = [f for f in changed_files if f.startswith("_posts/") and f.endswith((".md", ".markdown"))]
    
    if not post_files:
        print("No blog posts found in the changes.")
        sys.exit(0)
        
    print(f"Found {len(post_files)} blog posts to process: {', '.join(post_files)}")
    
    # Load the list of already published posts
    published_posts = load_published_posts()
    newly_published = set()
    
    # Connect to Bluesky
    try:
        client = Client()
        client.login(bluesky_id, bluesky_pw)
    except Exception as e:
        print(f"Error logging in to Bluesky: {e}")
        sys.exit(1)
    
    # Process each post
    for post_file in post_files:
        post_data = process_post(post_file, published_posts)
        
        if post_data:
            # Post to Bluesky
            success = post_to_bluesky(
                client,
                post_data["title"],
                post_data["summary"],
                post_data["url"],
                post_data["categories"]
            )
            
            if success:
                # Add normalized path to the newly published set
                newly_published.add(normalize_path(post_file))
    
    # Update the published posts file
    if newly_published:
        published_posts.update(newly_published)
        save_published_posts(published_posts)
        print(f"Added {len(newly_published)} posts to the published list.")

if __name__ == "__main__":
    main()