import sys
import ssl
import argparse
from pathlib import Path

from scrapyer.docuproc import DocumentProcessor
from scrapyer.httprequest import HttpRequest


def boot_up():
    """
    Main entry point for the Scrapyer content extraction tool.
    Parses command-line arguments and initiates content extraction focused on
    main HTML content (text and media) while excluding scripts, stylesheets, and other non-essential elements.
    """
    parser = argparse.ArgumentParser(
        description='Scrapyer - A web page content extractor focused on main text and media',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage - extract main content from a page
  scrapyer http://example.com /path/to/save

  # Disable SSL verification (for self-signed certificates)
  scrapyer https://localhost:8443 /path/to/save --no-verify-ssl

  # Use custom SSL certificate
  scrapyer https://example.com /path/to/save --ssl-cert /path/to/cert.pem

  # Extract only specific media types
  scrapyer http://example.com /path/to/save --media-types images,videos
        '''
    )
    
    # Required arguments
    parser.add_argument('url', help='URL of the web page to extract content from')
    parser.add_argument('save_path', help='Directory path to save extracted content')
    
    # Optional arguments
    parser.add_argument('--timeout', type=int, default=30, 
                        help='Request timeout in seconds (default: 30)')
    parser.add_argument('--no-verify-ssl', action='store_true',
                        help='Disable SSL certificate verification (useful for self-signed certificates)')
    parser.add_argument('--ssl-cert', type=str, metavar='PATH',
                        help='Path to SSL certificate file for custom CA or self-signed certificates')
    parser.add_argument('--media-types', type=str, default='images,videos,audio',
                        help='Comma-separated list of media types to extract: images, videos, audio (default: all)')
    parser.add_argument('--text-only', action='store_true',
                        help='Extract only text content, skip all media downloads (images, videos, audio)')
    parser.add_argument('--strip-html', action='store_true', default=True,
                        help='Strip all HTML tags and extract plain text (enabled by default)')
    parser.add_argument('--preserve-structure', action='store_true',
                        help='Preserve basic document structure (headings, paragraphs) in output')
    parser.add_argument('--crawl', action='store_true',
                        help='Crawl and extract content from all linked pages found on the initial URL')
    parser.add_argument('--crawl-limit', type=int, metavar='N',
                        help='Maximum number of pages to crawl (default: unlimited)')
    
    try:
        args = parser.parse_args()
        
        # Display configuration
        print(f"🔗 URL: {args.url}")
        save_path = Path(args.save_path)
        print(f"💾 Save path: {save_path}")
        
        # Configure SSL settings
        ssl_context = None
        verify_ssl = not args.no_verify_ssl
        
        if args.ssl_cert:
            # Create SSL context with custom certificate for HTTPS connections
            print(f"🔐 Using SSL certificate: {args.ssl_cert}")
            ssl_context = ssl.create_default_context(cafile=args.ssl_cert)
            if not args.no_verify_ssl:
                verify_ssl = True
        
        if args.no_verify_ssl:
            print("⚠️  Warning: SSL verification disabled!")
        
        # Parse media types configuration
        if args.text_only:
            media_types = []
            print("📝 Text-only mode: Media downloads disabled")
        else:
            media_types = [mt.strip().lower() for mt in args.media_types.split(',')]
            print(f"📁 Extracting media types: {', '.join(media_types)}")
        
        # Display content extraction mode
        if args.strip_html:
            mode = "plain text" if not args.preserve_structure else "structured text"
            print(f"📄 Content extraction mode: {mode}")
        
        # Create HTTP request with SSL configuration
        # This will fetch ONLY the HTML page content, ignoring external resources
        request = HttpRequest(
            args.url, 
            time_out=args.timeout,
            verify_ssl=verify_ssl,
            ssl_context=ssl_context,
            fetch_html_only=True  # NEW: Only fetch HTML content, skip scripts/stylesheets
        )

        # Process the HTML content and extract main text + media
        # This will:
        # 1. Parse the HTML
        # 2. Identify and extract main content blocks (article, main, content divs)
        # 3. Strip out <script>, <style>, <nav>, <footer>, and other non-content elements
        # 4. Extract text content
        # 5. Identify and download media (images, videos, audio)
        # 6. Save cleaned content and media to the specified path
        doc = DocumentProcessor(
            request, 
            save_path,
            strip_html=args.strip_html,
            preserve_structure=args.preserve_structure,
            media_types=media_types,
            crawl=args.crawl,
            crawl_limit=args.crawl_limit,
            timeout=args.timeout,
            verify_ssl=verify_ssl,
            ssl_context=ssl_context
        )
        doc.start()
        
        print("✅ Content extraction completed successfully!")
        
    except SystemExit:
        # argparse raises SystemExit on --help or errors
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
