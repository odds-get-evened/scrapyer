"""
Tests for handling non-HTML content types (e.g., Atom feeds, XML, JSON)
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
from scrapyer.docuproc import DocumentProcessor
from scrapyer.httprequest import HttpRequest


class TestNonHTMLContentHandling(unittest.TestCase):
    """Test that non-HTML content types are handled gracefully"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_path = Path('/tmp/test_non_html')
        
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_atom_xml_feed_skipped(self, mock_http_conn):
        """Test that Atom XML feeds are skipped with a warning instead of crashing"""
        # Create a mock response with Atom XML content type
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = 'OK'
        mock_response.getheader.return_value = 'application/atom+xml; charset=utf-8'
        mock_response.read.return_value = b'<?xml version="1.0"?><feed></feed>'
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.getresponse.return_value = mock_response
        mock_http_conn.return_value = mock_conn_instance
        
        # Create DocumentProcessor
        request = HttpRequest('http://example.com/feed.atom', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=False,
            timeout=30,
            verify_ssl=True,
            ssl_context=None,
            media_types=[]
        )
        
        # Process should not crash - it should skip the URL
        try:
            processor._process_single_page('http://example.com/feed.atom', self.test_path)
            # If we get here, the fix worked - non-HTML content was handled gracefully
            success = True
        except ValueError as e:
            # If we get here, the fix didn't work - ValueError was not caught
            success = False
            self.fail(f"ValueError was not caught: {e}")
        
        self.assertTrue(success, "Non-HTML content should be handled gracefully")
    
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_json_content_skipped(self, mock_http_conn):
        """Test that JSON content is skipped with a warning"""
        # Create a mock response with JSON content type
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = 'OK'
        mock_response.getheader.return_value = 'application/json'
        mock_response.read.return_value = b'{"key": "value"}'
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.getresponse.return_value = mock_response
        mock_http_conn.return_value = mock_conn_instance
        
        # Create DocumentProcessor
        request = HttpRequest('http://example.com/api/data.json', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=False,
            timeout=30,
            verify_ssl=True,
            ssl_context=None,
            media_types=[]
        )
        
        # Process should not crash
        try:
            processor._process_single_page('http://example.com/api/data.json', self.test_path)
            success = True
        except ValueError as e:
            success = False
            self.fail(f"ValueError was not caught: {e}")
        
        self.assertTrue(success, "JSON content should be handled gracefully")
    
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_rss_feed_skipped(self, mock_http_conn):
        """Test that RSS feeds are skipped with a warning"""
        # Create a mock response with RSS/XML content type
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = 'OK'
        mock_response.getheader.return_value = 'application/rss+xml'
        mock_response.read.return_value = b'<?xml version="1.0"?><rss></rss>'
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.getresponse.return_value = mock_response
        mock_http_conn.return_value = mock_conn_instance
        
        # Create DocumentProcessor
        request = HttpRequest('http://example.com/feed.rss', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=False,
            timeout=30,
            verify_ssl=True,
            ssl_context=None,
            media_types=[]
        )
        
        # Process should not crash
        try:
            processor._process_single_page('http://example.com/feed.rss', self.test_path)
            success = True
        except ValueError as e:
            success = False
            self.fail(f"ValueError was not caught: {e}")
        
        self.assertTrue(success, "RSS feed should be handled gracefully")
    
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_crawling_with_non_html_links(self, mock_http_conn):
        """Test that crawling continues when encountering non-HTML links"""
        # Create HTML content with links to both HTML pages and non-HTML resources
        html_content = '''
        <html>
            <body>
                <a href="/page1.html">Page 1</a>
                <a href="/feed.atom">Atom Feed</a>
                <a href="/page2.html">Page 2</a>
            </body>
        </html>
        '''
        
        # Create different responses for different URLs
        def get_response_for_url(url):
            if 'feed.atom' in url:
                # Non-HTML response
                response = MagicMock()
                response.status = 200
                response.reason = 'OK'
                response.getheader.return_value = 'application/atom+xml; charset=utf-8'
                response.read.return_value = b'<?xml version="1.0"?><feed></feed>'
            else:
                # HTML response
                response = MagicMock()
                response.status = 200
                response.reason = 'OK'
                response.getheader.return_value = 'text/html'
                response.read.return_value = html_content.encode('utf-8')
            return response
        
        # Mock to return different responses based on URL
        mock_conn_instance = MagicMock()
        mock_http_conn.return_value = mock_conn_instance
        
        # Track which URLs are requested
        requested_urls = []
        
        def track_request(method, path, **kwargs):
            requested_urls.append(path)
            # Determine which response to return based on path
            return get_response_for_url(path)
        
        mock_conn_instance.request.side_effect = track_request
        mock_conn_instance.getresponse.side_effect = lambda: get_response_for_url(
            requested_urls[-1] if requested_urls else '/'
        )
        
        # Create DocumentProcessor with crawl enabled
        request = HttpRequest('http://example.com', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=True,
            crawl_limit=5,
            timeout=30,
            verify_ssl=True,
            ssl_context=None,
            media_types=[]
        )
        
        # Start processing - should handle non-HTML URLs gracefully
        try:
            processor.start()
        except Exception as e:
            # Allow network-related exceptions but not ValueError
            if isinstance(e, ValueError):
                self.fail(f"ValueError should be caught and handled: {e}")
        
        # Verify that some URLs were visited (the HTML ones)
        self.assertGreater(len(processor.visited_urls), 0, "Should have visited at least one URL")


class TestHTMLContentProcessing(unittest.TestCase):
    """Test that valid HTML content is still processed correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_path = Path('/tmp/test_html_processing')
    
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_html_content_processed_normally(self, mock_http_conn):
        """Test that HTML content is still processed normally after our fix"""
        # Create a mock response with HTML content
        html_content = '<html><body><p>Test content</p></body></html>'
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = 'OK'
        mock_response.getheader.return_value = 'text/html; charset=utf-8'
        mock_response.read.return_value = html_content.encode('utf-8')
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.getresponse.return_value = mock_response
        mock_http_conn.return_value = mock_conn_instance
        
        # Create DocumentProcessor
        request = HttpRequest('http://example.com', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=False,
            timeout=30,
            verify_ssl=True,
            ssl_context=None,
            media_types=[]
        )
        
        # Process should work normally
        try:
            processor._process_single_page('http://example.com/', self.test_path)
            # Verify that the DOM was parsed
            self.assertIsNotNone(processor.dom, "DOM should be parsed for HTML content")
            success = True
        except Exception as e:
            success = False
            self.fail(f"HTML content processing failed: {e}")
        
        self.assertTrue(success, "HTML content should be processed normally")


if __name__ == '__main__':
    unittest.main()
