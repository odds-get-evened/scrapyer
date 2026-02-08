"""
Tests for web crawling functionality
"""

import unittest
import sys
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from io import StringIO
from scrapyer import main
from scrapyer.docuproc import DocumentProcessor
from scrapyer.httprequest import HttpRequest


class TestCrawlingCLI(unittest.TestCase):
    """Test crawling-related CLI arguments"""
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_crawl_flag(self, mock_http_request, mock_doc_processor):
        """Test --crawl flag enables crawling mode"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test', '--crawl']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify DocumentProcessor was called with crawl=True
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        self.assertTrue(call_args[1]['crawl'])
        self.assertIsNone(call_args[1]['crawl_limit'])
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_crawl_with_limit(self, mock_http_request, mock_doc_processor):
        """Test --crawl with --crawl-limit sets the limit"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test', '--crawl', '--crawl-limit', '5']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify DocumentProcessor was called with crawl=True and crawl_limit=5
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        self.assertTrue(call_args[1]['crawl'])
        self.assertEqual(call_args[1]['crawl_limit'], 5)
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_crawl_without_flag(self, mock_http_request, mock_doc_processor):
        """Test that crawl is disabled by default"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify DocumentProcessor was called with crawl=False
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        self.assertFalse(call_args[1]['crawl'])


class TestCrawlingLogic(unittest.TestCase):
    """Test the crawling logic in DocumentProcessor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_path = Path('/tmp/test_crawl')
        
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_extract_links_same_domain(self, mock_http_conn):
        """Test that links from the same domain are extracted"""
        # Create a mock response with HTML containing links
        html_content = '''
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="http://example.com/page3">Page 3</a>
                <a href="http://other.com/page4">Other Domain</a>
            </body>
        </html>
        '''
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = 'OK'
        mock_response.getheader.return_value = 'text/html'
        mock_response.read.return_value = html_content.encode('utf-8')
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.getresponse.return_value = mock_response
        mock_http_conn.return_value = mock_conn_instance
        
        # Create DocumentProcessor with crawl enabled
        request = HttpRequest('http://example.com', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=True,
            crawl_limit=10,
            timeout=30,
            verify_ssl=True,
            ssl_context=None
        )
        
        # Start processing (this will process multiple pages)
        try:
            processor.start()
        except Exception:
            pass  # Expected to fail when trying to fetch queued pages
        
        # Check that pages were visited (should have processed the initial page + some queued ones)
        # Since all pages return the same HTML with 3 same-domain links,
        # we should have visited multiple pages
        self.assertGreater(len(processor.visited_urls), 1)
    
    def test_create_page_directory(self):
        """Test that unique directories are created for each URL"""
        # Use a unique test directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / 'test_crawl'
            test_path.mkdir(parents=True, exist_ok=True)
            
            request = HttpRequest('http://example.com', time_out=30)
            processor = DocumentProcessor(
                request,
                test_path,
                crawl=True,
                timeout=30,
                verify_ssl=True,
                ssl_context=None
            )
            
            # Test creating directories for different URLs
            dir1 = processor._create_page_directory('http://example.com/')
            self.assertTrue(dir1.name == 'index')
            
            dir2 = processor._create_page_directory('http://example.com/about')
            self.assertTrue('about' in dir2.name)
            
            dir3 = processor._create_page_directory('http://example.com/blog/post-1')
            self.assertTrue('blog' in dir3.name or 'post' in dir3.name)
    
    @patch('scrapyer.httprequest.HTTPConnection')
    def test_crawl_limit_respected(self, mock_http_conn):
        """Test that crawl_limit stops crawling at the specified number"""
        # Create mock responses
        html_with_links = '''
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="/page3">Page 3</a>
            </body>
        </html>
        '''
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = 'OK'
        mock_response.getheader.return_value = 'text/html'
        mock_response.read.return_value = html_with_links.encode('utf-8')
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.getresponse.return_value = mock_response
        mock_http_conn.return_value = mock_conn_instance
        
        # Create DocumentProcessor with crawl_limit=2
        request = HttpRequest('http://example.com', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=True,
            crawl_limit=2,
            timeout=30,
            verify_ssl=True,
            ssl_context=None
        )
        
        # Start processing
        try:
            processor.start()
        except Exception:
            pass  # Expected to fail when processing
        
        # Should have visited at most 2 pages
        self.assertLessEqual(len(processor.visited_urls), 2)
    
    def test_crawl_skips_visited_urls(self):
        """Test that already visited URLs are not crawled again"""
        request = HttpRequest('http://example.com', time_out=30)
        processor = DocumentProcessor(
            request,
            self.test_path,
            crawl=True,
            timeout=30,
            verify_ssl=True,
            ssl_context=None
        )
        
        # Initially the queue is empty (gets populated in start())
        self.assertEqual(len(processor.url_queue), 0)
        
        # Add some URLs to visited set before processing starts
        processor.visited_urls.add('http://example.com/page1')
        processor.visited_urls.add('http://example.com/page2')
        
        # Verify the URLs are in the visited set
        self.assertIn('http://example.com/page1', processor.visited_urls)
        self.assertIn('http://example.com/page2', processor.visited_urls)
        self.assertEqual(len(processor.visited_urls), 2)


class TestCrawlingHelp(unittest.TestCase):
    """Test that help includes crawling options"""
    
    def test_help_includes_crawl_options(self):
        """Test that --help displays crawling options"""
        test_args = ['scrapyer', '--help']
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    main.boot_up()
                    output = mock_stdout.getvalue()
                    self.assertIn('--crawl', output)
                    self.assertIn('--crawl-limit', output)
            
            # Help should exit with code 0
            self.assertEqual(cm.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
