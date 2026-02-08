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

### SSL/TLS Configuration

Scrapyer supports custom SSL/TLS configuration for HTTPS connections, including:

- **SSL certificate verification control** - Enable or disable certificate verification (default: enabled)
- **Custom SSL contexts** - Provide your own SSL context for advanced use cases
- **Self-signed certificates** - Work with development environments using self-signed certificates
- **Custom CA bundles** - Use custom certificate authority bundles for internal/corporate certificates
- **Client certificate authentication** - Support for mutual TLS authentication

**📖 For detailed SSL configuration examples and usage, see [SSL_USAGE.md](SSL_USAGE.md)**

## Features

- **Web page archiving** - Download and save complete web pages with all assets
- **SSL/TLS support** - Flexible SSL configuration for secure connections
- **Retry logic** - Automatic retry with configurable attempts for transient network failures
- **Timeout handling** - Comprehensive timeout and error handling for robust scraping
- **Plain text extraction** - Extract clean text content from HTML documents

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