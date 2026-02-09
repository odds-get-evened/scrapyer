import secrets
import re
import socket
import ssl
from http.client import HTTPSConnection, HTTPConnection, HTTPResponse
from urllib.parse import urlparse, ParseResult, quote_plus

REQUEST_USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 7.1.1; Moto G (5S) Build/NPPS26.102-49-11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.91 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
    'Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18',
    'SpecialAgent/13.0 (NSA 66.6 Linux) Magickal/3.14 (KHTML, like Gecko) Version/13.0.0'
]

def safe_queryize(m):
    """
    Safely encode query string values for URL parameters.
    """
    if m.group() is not None:
        return m.group(1) + '=' + quote_plus(m.group(3))

class HttpProps:
    SCHEME = 'http'
    PORT = 80

class HttpsProps:
    SCHEME = 'https'
    PORT = 443

class HttpRequest:
    def __init__(self, url: str, time_out: int = 30, verify_ssl: bool = True, 
                 ssl_context: ssl.SSLContext = None, fetch_html_only: bool = False):
        """
        Initialize an HTTP/HTTPS request for fetching web content.
        
        Args:
            url: The URL to request
            time_out: Timeout in seconds (default: 30)
            verify_ssl: Enable/disable SSL certificate verification (default: True)
            ssl_context: Custom SSL context for HTTPS connections (default: None)
            fetch_html_only: If True, only fetch HTML content and reject other content types (default: False)
        """
        self.url: ParseResult = None
        self.timeout: int = time_out
        self.verify_ssl: bool = verify_ssl
        self.ssl_context: ssl.SSLContext = ssl_context
        self.fetch_html_only: bool = fetch_html_only  # NEW: flag to restrict to HTML only
        self.connection: HTTPConnection | HTTPSConnection = None
        self.port: int = HttpProps.PORT
        self.parse(url)
        self.body: str = None
        self.headers: dict = {}

    def parse(self, url: str) -> None:
        """Parse the URL and initialize the connection."""
        p = urlparse(url)
        self.url = p
        self.determine_port()
        self.set_connection()

    def determine_port(self) -> None:
        """Determine the port based on the URL scheme (HTTP or HTTPS)."""
        if self.url.scheme == HttpsProps.SCHEME:
            self.port = HttpsProps.PORT
        else:
            self.port = HttpProps.PORT

    def set_connection(self) -> None:
        """Create HTTP or HTTPS connection object based on URL scheme."""
        host_name = socket.gethostbyname(socket.gethostname())

        if self.port == HttpsProps.PORT:
            # Create or use custom SSL context for secure connections
            context = self._get_ssl_context()
            self.connection = HTTPSConnection(self.url.netloc, timeout=self.timeout, context=context)
        else:
            self.connection = HTTPConnection(self.url.netloc, timeout=self.timeout)

    def _get_ssl_context(self) -> ssl.SSLContext:
        """
        Get SSL context for HTTPS connections with proper verification settings.
        
        Returns:
            SSLContext configured based on verify_ssl setting or custom context
        """
        if self.ssl_context is not None:
            # Use user-provided custom SSL context
            return self.ssl_context
        
        # Create default context
        context = ssl.create_default_context()
        
        if not self.verify_ssl:
            # Disable certificate verification (useful for development/testing)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        return context

    def add_header(self, n: str, v: str) -> None:
        """Add a custom header to the HTTP request."""
        self.headers[n] = v

    def get(self) -> HTTPResponse:
        """
        Execute the HTTP GET request and return the response.
        When fetch_html_only is True, validates that response is HTML content.
        
        Returns:
            HTTPResponse object containing the server's response
            
        Raises:
            ValueError: If fetch_html_only is True and response is not HTML
        """
        random_ua: str = secrets.choice(REQUEST_USER_AGENTS)

        # Set request headers to simulate a real browser
        self.add_header('User-Agent', random_ua)
        self.add_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.add_header('Pragma', 'no-cache')
        self.add_header('Expires', '0')
        
        # When fetching HTML only, specify acceptable content types
        if self.fetch_html_only:
            self.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        else:
            self.add_header('Accept', '*/*')
            
        self.add_header('Accept-Language', 'en-US,en;q=0.9')
        # Don't request compressed encoding as http.client doesn't auto-decompress
        # This prevents receiving gzip/deflate/br encoded content that would be garbled
        self.add_header('Accept-Encoding', 'identity')
        self.add_header('Connection', 'keep-alive')
        
        # Recreate connection to avoid "Request-sent" error on retry
        self.set_connection()
        
        self.connection.request("GET", self.build_url_path(), body=self.body, headers=self.headers)
        response = self.connection.getresponse()
        
        # Validate content type if HTML-only mode is enabled
        if self.fetch_html_only:
            content_type = response.getheader('Content-Type', '').lower()
            # Accept HTML, XHTML, and XML content types (including RSS/Atom feeds)
            if not ('text/html' in content_type or 'application/xhtml' in content_type or 
                    'xml' in content_type):
                raise ValueError(
                    f"Expected HTML content but received '{content_type}'. "
                    f"This URL does not point to a web page."
                )
        
        return response

    def build_url_path(self, path_only: bool = False) -> str:
        """
        Rebuild only the path portion from the original full URL.
        
        Args:
            path_only: If True, only return the path without query params or fragments
            
        Returns:
            String including path, parameters, query, and fragments
        """
        p = ""
        p += self.url.path

        if path_only is False:
            if self.url.params != "":
                p += f":{self.url.params}"

            if self.url.query != "":
                # Safely encode query string values to prevent injection
                p += "?" + re.sub(r"([^=]+)(=([^&#]*))?", safe_queryize, self.url.query)

            if self.url.fragment != "":
                p += f"#{self.url.fragment}"

        return p

    def absolute_source(self, p: str) -> str:
        """
        Convert a relative or root-relative path to an absolute URL.
        
        Args:
            p: Path to convert (can be relative, root-relative, or already absolute)
            
        Returns:
            Absolute URL string
        """
        r = ""

        if p.startswith("/"):
            # Root path - combine with domain
            r = self.get_root_url() + p
        elif re.match(r'^https?://', p):
            # Already absolute URL
            r = p
        else:
            # Relative path - combine with current page path
            r = self.get_relative_url() + p

        return r

    def get_relative_url(self):
        """Get the base URL including the current path (without filename)."""
        return self.get_root_url() + self.build_url_path(path_only=True)

    def get_root_url(self) -> str:
        """Get the root URL (scheme + domain)."""
        return self.url.scheme + "://" + self.url.netloc
