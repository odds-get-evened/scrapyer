"""
Tests for content filtering of navigation and UI elements
"""

import re
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scrapyer.docuproc import DocumentProcessor, EXCLUDED_ELEMENTS, EXCLUDED_ROLES, EXCLUDED_CLASS_ID_PATTERNS
from unittest.mock import MagicMock, patch


class TestContentFiltering(unittest.TestCase):
    """Test filtering of navigation and UI elements"""
    
    def test_excluded_elements_includes_ui_components(self):
        """Test that EXCLUDED_ELEMENTS includes form, button, and dialog"""
        self.assertIn('form', EXCLUDED_ELEMENTS)
        self.assertIn('button', EXCLUDED_ELEMENTS)
        self.assertIn('dialog', EXCLUDED_ELEMENTS)
    
    def test_excluded_roles_defined(self):
        """Test that EXCLUDED_ROLES includes navigation-related ARIA roles"""
        self.assertIn('navigation', EXCLUDED_ROLES)
        self.assertIn('banner', EXCLUDED_ROLES)
        self.assertIn('complementary', EXCLUDED_ROLES)
        self.assertIn('contentinfo', EXCLUDED_ROLES)
    
    def test_excluded_patterns_defined(self):
        """Test that EXCLUDED_CLASS_ID_PATTERNS includes common UI patterns"""
        # Check each expected keyword exists as a standalone pattern (not as substring)
        expected_patterns = ['sidebar', 'menu', 'breadcrumb', 'advertisement', 'modal']
        
        for expected in expected_patterns:
            # Check if the pattern exists as a complete match or word boundary
            found = any(
                expected == pattern or  # Exact match
                re.search(r'\b' + re.escape(expected) + r'\b', pattern)  # Word boundary match
                for pattern in EXCLUDED_CLASS_ID_PATTERNS
            )
            self.assertTrue(found, f"Pattern '{expected}' not found in EXCLUDED_CLASS_ID_PATTERNS")
    
    @patch('scrapyer.docuproc.HttpRequest')
    def test_filter_navigation_elements_by_role(self, mock_request):
        """Test filtering elements by ARIA role attribute"""
        # Create a simple HTML document with navigation role
        html = """
        <html>
        <body>
            <div role="navigation">
                <a href="#">Nav Link 1</a>
                <a href="#">Nav Link 2</a>
            </div>
            <article>
                <p>Main content here</p>
            </article>
        </body>
        </html>
        """
        
        # Create processor instance
        mock_request.return_value.get_root_url.return_value = "http://example.com"
        mock_request.return_value.build_url_path.return_value = ""
        
        processor = DocumentProcessor(mock_request, Path('/tmp/test'))
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        # Extract text (which should filter navigation)
        with patch.object(processor.request, 'absolute_source', return_value='http://example.com'):
            text = processor.save_text(Path('/tmp/test_filter'), processor.request)
        
        # Navigation content should be filtered out
        self.assertNotIn('Nav Link 1', text)
        self.assertNotIn('Nav Link 2', text)
        # Main content should remain
        self.assertIn('Main content here', text)
    
    @patch('scrapyer.docuproc.HttpRequest')
    def test_filter_sidebar_by_class(self, mock_request):
        """Test filtering elements with sidebar class"""
        html = """
        <html>
        <body>
            <div class="sidebar">
                <p>Sidebar widget</p>
            </div>
            <article>
                <p>Article content</p>
            </article>
        </body>
        </html>
        """
        
        mock_request.return_value.get_root_url.return_value = "http://example.com"
        mock_request.return_value.build_url_path.return_value = ""
        
        processor = DocumentProcessor(mock_request, Path('/tmp/test'))
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        with patch.object(processor.request, 'absolute_source', return_value='http://example.com'):
            text = processor.save_text(Path('/tmp/test_filter'), processor.request)
        
        # Sidebar content should be filtered
        self.assertNotIn('Sidebar widget', text)
        # Main content should remain
        self.assertIn('Article content', text)
    
    @patch('scrapyer.docuproc.HttpRequest')
    def test_filter_menu_by_id(self, mock_request):
        """Test filtering elements with menu-related id"""
        html = """
        <html>
        <body>
            <div id="nav-menu">
                <a href="#">Menu Item</a>
            </div>
            <main>
                <p>Main text content</p>
            </main>
        </body>
        </html>
        """
        
        mock_request.return_value.get_root_url.return_value = "http://example.com"
        mock_request.return_value.build_url_path.return_value = ""
        
        processor = DocumentProcessor(mock_request, Path('/tmp/test'))
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        with patch.object(processor.request, 'absolute_source', return_value='http://example.com'):
            text = processor.save_text(Path('/tmp/test_filter'), processor.request)
        
        # Menu content should be filtered
        self.assertNotIn('Menu Item', text)
        # Main content should remain
        self.assertIn('Main text content', text)
    
    @patch('scrapyer.docuproc.HttpRequest')
    def test_filter_multiple_patterns(self, mock_request):
        """Test filtering multiple UI patterns simultaneously"""
        html = """
        <html>
        <body>
            <nav>Top Nav</nav>
            <div class="breadcrumb">Home > Page</div>
            <aside class="widget-sidebar">Widget</aside>
            <div id="social-share">Share buttons</div>
            <article>
                <h1>Article Title</h1>
                <p>This is the actual content we want.</p>
            </article>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        
        mock_request.return_value.get_root_url.return_value = "http://example.com"
        mock_request.return_value.build_url_path.return_value = ""
        
        processor = DocumentProcessor(mock_request, Path('/tmp/test'))
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        with patch.object(processor.request, 'absolute_source', return_value='http://example.com'):
            text = processor.save_text(Path('/tmp/test_filter'), processor.request)
        
        # All UI elements should be filtered
        self.assertNotIn('Top Nav', text)
        self.assertNotIn('Home > Page', text)
        self.assertNotIn('Widget', text)
        self.assertNotIn('Share buttons', text)
        self.assertNotIn('Footer content', text)
        
        # Main content should remain
        self.assertIn('Article Title', text)
        self.assertIn('This is the actual content we want', text)
    
    @patch('scrapyer.docuproc.HttpRequest')
    def test_form_and_button_elements_filtered(self, mock_request):
        """Test that form and button elements are removed"""
        html = """
        <html>
        <body>
            <article>
                <p>Content before form</p>
                <form>
                    <input type="text" placeholder="Search...">
                    <button>Search</button>
                </form>
                <button>Click me</button>
                <p>Content after form</p>
            </article>
        </body>
        </html>
        """
        
        mock_request.return_value.get_root_url.return_value = "http://example.com"
        mock_request.return_value.build_url_path.return_value = ""
        
        processor = DocumentProcessor(mock_request, Path('/tmp/test'))
        processor.dom = BeautifulSoup(html, 'html.parser')
        
        with patch.object(processor.request, 'absolute_source', return_value='http://example.com'):
            text = processor.save_text(Path('/tmp/test_filter'), processor.request)
        
        # Form and button text should be filtered
        self.assertNotIn('Search...', text)
        self.assertNotIn('Search', text)
        self.assertNotIn('Click me', text)
        
        # Main content should remain
        self.assertIn('Content before form', text)
        self.assertIn('Content after form', text)


if __name__ == '__main__':
    unittest.main()
