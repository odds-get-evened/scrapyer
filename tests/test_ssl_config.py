"""
Tests for SSL context configuration in HttpRequest
"""

import ssl
import unittest
from scrapyer.httprequest import HttpRequest


class TestSSLConfiguration(unittest.TestCase):
    """Test SSL/TLS configuration options"""
    
    def test_default_ssl_verification_enabled(self):
        """Test that SSL verification is enabled by default"""
        req = HttpRequest('https://example.com')
        self.assertTrue(req.verify_ssl)
        self.assertIsNone(req.ssl_context)
    
    def test_ssl_verification_can_be_disabled(self):
        """Test that SSL verification can be disabled"""
        req = HttpRequest('https://example.com', verify_ssl=False)
        self.assertFalse(req.verify_ssl)
        self.assertIsNone(req.ssl_context)
    
    def test_custom_ssl_context_accepted(self):
        """Test that custom SSL context can be provided"""
        custom_context = ssl.create_default_context()
        req = HttpRequest('https://example.com', ssl_context=custom_context)
        self.assertIs(req.ssl_context, custom_context)
    
    def test_get_ssl_context_returns_custom_when_provided(self):
        """Test that _get_ssl_context returns custom context when provided"""
        custom_context = ssl.create_default_context()
        req = HttpRequest('https://example.com', ssl_context=custom_context)
        result = req._get_ssl_context()
        self.assertIs(result, custom_context)
    
    def test_get_ssl_context_creates_default_with_verification(self):
        """Test that _get_ssl_context creates default context with verification"""
        req = HttpRequest('https://example.com', verify_ssl=True)
        context = req._get_ssl_context()
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
    
    def test_get_ssl_context_disables_verification_when_requested(self):
        """Test that _get_ssl_context disables verification when verify_ssl=False"""
        req = HttpRequest('https://example.com', verify_ssl=False)
        context = req._get_ssl_context()
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertFalse(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)
    
    def test_custom_context_takes_precedence_over_verify_ssl(self):
        """Test that custom ssl_context takes precedence over verify_ssl parameter"""
        # Create a custom context with verification enabled
        custom_context = ssl.create_default_context()
        custom_context.check_hostname = True
        custom_context.verify_mode = ssl.CERT_REQUIRED
        
        # Pass verify_ssl=False but also provide custom context
        req = HttpRequest('https://example.com', verify_ssl=False, ssl_context=custom_context)
        result = req._get_ssl_context()
        
        # Custom context should be returned, not a new context based on verify_ssl
        self.assertIs(result, custom_context)
        # Verify the returned context still has verification enabled
        self.assertTrue(result.check_hostname)
        self.assertEqual(result.verify_mode, ssl.CERT_REQUIRED)
    
    def test_timeout_parameter_still_works(self):
        """Test that timeout parameter works with SSL options"""
        req = HttpRequest('https://example.com', time_out=60, verify_ssl=False)
        self.assertEqual(req.timeout, 60)
        self.assertFalse(req.verify_ssl)
    
    def test_http_connections_not_affected(self):
        """Test that HTTP (non-SSL) connections are not affected by SSL params"""
        req = HttpRequest('http://example.com', verify_ssl=False)
        # HTTP connections should work regardless of SSL parameters
        self.assertFalse(req.verify_ssl)
        self.assertEqual(req.url.scheme, 'http')
    
    def test_ssl_context_with_custom_ca_bundle(self):
        """Test creating SSL context with custom CA bundle (simulated)"""
        # Create a context that could load a custom CA bundle
        context = ssl.create_default_context()
        # In real usage, would call: context.load_verify_locations('/path/to/ca.pem')
        
        req = HttpRequest('https://internal.example.com', ssl_context=context)
        result = req._get_ssl_context()
        self.assertIsInstance(result, ssl.SSLContext)


class TestSSLIntegration(unittest.TestCase):
    """Test SSL configuration integration with other components"""
    
    def test_ssl_settings_stored_in_request_object(self):
        """Test that SSL settings are properly stored in request object"""
        custom_context = ssl.create_default_context()
        req = HttpRequest('https://example.com', 
                         time_out=45, 
                         verify_ssl=False, 
                         ssl_context=custom_context)
        
        self.assertEqual(req.timeout, 45)
        self.assertFalse(req.verify_ssl)
        self.assertIs(req.ssl_context, custom_context)


if __name__ == '__main__':
    unittest.main()
