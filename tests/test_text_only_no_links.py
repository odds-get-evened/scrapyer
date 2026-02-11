"""
Tests to verify that --text-only mode removes all HTML including links
"""

import unittest
from pathlib import Path
from unittest.mock import Mock
from bs4 import BeautifulSoup
import tempfile
import shutil

from scrapyer.docuproc import DocumentProcessor


class TestTextOnlyNoLinks(unittest.TestCase):
    """Test that text-only mode extracts only text without URLs"""
    
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
    
    def test_links_removed_urls_not_in_text(self):
        """Test that URLs are not included in extracted text"""
        html = """
        <html>
        <body>
            <article>
                <h1>Article Title</h1>
                <p>Visit <a href="http://example.com">our website</a> for more information.</p>
                <p>Check the <a href="/docs/guide.html">documentation</a> for details.</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Link text should be present
        self.assertIn('our website', text)
        self.assertIn('documentation', text)
        
        # URLs should NOT be present
        self.assertNotIn('http://example.com', text)
        self.assertNotIn('/docs/guide.html', text)
        self.assertNotIn('(http', text)  # No URL in parentheses format
    
    def test_link_text_preserved(self):
        """Test that link text is preserved even when URLs are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>Click <a href="https://github.com">here</a> to view the repository.</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # The word "here" (link text) should be present
        self.assertIn('here', text)
        # URL should NOT be present
        self.assertNotIn('github.com', text)
        self.assertNotIn('https://', text)
    
    def test_empty_links_removed(self):
        """Test that empty links are removed properly"""
        html = """
        <html>
        <body>
            <article>
                <p>Some text <a href="http://example.com"></a> with empty link.</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Text should be present
        self.assertIn('Some text', text)
        self.assertIn('with empty link', text)
        # URL should NOT be present
        self.assertNotIn('http://example.com', text)
    
    def test_multiple_links_in_paragraph(self):
        """Test handling of multiple links in a single paragraph"""
        html = """
        <html>
        <body>
            <article>
                <p>Read the <a href="/guide">guide</a> and <a href="/tutorial">tutorial</a> for help.</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Link texts should be present
        self.assertIn('guide', text)
        self.assertIn('tutorial', text)
        # URLs should NOT be present
        self.assertNotIn('/guide', text)
        self.assertNotIn('/tutorial', text)
    
    def test_only_content_elements_extracted(self):
        """Test that only content from document elements like p, h1, h2, etc. is extracted"""
        html = """
        <html>
        <head>
            <title>Page Title</title>
            <script>console.log('script');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <nav>Navigation Menu</nav>
            <header>Header Content</header>
            <article>
                <h1>Main Heading</h1>
                <h2>Subheading</h2>
                <p>This is a paragraph with actual content.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </article>
            <footer>Footer Content</footer>
            <script>alert('another script');</script>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Content elements should be present
        self.assertIn('Main Heading', text)
        self.assertIn('Subheading', text)
        self.assertIn('This is a paragraph', text)
        self.assertIn('List item 1', text)
        self.assertIn('List item 2', text)
        
        # Non-content elements should NOT be present
        self.assertNotIn('Navigation Menu', text)
        self.assertNotIn('Header Content', text)
        self.assertNotIn('Footer Content', text)
        self.assertNotIn('console.log', text)
        self.assertNotIn('color: red', text)
        self.assertNotIn('alert', text)
    
    def test_strictly_text_no_html_tags(self):
        """Test that HTML tags are completely removed from text"""
        html = """
        <html>
        <body>
            <article>
                <p>Text with <strong>bold</strong> and <em>italic</em> formatting.</p>
                <p>Text with <span class="highlight">highlighted</span> content.</p>
            </article>
        </body>
        </html>
        """
        
        processor = DocumentProcessor(self.mock_request, self.save_path, media_types=[])
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        text = processor.save_text(self.save_path, self.mock_request)
        
        # Text content should be present
        self.assertIn('bold', text)
        self.assertIn('italic', text)
        self.assertIn('highlighted', text)
        
        # HTML tags should NOT be present
        self.assertNotIn('<strong>', text)
        self.assertNotIn('</strong>', text)
        self.assertNotIn('<em>', text)
        self.assertNotIn('</em>', text)
        self.assertNotIn('<span', text)
        self.assertNotIn('</span>', text)
        self.assertNotIn('<p>', text)
        self.assertNotIn('</p>', text)


if __name__ == '__main__':
    unittest.main()
