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
        """Test that root URL generates 'content_<hash>.txt'"""
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
            
            # Check that a file with 'content_' prefix was created
            content_files = list(self.save_path.glob("content_*.txt"))
            self.assertEqual(len(content_files), 1)
            self.assertTrue(content_files[0].name.startswith('content_'))
            self.assertTrue(content_files[0].name.endswith('.txt'))
    
    def test_unique_filename_for_path_url(self):
        """Test that URL with path generates unique filename based on content hash"""
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
            
            # Check that a file with 'content_' prefix was created
            content_files = list(self.save_path.glob("content_*.txt"))
            self.assertEqual(len(content_files), 1)
            self.assertTrue(content_files[0].name.startswith('content_'))
            self.assertTrue(content_files[0].name.endswith('.txt'))
    
    def test_different_urls_generate_different_filenames(self):
        """Test that different content generates different unique filenames"""
        # Create processor
        request = HttpRequest("http://example.com/", time_out=30)
        proc = DocumentProcessor(
            request, 
            self.save_path,
            media_types=[]
        )
        
        # Generate filenames for different content
        content1 = "This is content from page 1"
        content2 = "This is different content from page 2"
        
        filename1 = proc._generate_content_filename(content1)
        filename2 = proc._generate_content_filename(content2)
        
        # Verify that both filenames are unique
        self.assertNotEqual(filename1, filename2)
        
        # Verify both start with 'content_' and end with '.txt'
        self.assertTrue(filename1.startswith('content_'))
        self.assertTrue(filename1.endswith('.txt'))
        self.assertTrue(filename2.startswith('content_'))
        self.assertTrue(filename2.endswith('.txt'))
    
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
            content_files = list(self.save_path.glob("content_*.txt"))
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
            content_files = list(self.save_path.glob("content_*.txt"))
            self.assertGreater(len(content_files), 0)


class TestEmptyContentHandling(unittest.TestCase):
    """Test that empty content pages don't create files"""
    
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
    
    def test_empty_page_creates_no_file(self):
        """Test that a page with no content doesn't create a file"""
        # HTML with no meaningful content
        empty_html = """
        <html>
        <head><title>Empty Page</title></head>
        <body>
            <script>console.log("test");</script>
            <style>.test { color: red; }</style>
        </body>
        </html>
        """
        
        with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
            mock_conn_instance = Mock()
            mock_http_conn.return_value = mock_conn_instance
            
            mock_response = self._create_mock_response(empty_html)
            mock_conn_instance.getresponse.return_value = mock_response
            
            request = HttpRequest("http://example.com/empty", time_out=30)
            
            proc = DocumentProcessor(
                request, 
                self.save_path,
                media_types=[]
            )
            
            # Process the page
            proc._process_single_page("http://example.com/empty", self.save_path)
            
            # Verify that no content files were created
            content_files = list(self.save_path.glob("content_*.txt"))
            self.assertEqual(len(content_files), 0, "No files should be created for empty content")
            
            # Verify that no directories were created
            subdirs = [d for d in self.save_path.iterdir() if d.is_dir()]
            self.assertEqual(len(subdirs), 0, "No directories should be created for empty content")
    
    def test_empty_page_no_base_directory_created(self):
        """Test that even the base save_path directory is not created for empty content when it doesn't exist"""
        # Use a non-existent directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path that doesn't exist yet
            new_save_path = Path(tmpdir) / 'nonexistent' / 'subdir'
            
            # HTML with no meaningful content
            empty_html = """
            <html>
            <head><title>Empty Page</title></head>
            <body>
                <script>console.log("test");</script>
            </body>
            </html>
            """
            
            with patch('scrapyer.httprequest.HTTPConnection') as mock_http_conn:
                mock_conn_instance = Mock()
                mock_http_conn.return_value = mock_conn_instance
                
                mock_response = self._create_mock_response(empty_html)
                mock_conn_instance.getresponse.return_value = mock_response
                
                request = HttpRequest("http://example.com/empty", time_out=30)
                
                proc = DocumentProcessor(
                    request, 
                    new_save_path,
                    media_types=[]
                )
                
                # Process the page
                proc._process_single_page("http://example.com/empty", new_save_path)
                
                # Verify that the directory was not created at all
                self.assertFalse(new_save_path.exists(), "Base directory should not be created for empty content")


if __name__ == '__main__':
    unittest.main()
