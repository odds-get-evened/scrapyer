# SSL Configuration Guide

Scrapyer now supports custom SSL/TLS configuration for HTTPS connections. This guide explains how to use these features both from the command line and programmatically.

## Command Line Usage

### Default Behavior (SSL Verification Enabled)

By default, scrapyer performs full SSL certificate verification:

```bash
scrapyer https://example.com /path/to/save
```

### Disable SSL Verification

For development/testing with self-signed certificates, use the `--no-verify-ssl` flag:

```bash
scrapyer https://localhost:8443 /path/to/save --no-verify-ssl
```

**⚠️ Warning:** Disabling SSL verification should only be used for development/testing. Never disable SSL verification in production as it makes your application vulnerable to man-in-the-middle attacks.

### Use Custom SSL Certificate

For self-signed certificates or custom CA bundles, use the `--ssl-cert` option:

```bash
# Use a self-signed certificate
scrapyer https://localhost:8443 /path/to/save --ssl-cert /path/to/self-signed.crt

# Use a custom CA bundle
scrapyer https://internal.company.com /path/to/save --ssl-cert /path/to/ca-bundle.pem
```

### Other Options

```bash
# Set custom timeout (in seconds)
scrapyer https://example.com /path/to/save --timeout 60

# Combine multiple options
scrapyer https://example.com /path/to/save --timeout 45 --ssl-cert /path/to/cert.pem

# View all available options
scrapyer --help
```

## Programmatic Usage

### Default Behavior (SSL Verification Enabled)

By default, scrapyer performs full SSL certificate verification:

```python
from scrapyer.httprequest import HttpRequest
from scrapyer.docuproc import DocumentProcessor
from pathlib import Path

# Default: SSL verification is enabled
url = "https://example.com"
request = HttpRequest(url)
doc = DocumentProcessor(request, Path("/save/path"))
doc.start()
```

### Disable SSL Verification

For development/testing with self-signed certificates or when you want to bypass SSL verification:

```python
from scrapyer.httprequest import HttpRequest

# Disable SSL certificate verification
request = HttpRequest("https://self-signed-cert-site.com", verify_ssl=False)
```

**⚠️ Warning:** Disabling SSL verification should only be used for development/testing. Never disable SSL verification in production as it makes your application vulnerable to man-in-the-middle attacks.

### Custom SSL Context

For advanced use cases, you can provide your own SSL context:

```python
import ssl
from scrapyer.httprequest import HttpRequest

# Create custom SSL context
context = ssl.create_default_context()

# Load custom CA bundle
context.load_verify_locations('/path/to/ca-bundle.crt')

# Or load client certificates
context.load_cert_chain(certfile='/path/to/client.crt', 
                        keyfile='/path/to/client.key')

# Use custom context
request = HttpRequest("https://example.com", ssl_context=context)
```

## Common Use Cases

### 1. Self-Signed Certificates (Development)

```python
from scrapyer.httprequest import HttpRequest

# Quick way: disable verification (not recommended for production)
request = HttpRequest("https://localhost:8443", verify_ssl=False)
```

### 2. Custom CA Bundle

```python
import ssl
from scrapyer.httprequest import HttpRequest

# Create context with custom CA bundle
context = ssl.create_default_context(cafile='/path/to/custom-ca-bundle.pem')
request = HttpRequest("https://internal-site.company.com", ssl_context=context)
```

### 3. Client Certificate Authentication

```python
import ssl
from scrapyer.httprequest import HttpRequest

# Create context and load client certificate
context = ssl.create_default_context()
context.load_cert_chain(
    certfile='/path/to/client.crt',
    keyfile='/path/to/client.key',
    password='certificate_password'  # optional
)

request = HttpRequest("https://api.example.com", ssl_context=context)
```

### 4. Specific TLS Version

```python
import ssl
from scrapyer.httprequest import HttpRequest

# Force TLS 1.2 or higher
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.minimum_version = ssl.TLSVersion.TLSv1_2

request = HttpRequest("https://example.com", ssl_context=context)
```

## Parameters

### HttpRequest Constructor

```python
HttpRequest(url, time_out=30, verify_ssl=True, ssl_context=None)
```

- **url** (str): The URL to request
- **time_out** (int): Timeout in seconds (default: 30)
- **verify_ssl** (bool): Enable/disable SSL certificate verification (default: True)
- **ssl_context** (ssl.SSLContext): Custom SSL context (default: None)

### DocumentProcessor

The `DocumentProcessor` automatically inherits SSL settings from the `HttpRequest` passed to it, so all downloaded resources (images, CSS, JavaScript) will use the same SSL configuration.

```python
from scrapyer.httprequest import HttpRequest
from scrapyer.docuproc import DocumentProcessor
from pathlib import Path

# Create request with custom SSL settings
request = HttpRequest("https://example.com", verify_ssl=False)

# DocumentProcessor will use the same SSL settings for all resources
doc = DocumentProcessor(request, Path("/save/path"))
doc.start()
```

## Security Best Practices

1. **Always verify SSL certificates in production** - Only disable verification for development/testing
2. **Use custom CA bundles** when working with internal/corporate certificates
3. **Keep certificates up to date** - Regularly update your CA bundle
4. **Use strong TLS versions** - Prefer TLS 1.2 or higher
5. **Protect private keys** - Never commit private keys to version control

## Troubleshooting

### SSL Certificate Verify Failed

```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solutions:**
1. Ensure system CA certificates are up to date
2. Provide a custom CA bundle with `ssl_context`
3. For development only: use `verify_ssl=False`

### SSL Handshake Timeout

```
TimeoutError: _ssl.c:1011: The handshake operation timed out
```

**Solutions:**
1. Increase timeout: `HttpRequest(url, time_out=60)`
2. Check network connectivity
3. Verify the server supports modern TLS versions

### Self-Signed Certificate Errors

For development with self-signed certificates, either:
1. Use `verify_ssl=False` (quick but insecure)
2. Add the self-signed certificate to a custom CA bundle (more secure)

```python
import ssl
from scrapyer.httprequest import HttpRequest

# Option 1: Disable verification (development only)
request = HttpRequest("https://localhost:8443", verify_ssl=False)

# Option 2: Add self-signed cert to context (better)
context = ssl.create_default_context()
context.load_verify_locations('/path/to/self-signed.crt')
request = HttpRequest("https://localhost:8443", ssl_context=context)
```
