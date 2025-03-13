#!/usr/bin/env python3
"""
Jekyll to Substack Cross-posting Script

This script identifies Jekyll posts changed in the latest commit, 
processes their content, and publishes them to Substack with safeguards
against duplicate or excessive publishing.
"""

import os
import sys
import json
import time
import frontmatter
import markdown
import requests
from pathlib import Path
import logging
from datetime import datetime, timedelta
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
SUBSTACK_API_KEY = os.environ.get('SUBSTACK_API_KEY')
SUBSTACK_PUBLICATION = os.environ.get('SUBSTACK_PUBLICATION')
CHANGED_POSTS = os.environ.get('CHANGED_POSTS', '')
MAX_PUBLICATIONS_PER_DAY = int(os.environ.get('MAX_PUBLICATIONS_PER_DAY', '1'))
FORCE_PUBLISH = os.environ.get('FORCE_PUBLISH', '').lower() == 'true'

# Substack API endpoints
BASE_URL = f"https://api.substack.com/api/v1/publication/{SUBSTACK_PUBLICATION}"
DRAFTS_URL = f"{BASE_URL}/drafts"
PUBLISH_URL = f"{BASE_URL}/post"
POSTS_URL = f"{BASE_URL}/posts"

# Cache file for tracking publications
PUBLICATION_CACHE_PATH = '.github/.substack_publication_cache.json'

class PublicationCache:
    """Manages a cache of published posts to prevent duplicate publishing."""
    
    def __init__(self, cache_path=PUBLICATION_CACHE_PATH):
        self.cache_path = cache_path
        self.cache = self._load_cache()
        
    def _load_cache(self):
        """Load the cache from file if it exists."""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    cache = json.load(f)
                return cache
            return {
                'published_posts': {},
                'last_publication_dates': [],
                'last_publication_count_24h': 0,
                'last_publication_day': '',
            }
        except Exception as e:
            logger.warning(f"Error loading publication cache: {e}. Creating new cache.")
            return {
                'published_posts': {},
                'last_publication_dates': [],
                'last_publication_count_24h': 0,
                'last_publication_day': '',
            }
    
    def _save_cache(self):
        """Save the cache to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving publication cache: {e}")
    
    def post_was_published(self, post_path, content_hash):
        """Check if a post was already published based on content hash."""
        return content_hash in self.cache['published_posts'].values()
    
    def record_publication(self, post_path, content_hash):
        """Record a publication in the cache."""
        now = datetime.now().isoformat()
        
        # Clean up old entries from the dates list (older than 24 hours)
        current_time = datetime.now()
        self.cache['last_publication_dates'] = [
            date for date in self.cache['last_publication_dates']
            if current_time - datetime.fromisoformat(date) < timedelta(hours=24)
        ]
        
        # Add the new publication date
        self.cache['last_publication_dates'].append(now)
        
        # Update the 24h counter
        self.cache['last_publication_count_24h'] = len(self.cache['last_publication_dates'])
        
        # Update the last publication day
        today = datetime.now().strftime('%Y-%m-%d')
        self.cache['last_publication_day'] = today
        
        # Record the post hash
        self.cache['published_posts'][post_path] = content_hash
        
        # Save the updated cache
        self._save_cache()
    
    def can_publish_more_today(self):
        """Check if we've reached the daily publication limit."""
        # Clean up old entries first
        current_time = datetime.now()
        self.cache['last_publication_dates'] = [
            date for date in self.cache['last_publication_dates']
            if current_time - datetime.fromisoformat(date) < timedelta(hours=24)
        ]
        
        # Update the 24h counter
        self.cache['last_publication_count_24h'] = len(self.cache['last_publication_dates'])
        
        # Check if we're under the limit
        return self.cache['last_publication_count_24h'] < MAX_PUBLICATIONS_PER_DAY
    
    def get_published_count_24h(self):
        """Get the number of posts published in the last 24 hours."""
        return self.cache['last_publication_count_24h']


def validate_environment():
    """Validate that all required environment variables are set."""
    if not SUBSTACK_API_KEY:
        logger.error("SUBSTACK_API_KEY environment variable is not set")
        return False
    if not SUBSTACK_PUBLICATION:
        logger.error("SUBSTACK_PUBLICATION environment variable is not set")
        return False
    if not CHANGED_POSTS:
        logger.warning("No changed posts found")
        return False
    return True


def get_changed_posts():
    """Get list of changed posts from the environment variable."""
    if not CHANGED_POSTS:
        return []
    return CHANGED_POSTS.split()


def get_content_hash(post_data):
    """Generate a hash from post content to detect duplicates."""
    content_string = f"{post_data['title']}|{post_data['body_html']}"
    return hashlib.md5(content_string.encode('utf-8')).hexdigest()


