#!/usr/bin/env python3
"""
Example: Using scrapyer with different SSL configurations
"""

import ssl
import sys
from pathlib import Path
from scrapyer.httprequest import HttpRequest
from scrapyer.docuproc import DocumentProcessor


def example_default_ssl():
    """Example 1: Default SSL verification (recommended for production)"""
    print("=" * 60)
    print("Example 1: Default SSL Verification")
    print("=" * 60)
    
    url = "https://httpbin.org/html"
    save_path = Path("/tmp/scrapyer_example_default")
    
    # Default behavior - SSL verification enabled
    request = HttpRequest(url)
    print(f"URL: {url}")
    print(f"SSL Verification: {request.verify_ssl}")
    print(f"Timeout: {request.timeout}s")
    print()
    
    # Note: Uncomment to actually run the scraper
    # doc = DocumentProcessor(request, save_path)
    # doc.start()
    

def example_no_ssl_verification():
    """Example 2: Disable SSL verification (development only)"""
    print("=" * 60)
    print("Example 2: Disable SSL Verification (Development Only)")
    print("=" * 60)
    
    url = "https://self-signed.badssl.com/"
    save_path = Path("/tmp/scrapyer_example_no_verify")
    
    # Disable SSL verification for self-signed certificates
    request = HttpRequest(url, verify_ssl=False)
    print(f"URL: {url}")
    print(f"SSL Verification: {request.verify_ssl}")
    print(f"Timeout: {request.timeout}s")
    print("⚠️  Warning: SSL verification disabled!")
    print()
    
    # Note: Uncomment to actually run the scraper
    # doc = DocumentProcessor(request, save_path)
    # doc.start()


def example_custom_ssl_context():
    """Example 3: Custom SSL context with specific settings"""
    print("=" * 60)
    print("Example 3: Custom SSL Context")
    print("=" * 60)
    
    url = "https://httpbin.org/html"
    save_path = Path("/tmp/scrapyer_example_custom")
    
    # Create custom SSL context
    context = ssl.create_default_context()
    
    # Optionally configure the context
    # context.minimum_version = ssl.TLSVersion.TLSv1_2
    # context.load_verify_locations('/path/to/ca-bundle.crt')
    
    request = HttpRequest(url, ssl_context=context)
    print(f"URL: {url}")
    print(f"SSL Context: Custom (TLS 1.2+)")
    print(f"Timeout: {request.timeout}s")
    print()
    
    # Note: Uncomment to actually run the scraper
    # doc = DocumentProcessor(request, save_path)
    # doc.start()


def example_client_certificate():
    """Example 4: Client certificate authentication"""
    print("=" * 60)
    print("Example 4: Client Certificate Authentication")
    print("=" * 60)
    
    url = "https://client.badssl.com/"
    save_path = Path("/tmp/scrapyer_example_client_cert")
    
    # Create context with client certificate
    # Note: You would need actual certificate files for this to work
    context = ssl.create_default_context()
    
    # Uncomment and provide actual certificate paths
    # context.load_cert_chain(
    #     certfile='/path/to/client.crt',
    #     keyfile='/path/to/client.key'
    # )
    
    request = HttpRequest(url, ssl_context=context)
    print(f"URL: {url}")
    print(f"SSL Context: Custom with client certificate")
    print(f"Timeout: {request.timeout}s")
    print("Note: This example requires actual certificate files")
    print()


def example_custom_ca_bundle():
    """Example 5: Custom CA bundle for internal certificates"""
    print("=" * 60)
    print("Example 5: Custom CA Bundle")
    print("=" * 60)
    
    url = "https://internal.company.com"
    save_path = Path("/tmp/scrapyer_example_ca_bundle")
    
    # Create context with custom CA bundle
    # Note: You would need an actual CA bundle file for this to work
    try:
        # Uncomment and provide actual CA bundle path
        # context = ssl.create_default_context(cafile='/path/to/ca-bundle.pem')
        context = ssl.create_default_context()
        
        request = HttpRequest(url, ssl_context=context)
        print(f"URL: {url}")
        print(f"SSL Context: Custom CA bundle")
        print(f"Timeout: {request.timeout}s")
        print("Note: This example requires an actual CA bundle file")
        print()
    except FileNotFoundError:
        print("CA bundle file not found (expected for this example)")
        print()


def main():
    """Run all examples"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Scrapyer SSL Configuration Examples              ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print("These examples demonstrate different SSL configurations.")
    print("Note: The actual scraping code is commented out.")
    print()
    
    try:
        example_default_ssl()
        example_no_ssl_verification()
        example_custom_ssl_context()
        example_client_certificate()
        example_custom_ca_bundle()
        
        print("=" * 60)
        print("All examples completed!")
        print("=" * 60)
        print()
        print("To actually run the scraper, uncomment the doc.start() lines")
        print("in each example function.")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
