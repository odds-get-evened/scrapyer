import sys
import ssl
import argparse
from pathlib import Path

from scrapyer.docuproc import DocumentProcessor
from scrapyer.httprequest import HttpRequest


def boot_up():
    parser = argparse.ArgumentParser(
        description='Scrapyer - A web page archiver with NLP capabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage
  scrapyer http://example.com /path/to/save

  # Disable SSL verification (for self-signed certificates)
  scrapyer https://localhost:8443 /path/to/save --no-verify-ssl

  # Use custom SSL certificate
  scrapyer https://example.com /path/to/save --ssl-cert /path/to/cert.pem
        '''
    )
    
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('save_path', help='Directory path to save scraped content')
    parser.add_argument('--timeout', type=int, default=30, 
                        help='Request timeout in seconds (default: 30)')
    parser.add_argument('--no-verify-ssl', action='store_true',
                        help='Disable SSL certificate verification (useful for self-signed certificates)')
    parser.add_argument('--ssl-cert', type=str, metavar='PATH',
                        help='Path to SSL certificate file for custom CA or self-signed certificates')
    
    try:
        args = parser.parse_args()
        
        print(f"URL: {args.url}")
        save_path = Path(args.save_path)
        print(f"Save path: {save_path}")
        
        # Configure SSL settings
        ssl_context = None
        verify_ssl = not args.no_verify_ssl
        
        if args.ssl_cert:
            # Create SSL context with custom certificate
            print(f"Using SSL certificate: {args.ssl_cert}")
            ssl_context = ssl.create_default_context(cafile=args.ssl_cert)
            verify_ssl = True  # When using custom cert, we want verification enabled
        
        if args.no_verify_ssl:
            print("⚠️  Warning: SSL verification disabled!")
        
        # Create HTTP request with SSL configuration
        request = HttpRequest(
            args.url, 
            time_out=args.timeout,
            verify_ssl=verify_ssl,
            ssl_context=ssl_context
        )

        '''
        process content
        '''
        doc = DocumentProcessor(request, save_path)
        doc.start()
    except SystemExit:
        # argparse raises SystemExit on --help or errors
        raise
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