def check_for_duplicate_on_substack(post_data, headers):
    """Check if a post with the same title already exists on Substack."""
    try:
        # Get recent posts from Substack
        response = requests.get(POSTS_URL, headers=headers)
        response.raise_for_status()
        posts = response.json()
        
        # Check for posts with the same title (case-insensitive)
        for post in posts:
            if post.get('title', '').lower() == post_data['title'].lower():
                return True
        
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking for duplicates on Substack: {e}")
        # If there's an error checking, we'll err on the side of caution
        return True


def process_post(post_path):
    """Process a Jekyll post and return its data."""
    try:
        post = frontmatter.load(post_path)
        
        # Check if the post should be skipped
        if post.get('draft', False) or post.get('published', True) is False:
            logger.info(f"Skipping draft post: {post_path}")
            return None

        # Check if the post should be forcibly skipped for Substack
        if post.get('skip_substack', False):
            logger.info(f"Skipping post marked with skip_substack: {post_path}")
            return None

        # Extract title from frontmatter, or from filename if not available
        title = post.get('title', Path(post_path).stem.split('-', 3)[-1].replace('-', ' ').title())
        
        # Convert Markdown to HTML
        content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code'])
        
        # Get Substack-specific metadata
        substack_status = post.get('substack_status', 'draft')
        substack_audience = post.get('substack_audience', 'everyone')
        
        return {
            'title': title,
            'body_html': content_html,
            'status': substack_status,
            'audience': substack_audience,
            # Add any other metadata fields you need
            'subtitle': post.get('description', ''),
            'canonical_url': post.get('canonical_url', ''),
            'post_path': post_path,
        }
    except Exception as e:
        logger.error(f"Error processing post {post_path}: {e}")
        return None


def create_draft_on_substack(post_data, publication_cache):
    """Create a draft post on Substack."""
    headers = {
        'Authorization': f'Bearer {SUBSTACK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Generate content hash for duplicate detection
    content_hash = get_content_hash(post_data)
    
    # Check if the post was already published by this script
    if publication_cache.post_was_published(post_data['post_path'], content_hash):
        logger.warning(f"Post '{post_data['title']}' was already published. Skipping.")
        return None
    
    # Check if a post with the same title already exists on Substack
    if check_for_duplicate_on_substack(post_data, headers):
        logger.warning(f"A post with title '{post_data['title']}' already exists on Substack. Skipping.")
        return None
    
    # Prepare data for Substack API
    draft_data = {
        'title': post_data['title'],
        'body_html': post_data['body_html'],
        'subtitle': post_data['subtitle'],
    }
    
    # Add canonical URL if available
    if post_data['canonical_url']:
        draft_data['canonical_url'] = post_data['canonical_url']
    
    try:
        response = requests.post(DRAFTS_URL, json=draft_data, headers=headers)
        response.raise_for_status()
        draft_id = response.json().get('id')
        logger.info(f"Created draft post '{post_data['title']}' with ID {draft_id}")
        return draft_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating draft on Substack: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return None


def publish_post_on_substack(draft_id, post_data, publication_cache):
    """Publish a draft post on Substack if it should be published."""
    if post_data['status'] != 'published':
        logger.info(f"Draft {draft_id} is set to remain as draft")
        return False

    # Check publication limits unless forced
    if not FORCE_PUBLISH:
        if not publication_cache.can_publish_more_today():
            logger.warning(
                f"Daily publication limit of {MAX_PUBLICATIONS_PER_DAY} reached. "
                f"Draft {draft_id} will remain as draft. Use FORCE_PUBLISH=true to override."
            )
            return False
    
    headers = {
        'Authorization': f'Bearer {SUBSTACK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    publish_data = {
        'draft_id': draft_id,
        'email_settings': {
            'audience': post_data['audience']
        }
    }
    
    try:
        response = requests.post(PUBLISH_URL, json=publish_data, headers=headers)
        response.raise_for_status()
        logger.info(f"Published post '{post_data['title']}' to Substack")
        
        # Record successful publication
        content_hash = get_content_hash(post_data)
        publication_cache.record_publication(post_data['post_path'], content_hash)
        
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error publishing post on Substack: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return False


def main():
    """Main function to process changed posts and publish them to Substack."""
    if not validate_environment():
        sys.exit(1)
    
    # Load publication cache
    publication_cache = PublicationCache()
    
    changed_posts = get_changed_posts()
    logger.info(f"Found {len(changed_posts)} changed posts")
    
    # Show publication stats
    published_count = publication_cache.get_published_count_24h()
    logger.info(f"Posts published in the last 24 hours: {published_count}")
    logger.info(f"Maximum posts allowed per day: {MAX_PUBLICATIONS_PER_DAY}")
    
    published_posts = 0
    for post_path in changed_posts:
        logger.info(f"Processing post: {post_path}")
        post_data = process_post(post_path)
        
        if post_data:
            draft_id = create_draft_on_substack(post_data, publication_cache)
            if draft_id and post_data['status'] == 'published':
                if publish_post_on_substack(draft_id, post_data, publication_cache):
                    published_posts += 1
    
    logger.info(f"Processing complete. Published {published_posts} posts to Substack.")


if __name__ == "__main__":
    main()