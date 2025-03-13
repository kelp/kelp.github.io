#!/usr/bin/env python3
"""
Unit tests for the Jekyll to Substack publish script.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
from datetime import datetime, timedelta
import hashlib
import requests

# Add parent directory to path so we can import the script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the script
import publish_to_substack as substack


class TestPublishToSubstack(unittest.TestCase):
    """Test cases for the publish_to_substack.py script."""

    def setUp(self):
        """Set up test environment."""
        # Create a temp directory for the cache
        self.test_dir = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.test_dir, '.substack_publication_cache.json')
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'SUBSTACK_API_KEY': 'test_api_key',
            'SUBSTACK_PUBLICATION': 'test_publication',
            'MAX_PUBLICATIONS_PER_DAY': '2',
        })
        self.env_patcher.start()
        
        # Set the fixture paths
        self.fixtures_path = os.path.join(os.path.dirname(__file__))
        self.standard_post = os.path.join(self.fixtures_path, 'fixture_post.md')
        self.published_post = os.path.join(self.fixtures_path, 'fixture_published_post.md')
        self.draft_post = os.path.join(self.fixtures_path, 'fixture_draft_post.md')

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temp directory
        shutil.rmtree(self.test_dir)
        # Stop patching environment
        self.env_patcher.stop()

    def test_validate_environment_success(self):
        """Test environment validation with all required variables."""
        # Directly patch the environment getters
        with patch('publish_to_substack.SUBSTACK_API_KEY', 'test_key'), \
             patch('publish_to_substack.SUBSTACK_PUBLICATION', 'test_pub'), \
             patch('publish_to_substack.CHANGED_POSTS', 'post1.md post2.md'):
            self.assertTrue(substack.validate_environment())

    def test_validate_environment_missing_key(self):
        """Test environment validation with missing API key."""
        with patch('publish_to_substack.SUBSTACK_API_KEY', ''), \
             patch('publish_to_substack.SUBSTACK_PUBLICATION', 'test_pub'), \
             patch('publish_to_substack.CHANGED_POSTS', 'post1.md'):
            self.assertFalse(substack.validate_environment())

    def test_validate_environment_missing_publication(self):
        """Test environment validation with missing publication."""
        with patch('publish_to_substack.SUBSTACK_API_KEY', 'test_key'), \
             patch('publish_to_substack.SUBSTACK_PUBLICATION', ''), \
             patch('publish_to_substack.CHANGED_POSTS', 'post1.md'):
            self.assertFalse(substack.validate_environment())
            
    def test_validate_environment_missing_posts(self):
        """Test environment validation with missing changed posts."""
        with patch('publish_to_substack.SUBSTACK_API_KEY', 'test_key'), \
             patch('publish_to_substack.SUBSTACK_PUBLICATION', 'test_pub'), \
             patch('publish_to_substack.CHANGED_POSTS', ''):
            self.assertFalse(substack.validate_environment())

    def test_get_changed_posts(self):
        """Test getting changed posts from environment variable."""
        with patch('publish_to_substack.CHANGED_POSTS', 'post1.md post2.md post3.md'):
            posts = substack.get_changed_posts()
            self.assertEqual(posts, ['post1.md', 'post2.md', 'post3.md'])

    def test_get_changed_posts_empty(self):
        """Test getting changed posts with empty environment variable."""
        with patch('publish_to_substack.CHANGED_POSTS', ''):
            posts = substack.get_changed_posts()
            self.assertEqual(posts, [])

    def test_get_content_hash(self):
        """Test generating a content hash."""
        post_data = {
            'title': 'Test Post',
            'body_html': '<p>Test content</p>',
        }
        hash1 = substack.get_content_hash(post_data)
        
        # Should get the same hash for the same content
        hash2 = substack.get_content_hash(post_data)
        self.assertEqual(hash1, hash2)
        
        # Should get a different hash for different content
        post_data['title'] = 'Changed Title'
        hash3 = substack.get_content_hash(post_data)
        self.assertNotEqual(hash1, hash3)

    @patch('requests.get')
    def test_check_for_duplicate_on_substack(self, mock_get):
        """Test checking for duplicates on Substack."""
        # Mock response with existing posts
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'title': 'Existing Post 1'},
            {'title': 'Existing Post 2'},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test with a new title
        post_data = {'title': 'New Post'}
        self.assertFalse(substack.check_for_duplicate_on_substack(post_data, {}))
        
        # Test with an existing title (case insensitive)
        post_data = {'title': 'existing post 1'}
        self.assertTrue(substack.check_for_duplicate_on_substack(post_data, {}))
        
    @patch('requests.get')
    def test_check_for_duplicate_on_substack_api_error(self, mock_get):
        """Test error handling when checking for duplicates on Substack."""
        # Mock API error
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        post_data = {'title': 'Test Post'}
        # Should return True (err on the side of caution)
        self.assertTrue(substack.check_for_duplicate_on_substack(post_data, {}))

    def test_process_post_standard(self):
        """Test processing a standard post."""
        result = substack.process_post(self.standard_post)
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Test Jekyll Post')
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['audience'], 'everyone')
        self.assertIn('<h1>Test Post Heading</h1>', result['body_html'])

    def test_process_post_published(self):
        """Test processing a post marked for publishing."""
        result = substack.process_post(self.published_post)
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Published Test Post')
        self.assertEqual(result['status'], 'published')
        self.assertIn('<h1>Published Test Post</h1>', result['body_html'])

    def test_process_post_draft(self):
        """Test processing a draft post that should be skipped."""
        result = substack.process_post(self.draft_post)
        self.assertIsNone(result)

    def test_process_post_with_skip_substack(self):
        """Test processing a post with skip_substack flag."""
        with patch('frontmatter.load') as mock_load:
            # Create a mock object that behaves like a frontmatter post
            mock_post = MagicMock()
            mock_post.content = 'Test content'
            
            # Configure the get method to return specific values
            mock_post.get.side_effect = lambda key, default=None: {
                'skip_substack': True,
                'title': 'Skip Test',
                'draft': False,
                'published': True
            }.get(key, default)
            
            mock_load.return_value = mock_post
            
            result = substack.process_post('test_path.md')
            self.assertIsNone(result)

    @patch('requests.post')
    def test_create_draft_on_substack(self, mock_post):
        """Test creating a draft on Substack."""
        # Mock the publication cache
        mock_cache = MagicMock()
        mock_cache.post_was_published.return_value = False
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'draft123'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock the duplicate check to return False (no duplicates)
        with patch('publish_to_substack.check_for_duplicate_on_substack', return_value=False):
            post_data = {
                'title': 'Test Draft',
                'body_html': '<p>Test content</p>',
                'subtitle': 'Test subtitle',
                'canonical_url': '',
                'post_path': 'test.md'
            }
            
            result = substack.create_draft_on_substack(post_data, mock_cache)
            self.assertEqual(result, 'draft123')
            
            # Verify the API was called correctly
            mock_post.assert_called_once()
            # Check that title was included in the JSON
            args, kwargs = mock_post.call_args
            self.assertIn('title', kwargs.get('json', {}))

    @patch('requests.post')
    def test_create_draft_already_published(self, mock_post):
        """Test trying to create a draft for an already published post."""
        # Mock the publication cache to say the post was already published
        mock_cache = MagicMock()
        mock_cache.post_was_published.return_value = True
        
        post_data = {
            'title': 'Already Published',
            'body_html': '<p>Test content</p>',
            'subtitle': '',
            'canonical_url': '',
            'post_path': 'test.md'
        }
        
        result = substack.create_draft_on_substack(post_data, mock_cache)
        self.assertIsNone(result)
        
        # Verify the API was NOT called
        mock_post.assert_not_called()
        
    @patch('requests.post')
    def test_create_draft_with_canonical_url(self, mock_post):
        """Test creating a draft with a canonical URL."""
        mock_cache = MagicMock()
        mock_cache.post_was_published.return_value = False
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'draft123'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock the duplicate check to return False (no duplicates)
        with patch('publish_to_substack.check_for_duplicate_on_substack', return_value=False):
            post_data = {
                'title': 'Test Draft',
                'body_html': '<p>Test content</p>',
                'subtitle': 'Test subtitle',
                'canonical_url': 'https://example.com/test-post',
                'post_path': 'test.md'
            }
            
            result = substack.create_draft_on_substack(post_data, mock_cache)
            self.assertEqual(result, 'draft123')
            
            # Verify canonical URL was included
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs['json']['canonical_url'], 'https://example.com/test-post')
    
    @patch('requests.post')
    def test_create_draft_duplicate_title(self, mock_post):
        """Test handling a duplicate title detection."""
        mock_cache = MagicMock()
        mock_cache.post_was_published.return_value = False
        
        # Mock the duplicate check to return True (duplicate found)
        with patch('publish_to_substack.check_for_duplicate_on_substack', return_value=True):
            post_data = {
                'title': 'Duplicate Title',
                'body_html': '<p>Test content</p>',
                'subtitle': 'Test subtitle',
                'canonical_url': '',
                'post_path': 'test.md'
            }
            
            result = substack.create_draft_on_substack(post_data, mock_cache)
            self.assertIsNone(result)
            
            # Verify the API was NOT called
            mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_create_draft_api_error(self, mock_post):
        """Test error handling when creating a draft on Substack."""
        mock_cache = MagicMock()
        mock_cache.post_was_published.return_value = False
        
        # Mock API error
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        mock_error_response = MagicMock()
        mock_error_response.text = "Error details"
        mock_post.side_effect.response = mock_error_response
        
        # Mock the duplicate check to return False (no duplicates)
        with patch('publish_to_substack.check_for_duplicate_on_substack', return_value=False):
            post_data = {
                'title': 'Test Draft',
                'body_html': '<p>Test content</p>',
                'subtitle': 'Test subtitle',
                'canonical_url': '',
                'post_path': 'test.md'
            }
            
            result = substack.create_draft_on_substack(post_data, mock_cache)
            self.assertIsNone(result)

    @patch('requests.post')
    def test_publish_post_on_substack(self, mock_post):
        """Test publishing a post on Substack."""
        # Mock the publication cache
        mock_cache = MagicMock()
        mock_cache.can_publish_more_today.return_value = True
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        post_data = {
            'title': 'Test Publish',
            'body_html': '<p>Test content</p>',
            'status': 'published',
            'audience': 'everyone',
            'post_path': 'test.md'
        }
        
        # Test with a draft that should be published
        with patch('publish_to_substack.get_content_hash', return_value='test_hash'):
            result = substack.publish_post_on_substack('draft123', post_data, mock_cache)
            self.assertTrue(result)
            
            # Verify the API was called correctly
            mock_post.assert_called_once()
            
            # Verify the publication was recorded
            mock_cache.record_publication.assert_called_once()

    @patch('publish_to_substack.FORCE_PUBLISH', False)
    @patch('requests.post')
    def test_publish_post_limit_reached(self, mock_post):
        """Test publishing when daily limit is reached."""
        # Mock the publication cache to say we can't publish more
        mock_cache = MagicMock()
        mock_cache.can_publish_more_today.return_value = False
        
        post_data = {
            'title': 'Test Limit',
            'body_html': '<p>Test content</p>',
            'status': 'published',
            'audience': 'everyone',
            'post_path': 'test.md'
        }
        
        # Test with FORCE_PUBLISH=false
        with patch('publish_to_substack.FORCE_PUBLISH', False):
            result = substack.publish_post_on_substack('draft123', post_data, mock_cache)
            self.assertFalse(result)
            
            # Verify the API was NOT called
            mock_post.assert_not_called()
            
            # Verify publication was NOT recorded
            mock_cache.record_publication.assert_not_called()
        
        # Test with FORCE_PUBLISH=true
        with patch('publish_to_substack.FORCE_PUBLISH', True):
            # Reset the mock
            mock_post.reset_mock()
            
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with patch('publish_to_substack.get_content_hash', return_value='test_hash'):
                result = substack.publish_post_on_substack('draft123', post_data, mock_cache)
                self.assertTrue(result)
                
                # Verify the API WAS called this time
                mock_post.assert_called_once()

    def test_publication_cache_load_save(self):
        """Test loading and saving the publication cache."""
        # Test creating a new cache when file doesn't exist
        cache = substack.PublicationCache(self.cache_path)
        self.assertEqual(cache.cache['published_posts'], {})
        self.assertEqual(cache.cache['last_publication_count_24h'], 0)
        
        # Test saving cache
        cache.cache['published_posts']['test.md'] = 'test_hash'
        cache.cache['last_publication_count_24h'] = 1
        cache._save_cache()
        
        # Verify the file was created
        self.assertTrue(os.path.exists(self.cache_path))
        
        # Test loading existing cache
        new_cache = substack.PublicationCache(self.cache_path)
        self.assertEqual(new_cache.cache['published_posts']['test.md'], 'test_hash')
        self.assertEqual(new_cache.cache['last_publication_count_24h'], 1)

    def test_publication_cache_tracking(self):
        """Test tracking publications in the cache."""
        # Directly patch MAX_PUBLICATIONS_PER_DAY
        with patch('publish_to_substack.MAX_PUBLICATIONS_PER_DAY', 2):
            # Create a new cache instance
            cache = substack.PublicationCache(self.cache_path)
            
            # Set the initial state
            cache.cache['published_posts'] = {}
            cache.cache['last_publication_dates'] = []
            cache.cache['last_publication_count_24h'] = 0
            
            # Should be able to publish initially
            self.assertTrue(cache.can_publish_more_today())
            
            # Record a publication
            cache.record_publication('post1.md', 'hash1')
            
            # Should still be able to publish (limit is 2)
            self.assertTrue(cache.can_publish_more_today())
            self.assertEqual(cache.get_published_count_24h(), 1)
            
            # Record another publication
            cache.record_publication('post2.md', 'hash2')
            
            # Now we should hit the limit
            self.assertFalse(cache.can_publish_more_today())
            self.assertEqual(cache.get_published_count_24h(), 2)
            
            # Test post_was_published
            self.assertTrue(cache.post_was_published('post1.md', 'hash1'))
            self.assertFalse(cache.post_was_published('post3.md', 'hash3'))

    def test_publication_cache_cleanup(self):
        """Test cleaning up old entries in the publication cache."""
        cache = substack.PublicationCache(self.cache_path)
        
        # Add an old entry (more than 24 hours ago)
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        cache.cache['last_publication_dates'].append(old_time)
        
        # Add a recent entry
        recent_time = datetime.now().isoformat()
        cache.cache['last_publication_dates'].append(recent_time)
        
        # Force update of count
        cache.can_publish_more_today()
        
        # Should only count the recent entry
        self.assertEqual(cache.get_published_count_24h(), 1)


    @patch('sys.exit')
    def test_main_function(self, mock_exit):
        """Test the main function."""
        # Test with valid environment
        with patch('publish_to_substack.validate_environment', return_value=True), \
             patch('publish_to_substack.PublicationCache'), \
             patch('publish_to_substack.get_changed_posts', return_value=['post1.md']), \
             patch('publish_to_substack.process_post', return_value={'title': 'Test Post', 'status': 'draft'}), \
             patch('publish_to_substack.create_draft_on_substack', return_value='draft123'):
            substack.main()
            mock_exit.assert_not_called()
    
    @patch('sys.exit')
    def test_main_function_invalid_env(self, mock_exit):
        """Test the main function with invalid environment."""
        with patch('publish_to_substack.validate_environment', return_value=False):
            substack.main()
            mock_exit.assert_called_once_with(1)
    
    @patch('sys.exit')
    def test_main_function_published_post(self, mock_exit):
        """Test the main function with a post marked for publishing."""
        post_data = {
            'title': 'Test Post',
            'body_html': '<p>Content</p>',
            'status': 'published',
            'audience': 'everyone',
            'post_path': 'post1.md'
        }
        with patch('publish_to_substack.validate_environment', return_value=True), \
             patch('publish_to_substack.PublicationCache'), \
             patch('publish_to_substack.get_changed_posts', return_value=['post1.md']), \
             patch('publish_to_substack.process_post', return_value=post_data), \
             patch('publish_to_substack.create_draft_on_substack', return_value='draft123'), \
             patch('publish_to_substack.publish_post_on_substack', return_value=True):
            substack.main()
            mock_exit.assert_not_called()
    
    def test_publication_cache_error_handling(self):
        """Test error handling in the publication cache."""
        # Test loading cache with an invalid file
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=Exception("Mock error")):
            cache = substack.PublicationCache(self.cache_path)
            self.assertEqual(cache.cache['published_posts'], {})
        
        # Test saving cache with an error
        cache = substack.PublicationCache(self.cache_path)
        with patch('builtins.open', side_effect=Exception("Mock error")):
            cache._save_cache()  # Should not raise an exception
            
    @patch('requests.post')
    def test_publish_post_not_published_status(self, mock_post):
        """Test with a post that is not marked for publishing."""
        mock_cache = MagicMock()
        
        post_data = {
            'title': 'Test Draft Only',
            'body_html': '<p>Test content</p>',
            'status': 'draft',  # Not 'published'
            'audience': 'everyone',
            'post_path': 'test.md'
        }
        
        result = substack.publish_post_on_substack('draft123', post_data, mock_cache)
        self.assertFalse(result)
        
        # Verify the API was NOT called
        mock_post.assert_not_called()
            
    @patch('requests.post')
    def test_publish_post_api_error(self, mock_post):
        """Test error handling when publishing to Substack."""
        # Mock the publication cache
        mock_cache = MagicMock()
        mock_cache.can_publish_more_today.return_value = True
        
        # Mock API error
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        mock_error_response = MagicMock()
        mock_error_response.text = "Error details"
        mock_post.side_effect.response = mock_error_response
        
        post_data = {
            'title': 'Test Publish Error',
            'body_html': '<p>Test content</p>',
            'status': 'published',
            'audience': 'everyone',
            'post_path': 'test.md'
        }
        
        result = substack.publish_post_on_substack('draft123', post_data, mock_cache)
        self.assertFalse(result)
        
        # Verify the publication was NOT recorded
        mock_cache.record_publication.assert_not_called()


if __name__ == '__main__':
    unittest.main()