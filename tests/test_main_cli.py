"""
Tests for CLI argument parsing in main.py
"""

import unittest
import sys
import ssl
from unittest.mock import patch, MagicMock
from io import StringIO
from scrapyer import main


class TestCLIArgumentParsing(unittest.TestCase):
    """Test command-line argument parsing"""
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_basic_arguments(self, mock_http_request, mock_doc_processor):
        """Test basic URL and save path arguments"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify HttpRequest was called with correct arguments
        mock_http_request.assert_called_once()
        call_args = mock_http_request.call_args
        self.assertEqual(call_args[0][0], 'http://example.com')
        self.assertEqual(call_args[1]['time_out'], 30)  # default timeout
        self.assertTrue(call_args[1]['verify_ssl'])  # default verify_ssl
        self.assertIsNone(call_args[1]['ssl_context'])  # default no custom context
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_no_verify_ssl_flag(self, mock_http_request, mock_doc_processor):
        """Test --no-verify-ssl flag disables SSL verification"""
        test_args = ['scrapyer', 'https://example.com', '/tmp/test', '--no-verify-ssl']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify HttpRequest was called with verify_ssl=False
        mock_http_request.assert_called_once()
        call_args = mock_http_request.call_args
        self.assertFalse(call_args[1]['verify_ssl'])
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_custom_timeout(self, mock_http_request, mock_doc_processor):
        """Test custom timeout argument"""
        test_args = ['scrapyer', 'http://example.com', '/tmp/test', '--timeout', '60']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify HttpRequest was called with custom timeout
        mock_http_request.assert_called_once()
        call_args = mock_http_request.call_args
        self.assertEqual(call_args[1]['time_out'], 60)
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    @patch('ssl.create_default_context')
    def test_ssl_cert_argument(self, mock_ssl_create, mock_http_request, mock_doc_processor):
        """Test --ssl-cert argument creates SSL context with certificate"""
        mock_context = MagicMock(spec=ssl.SSLContext)
        mock_ssl_create.return_value = mock_context
        
        test_args = ['scrapyer', 'https://example.com', '/tmp/test', '--ssl-cert', '/tmp/cert.pem']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
        
        # Verify ssl.create_default_context was called with cafile
        mock_ssl_create.assert_called_once_with(cafile='/tmp/cert.pem')
        
        # Verify HttpRequest was called with the SSL context
        mock_http_request.assert_called_once()
        call_args = mock_http_request.call_args
        self.assertEqual(call_args[1]['ssl_context'], mock_context)
        self.assertTrue(call_args[1]['verify_ssl'])  # Should be True when using custom cert
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_combined_arguments(self, mock_http_request, mock_doc_processor):
        """Test combining multiple arguments"""
        test_args = [
            'scrapyer', 
            'https://example.com', 
            '/tmp/test',
            '--timeout', '45',
            '--no-verify-ssl'
        ]
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
            
        # Verify all arguments were processed correctly
        mock_http_request.assert_called_once()
        call_args = mock_http_request.call_args
        self.assertEqual(call_args[1]['time_out'], 45)
        self.assertFalse(call_args[1]['verify_ssl'])
    
    def test_help_flag(self):
        """Test that --help flag displays help message"""
        test_args = ['scrapyer', '--help']
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    main.boot_up()
                    output = mock_stdout.getvalue()
                    self.assertIn('scrapyer', output.lower())
                    self.assertIn('--no-verify-ssl', output)
                    self.assertIn('--ssl-cert', output)
            
            # Help should exit with code 0
            self.assertEqual(cm.exception.code, 0)
    
    def test_missing_required_arguments(self):
        """Test that missing required arguments raises SystemExit"""
        test_args = ['scrapyer']  # Missing URL and save_path
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stderr', new_callable=StringIO):
                    main.boot_up()
            
            # Should exit with error code
            self.assertNotEqual(cm.exception.code, 0)


class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration with HttpRequest and DocumentProcessor"""
    
    @patch('scrapyer.main.DocumentProcessor')
    @patch('scrapyer.main.HttpRequest')
    def test_document_processor_receives_configured_request(self, mock_http_request, mock_doc_processor):
        """Test that DocumentProcessor receives properly configured HttpRequest"""
        mock_request_instance = MagicMock()
        mock_http_request.return_value = mock_request_instance
        
        test_args = ['scrapyer', 'http://example.com', '/tmp/test']
        
        with patch.object(sys, 'argv', test_args):
            main.boot_up()
        
        # Verify DocumentProcessor was initialized with the request instance
        mock_doc_processor.assert_called_once()
        call_args = mock_doc_processor.call_args
        self.assertEqual(call_args[0][0], mock_request_instance)
        
        # Verify DocumentProcessor.start() was called
        mock_doc_processor.return_value.start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
