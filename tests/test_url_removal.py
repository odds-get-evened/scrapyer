"""
Tests to verify that URLs are completely removed from text content
"""

import unittest
from pathlib import Path
from unittest.mock import Mock
from bs4 import BeautifulSoup
import tempfile
import shutil

from scrapyer.docuproc import DocumentProcessor


class TestURLRemoval(unittest.TestCase):
    """Test that all URLs are removed from extracted text content"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.save_path = Path(self.temp_dir)
        
        # Create a mock request
        self.mock_request = Mock()
        self.mock_request.get_root_url.return_value = "http://example.com"
        self.mock_request.build_url_path.return_value = ""
        self.mock_request.absolute_source = lambda x: f"http://example.com/{x}" if not x.startswith('http') else x
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_urls_in_parentheses_removed(self):
        """Test that URLs in parentheses are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>Article (https://en.wikipedia.org/wiki/Idiosyncrasy)</p>
                <p>Talk (https://en.wikipedia.org/wiki/Talk:Idiosyncrasy)</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check that the text contains the words but not the URLs
        self.assertIn('Article', text)
        self.assertIn('Talk', text)
        self.assertNotIn('https://', text)
        self.assertNotIn('http://', text)
        self.assertNotIn('wikipedia.org', text)
    
    def test_urls_in_brackets_removed(self):
        """Test that URLs in brackets are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>See reference [https://en.wikipedia.org/wiki/Reference]</p>
                <p>Citation [1] (https://example.com/cite)</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check that text is present but URLs are not
        self.assertIn('See reference', text)
        self.assertIn('Citation', text)
        self.assertIn('[1]', text)
        self.assertNotIn('https://', text)
        self.assertNotIn('http://', text)
        self.assertNotIn('example.com', text)
        self.assertNotIn('wikipedia.org', text)
    
    def test_standalone_urls_removed(self):
        """Test that standalone URLs not in parentheses/brackets are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>Visit http://example.com for more information.</p>
                <p>Check out www.example.org or https://test.com</p>
                <p>FTP available at ftp://files.example.com/downloads</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check that descriptive text remains but URLs are removed
        self.assertIn('Visit', text)
        self.assertIn('for more information', text)
        self.assertIn('Check out', text)
        self.assertIn('FTP available at', text)
        
        # Verify no URLs remain
        self.assertNotIn('http://', text)
        self.assertNotIn('https://', text)
        self.assertNotIn('www.', text)
        self.assertNotIn('ftp://', text)
        self.assertNotIn('example.com', text)
        self.assertNotIn('example.org', text)
        self.assertNotIn('test.com', text)
    
    def test_wikipedia_style_content(self):
        """Test with Wikipedia-style content that has many URLs"""
        html = """
        <html>
        <body>
            <article>
                <h1>Idiosyncrasy</h1>
                <p>Article (https://en.wikipedia.org/wiki/Idiosyncrasy)</p>
                <p>Talk (https://en.wikipedia.org/wiki/Talk:Idiosyncrasy)</p>
                <p>(Redirected from Idiosyncrasies (https://en.wikipedia.org/w/index.php?title=Idiosyncrasies&redirect=no))</p>
                <p>An idiosyncrasy is a unique feature of something. The term is often used to express peculiarity.</p>
                <p>[1] (https://en.wikipedia.org/wiki/Idiosyncrasies#cite_note-1)</p>
                <p>[2] (https://en.wikipedia.org/wiki/Idiosyncrasies#cite_note-2)</p>
                <h2>Etymology</h2>
                <p>edit (https://en.wikipedia.org/w/index.php?title=Idiosyncrasy&action=edit&section=1)</p>
                <p>The term "idiosyncrasy" originates from Greek (https://en.wikipedia.org/wiki/Greek_language)</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check that content text is preserved
        self.assertIn('Idiosyncrasy', text)
        self.assertIn('unique feature', text)
        self.assertIn('Etymology', text)
        self.assertIn('originates from Greek', text)
        
        # Verify absolutely no URLs are present
        self.assertNotIn('https://', text)
        self.assertNotIn('http://', text)
        self.assertNotIn('wikipedia.org', text)
        self.assertNotIn('en.wikipedia', text)
        self.assertNotIn('.org', text)
        self.assertNotIn('.com', text)
        self.assertNotIn('index.php', text)
        
        # Check that citation markers remain but not the URLs
        self.assertIn('[1]', text)
        self.assertIn('[2]', text)
    
    def test_mixed_url_formats(self):
        """Test removal of URLs in various mixed formats"""
        html = """
        <html>
        <body>
            <article>
                <p>Resources: https://example.com, www.test.org, and (http://another.com)</p>
                <p>References [https://ref1.com] and [https://ref2.com]</p>
                <p>More at ftp://files.example.com/data or https://secure.example.com/path?query=value#anchor</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check descriptive text remains
        self.assertIn('Resources:', text)
        self.assertIn('References', text)
        self.assertIn('More at', text)
        
        # Verify no URLs remain
        self.assertNotIn('http://', text)
        self.assertNotIn('https://', text)
        self.assertNotIn('www.', text)
        self.assertNotIn('ftp://', text)
        self.assertNotIn('.com', text)
        self.assertNotIn('.org', text)
    
    def test_url_query_parameters_removed(self):
        """Test that URLs with complex query parameters are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>Search results (https://example.com/search?q=test&lang=en&filter=active)</p>
                <p>API endpoint (https://api.example.com/v1/data?key=abc123&format=json)</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check text remains
        self.assertIn('Search results', text)
        self.assertIn('API endpoint', text)
        
        # Verify URLs are completely removed
        self.assertNotIn('https://', text)
        self.assertNotIn('example.com', text)
        self.assertNotIn('?q=', text)
        self.assertNotIn('&lang=', text)
        self.assertNotIn('api.', text)
    
    def test_url_fragments_removed(self):
        """Test that URLs with fragments/anchors are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>See section (https://example.com/page#section-1)</p>
                <p>Jump to (https://docs.example.com/guide#getting-started)</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Check text remains
        self.assertIn('See section', text)
        self.assertIn('Jump to', text)
        
        # Verify URLs with fragments are removed
        self.assertNotIn('https://', text)
        self.assertNotIn('example.com', text)
        self.assertNotIn('#section', text)
        self.assertNotIn('#getting', text)


if __name__ == '__main__':
    unittest.main()
