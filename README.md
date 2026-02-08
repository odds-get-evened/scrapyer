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

Scrapyer now supports custom SSL/TLS configuration for HTTPS connections:

```python
from scrapyer.httprequest import HttpRequest
from scrapyer.docuproc import DocumentProcessor
from pathlib import Path
import ssl

# Default: SSL verification enabled (recommended)
request = HttpRequest("https://example.com")

# Disable SSL verification (development/testing only)
request = HttpRequest("https://self-signed.example.com", verify_ssl=False)

# Custom SSL context (advanced)
context = ssl.create_default_context()
context.load_verify_locations('/path/to/ca-bundle.crt')
request = HttpRequest("https://example.com", ssl_context=context)

# Process the page
doc = DocumentProcessor(request, Path("/save/path"))
doc.start()
```

For detailed SSL configuration examples, see [SSL_USAGE.md](SSL_USAGE.md).

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