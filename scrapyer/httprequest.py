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
    safely encode query string values
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
    def __init__(self, url: str, time_out: int = 30, verify_ssl: bool = True, ssl_context: ssl.SSLContext = None):
        self.url: ParseResult = None
        self.timeout: int = time_out
        self.verify_ssl: bool = verify_ssl
        self.ssl_context: ssl.SSLContext = ssl_context
        self.connection: HTTPConnection | HTTPSConnection = None
        self.port: int = HttpProps.PORT
        self.parse(url)
        self.body: str = None
        self.headers: dict = {}

    def parse(self, url: str) -> None:
        p = urlparse(url)
        self.url = p

        self.determine_port()
        self.set_connection()

    def determine_port(self) -> None:
        if self.url.scheme == HttpsProps.SCHEME:
            self.port = HttpsProps.PORT
        else:
            self.port = HttpProps.PORT

    def set_connection(self) -> None:
        host_name = socket.gethostbyname(socket.gethostname())

        if self.port == HttpsProps.PORT:
            # Create or use custom SSL context
            context = self._get_ssl_context()
            self.connection = HTTPSConnection(self.url.netloc, timeout=self.timeout, context=context)
        else:
            self.connection = HTTPConnection(self.url.netloc, timeout=self.timeout)

    def _get_ssl_context(self) -> ssl.SSLContext:
        """
        Get SSL context for HTTPS connections.
        
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
        self.headers[n] = v

    def get(self) -> HTTPResponse:
        random_ua: str = secrets.choice(REQUEST_USER_AGENTS)

        # randomize the User-Agent name
        '''
        rand_hash = hex(crc32(datetime.now().isoformat().encode('utf8')))[2:]
        self.add_header('User-Agent',f"special-agent-{rand_hash}-browser/2.0")

        self.add_header('Host', random_host)
        '''
        self.add_header('User-Agent', random_ua)
        self.add_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.add_header('Pragma', 'no-cache')
        self.add_header('Expires', '0')
        self.add_header('Accept', '*/*')
        self.add_header('Accept-Language', '*/*')
        self.add_header('Accept-Encoding', '*/*')
        self.add_header('Connection', 'keep-alive')
        
        # Recreate connection to avoid "Request-sent" error on retry
        self.set_connection()
        
        self.connection.request("GET", self.build_url_path(), body=self.body, headers=self.headers)

        return self.connection.getresponse()

    def build_url_path(self, path_only: bool = False) -> str:
        """
        rebuild only the path from the original full URL

        Returns:
            string including path, parameters, query, and fragments
        """

        p = ""

        p += self.url.path

        if path_only is False:
            if self.url.params != "":
                p += f":{self.url.params}"

            if self.url.query != "":
                # break it apart
                '''
                because this is an untreated string for URLs
                we need to walk through items of query, and urlencode
                each value
                '''
                p += "?" + re.sub(r"([^=]+)(=([^&#]*))?", safe_queryize, self.url.query)

            if self.url.fragment != "":
                p += f"#{self.url.fragment}"

        return p

    def absolute_source(self, p: str) -> str:
        r = ""

        if p.startswith("/"):
            # root path
            r = self.get_root_url() + p
        elif re.match(r'^https?://', p):
            r = p
        else:
            # relative path
            r = self.get_relative_url() + p

        return r

    def get_relative_url(self):
        return self.get_root_url() + self.build_url_path(path_only=True)

    def get_root_url(self) -> str:
        return self.url.scheme + "://" + self.url.netloc
