"""
Tests for text-only mode and unique content filenames
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from io import StringIO, BytesIO
from http.client import HTTPResponse

from scrapyer import main
from scrapyer.docuproc import DocumentProcessor
from scrapyer.httprequest import HttpRequest


class TestTextOnlyMode(unittest.TestCase):
    """Test text-only mode functionality"""
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_text_only_flag_disables_media(self, mock_http_request, mock_doc_processor):
        """Test that --text-only flag disables all media downloads"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test', '--text-only']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
        
        # Verify DocumentProcessor was called with empty media_types list
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        self.assertEqual(call_args[1]['media_types'], [])
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_text_only_with_media_types_ignores_media_types(self, mock_http_request, mock_doc_processor):
        """Test that --text-only takes precedence over --media-types"""
        test_args = [
            'scrapyer', 
            'http://example.com', 
            '/tmp/test',
            '--text-only',
            '--media-types', 'images,videos'
        ]
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
        
        # Verify DocumentProcessor was called with empty media_types list
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        self.assertEqual(call_args[1]['media_types'], [])
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_without_text_only_flag_media_enabled(self, mock_http_request, mock_doc_processor):
        """Test that media is enabled by default when --text-only is not used"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
        
        # Verify DocumentProcessor was called with default media_types
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        # Default media types should include images, videos, and audio
        self.assertIn('images', call_args[1]['media_types'])
        self.assertIn('videos', call_args[1]['media_types'])
        self.assertIn('audio', call_args[1]['media_types'])
    
    def test_help_includes_text_only_option(self):
        """Test that --help displays the text-only option"""
        test_args = ['scrapyer', '--help']
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    main.boot_up()
                    output = mock_stdout.getvalue()
                    self.assertIn('--text-only', output)
            
            # Help should exit with code 0
            self.assertEqual(cm.exception.code, 0)


class TestUniqueContentFilenames(unittest.TestCase):
    """Test unique filename generation for content files"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.save_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_response(self, html_content):
        """Helper to create a mock HTTP response"""
        mock_response = Mock(spec=HTTPResponse)
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "text/html"
        mock_response.read.return_value = html_content.encode('utf-8')
        return mock_response
    
    def test_unique_filename_for_root_url(self):
        """Test that root URL generates 'index_<hash>_content.txt'"""
        # Create a real request object but mock the network call
        with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
            mock_conn_instance = Mock()
            mock_http_conn.return_value = mock_conn_instance
            
            mock_response = self._create_mock_response("<html><body>Test</body></html>")
            mock_conn_instance.getresponse.return_value = mock_response
            
            # Create real request
            request = HttpRequest("http://example.com/", time_out=30)
            
            # Create processor with empty media types (text-only)
            proc = DocumentProcessor(
                request, 
                self.save_path,
                media_types=[]
            )
            
            # Process the page
            proc._process_single_page("http://example.com/", self.save_path)
            
            # Check that a file with 'index_' prefix was created
            content_files = list(self.save_path.glob("index_*_content.txt"))
            self.assertEqual(len(content_files), 1)
            self.assertTrue(content_files[0].name.startswith('index_'))
            self.assertTrue(content_files[0].name.endswith('_content.txt'))
    
    def test_unique_filename_for_path_url(self):
        """Test that URL with path generates unique filename based on path"""
        with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
            mock_conn_instance = Mock()
            mock_http_conn.return_value = mock_conn_instance
            
            mock_response = self._create_mock_response("<html><body>Test</body></html>")
            mock_conn_instance.getresponse.return_value = mock_response
            
            # Create real request
            request = HttpRequest("http://example.com/blog/article", time_out=30)
            
            # Create processor with empty media types (text-only)
            proc = DocumentProcessor(
                request, 
                self.save_path,
                media_types=[]
            )
            
            # Process the page
            proc._process_single_page("http://example.com/blog/article", self.save_path)
            
            # Check that a file with 'article_' prefix was created
            content_files = list(self.save_path.glob("article_*_content.txt"))
            self.assertEqual(len(content_files), 1)
            self.assertTrue(content_files[0].name.startswith('article_'))
            self.assertTrue(content_files[0].name.endswith('_content.txt'))
    
    def test_different_urls_generate_different_filenames(self):
        """Test that different URLs generate different unique filenames"""
        # Test two different URLs
        urls_and_paths = [
            ("http://example.com/", "/"),
            ("http://example.com/page1", "/page1")
        ]
        
        filenames = []
        for url, path in urls_and_paths:
            with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
                mock_conn_instance = Mock()
                mock_http_conn.return_value = mock_conn_instance
                
                request = HttpRequest(url, time_out=30)
                
                proc = DocumentProcessor(
                    request, 
                    self.save_path,
                    media_types=[]
                )
                
                # Generate filename
                filename = proc._generate_content_filename(request)
                filenames.append(filename)
        
        # Verify that both filenames are unique
        self.assertEqual(len(filenames), 2)
        self.assertNotEqual(filenames[0], filenames[1])
        
        # Verify both end with _content.txt
        for filename in filenames:
            self.assertTrue(filename.endswith('_content.txt'))
    
    def test_no_content_txt_created(self):
        """Test that 'content.txt' is NOT created (only unique filenames)"""
        with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
            mock_conn_instance = Mock()
            mock_http_conn.return_value = mock_conn_instance
            
            mock_response = self._create_mock_response("<html><body>Test</body></html>")
            mock_conn_instance.getresponse.return_value = mock_response
            
            request = HttpRequest("http://example.com/", time_out=30)
            
            proc = DocumentProcessor(
                request, 
                self.save_path,
                media_types=[]
            )
            
            # Process the page
            proc._process_single_page("http://example.com/", self.save_path)
            
            # Verify that 'content.txt' does NOT exist
            content_txt = self.save_path / 'content.txt'
            self.assertFalse(content_txt.exists())
            
            # Verify that a unique content file was created
            content_files = list(self.save_path.glob("*_content.txt"))
            self.assertGreater(len(content_files), 0)


class TestMediaSkippingInTextOnlyMode(unittest.TestCase):
    """Test that media downloads are skipped in text-only mode"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.save_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_response(self, html_content):
        """Helper to create a mock HTTP response"""
        mock_response = Mock(spec=HTTPResponse)
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "text/html"
        mock_response.read.return_value = html_content.encode('utf-8')
        return mock_response
    
    def test_media_extraction_skipped_when_empty_media_types(self):
        """Test that media extraction is skipped when media_types is empty"""
        html_with_images = """
        <html>
        <body>
            <img src="image1.jpg">
            <img src="image2.jpg">
            <p>Some text</p>
        </body>
        </html>
        """
        
        with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
            mock_conn_instance = Mock()
            mock_http_conn.return_value = mock_conn_instance
            
            mock_response = self._create_mock_response(html_with_images)
            mock_conn_instance.getresponse.return_value = mock_response
            
            request = HttpRequest("http://example.com/", time_out=30)
            
            # Create processor with empty media types (text-only)
            proc = DocumentProcessor(
                request, 
                self.save_path,
                media_types=[]
            )
            
            # Process the page
            proc._process_single_page("http://example.com/", self.save_path)
            
            # Verify that no media subdirectories were created
            self.assertFalse((self.save_path / 'images').exists())
            self.assertFalse((self.save_path / 'videos').exists())
            self.assertFalse((self.save_path / 'audio').exists())
            
            # Verify that text content was still saved
            content_files = list(self.save_path.glob("*_content.txt"))
            self.assertGreater(len(content_files), 0)


if __name__ == '__main__':
    unittest.main()
