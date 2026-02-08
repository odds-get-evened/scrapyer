# scrapyer

---

#### a web page archiver with NLP capabilities

## Installation

### Install from GitHub

You can install scrapyer directly from GitHub:

```shell
$ pip install git+https://github.com/odds-get-evened/scrapyer.git
```

This will install the base package with basic scraping capabilities.

### Install with NLP features

To include NLP capabilities, install with the `nlp` extra:

```shell
$ pip install "git+https://github.com/odds-get-evened/scrapyer.git#egg=scrapyer[nlp]"
```

### Install from source

```shell
$ git clone https://github.com/odds-get-evened/scrapyer.git
$ cd scrapyer
$ pip install .
# For NLP features:
$ pip install ".[nlp]"
```

## Usage

### Basic Usage

```shell
$ scrapyer "http://example.com/page?id=12345#yup" /some/place/to/store/files/
```

### Web Crawling

Scrapyer can crawl and extract content from multiple linked pages:

```shell
# Crawl all linked pages from the initial URL
$ scrapyer http://example.com /path/to/save --crawl

# Limit crawling to a specific number of pages
$ scrapyer http://example.com /path/to/save --crawl --crawl-limit 10
```

When crawling is enabled:
- Scrapyer extracts all links from each page
- Only links from the same domain are followed
- Each page's content is saved in its own subdirectory
- Visited URLs are tracked to avoid duplicates
- Crawling continues until the limit is reached or no more links are found

### SSL/TLS Configuration

Scrapyer supports custom SSL/TLS configuration for HTTPS connections, including:

- **SSL certificate verification control** - Enable or disable certificate verification (default: enabled)
- **Custom SSL contexts** - Provide your own SSL context for advanced use cases
- **Self-signed certificates** - Work with development environments using self-signed certificates
- **Custom CA bundles** - Use custom certificate authority bundles for internal/corporate certificates
- **Client certificate authentication** - Support for mutual TLS authentication

#### Command Line Options

```shell
# Disable SSL verification for self-signed certificates
$ scrapyer https://localhost:8443 /path/to/save --no-verify-ssl

# Use a custom SSL certificate
$ scrapyer https://example.com /path/to/save --ssl-cert /path/to/cert.pem

# Set custom timeout
$ scrapyer http://example.com /path/to/save --timeout 60

# Text-only mode - skip all media downloads (images, videos, audio)
$ scrapyer http://example.com /path/to/save --text-only

# Combine crawling with other options
$ scrapyer https://example.com /path/to/save --crawl --crawl-limit 5 --timeout 60 --no-verify-ssl

# Text-only mode with crawling
$ scrapyer http://example.com /path/to/save --crawl --text-only

# View all options
$ scrapyer --help
```

**📖 For detailed SSL configuration examples and usage, see [SSL_USAGE.md](SSL_USAGE.md)**

## Features

- **Web page archiving** - Download and save complete web pages with all assets
- **Web crawling** - Automatically discover and extract content from linked pages on the same domain
- **Crawl limiting** - Control the scope of crawling with configurable page limits
- **Text-only mode** - Extract only text content without downloading any media files (images, videos, audio)
- **Unique content filenames** - Each crawled page gets a unique content filename based on its URL, preventing overwrites
- **SSL/TLS support** - Flexible SSL configuration for secure connections
- **Retry logic** - Automatic retry with configurable attempts for transient network failures
- **Timeout handling** - Comprehensive timeout and error handling for robust scraping
- **Plain text extraction** - Extract clean text content from HTML documents
- **Organized output** - Each crawled page is saved in its own subdirectory with unique naming

## NLP Features

Scrapyer now includes lightweight natural language processing (NLP) capabilities using the MiniLM ONNX model for efficient query processing and intent classification.

### Setup

1. Install scrapyer with NLP dependencies (see Installation section above)

2. Download and set up the model:
```shell
$ python setup_model.py
```

3. The model will be automatically downloaded, converted to ONNX format, and saved in the `nlp/onnx/` directory.

### Usage

```python
from nlp.onnx_nlp_model import ONNXNLPModel

# Initialize the model
model = ONNXNLPModel()

# Process a query
result = model.predict("How do I scrape a web page?")

# Compute similarity between texts
similarity = model.get_similarity("scrape website", "extract web data")
```

### Requirements

- onnxruntime
- transformers
- numpy
- torch
- aiohttp

Install all requirements: `pip install -r requirements.txt` or `pip install ".[nlp]"`