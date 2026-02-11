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

# Enable smart content quality filtering
$ scrapyer http://example.com /path/to/save --enable-quality-filter

# Quality filtering with custom threshold and heuristics only
$ scrapyer http://example.com /path/to/save --enable-quality-filter --quality-threshold 0.7 --no-nlp-quality

# Preserve document structure (headings, paragraphs)
$ scrapyer http://example.com /path/to/save --preserve-structure

# View all options
$ scrapyer --help
```

**📖 For detailed SSL configuration examples and usage, see [SSL_USAGE.md](SSL_USAGE.md)**

### Smart Content Quality Filtering

Scrapyer includes an intelligent content quality filtering system that helps distinguish informative prose content from UI elements, navigation menus, and other non-essential text.

#### How It Works

The quality filter uses multiple linguistic and structural signals to score content:

- **Sentence complexity** - Varied sentence lengths indicate natural prose
- **Vocabulary richness** - Type-Token Ratio (unique words / total words)
- **Information density** - Presence of numbers, dates, proper nouns, and technical terms
- **Research language indicators** - Patterns like "researchers found", "study shows", "according to"
- **Noise detection** - Penalizes navigation patterns, pagination, and menu-like text
- **NLP-based semantic analysis** (optional) - Uses the MiniLM ONNX model to compare content against quality prose templates

#### Command Line Usage

```shell
# Enable quality filtering with default settings
$ scrapyer http://example.com /path/to/save --enable-quality-filter

# Set a custom quality threshold (0-1 scale, default: 0.6)
$ scrapyer http://example.com /path/to/save --enable-quality-filter --quality-threshold 0.7

# Use heuristics only (disable NLP enhancement)
$ scrapyer http://example.com /path/to/save --enable-quality-filter --no-nlp-quality

# Combine with crawling for large-scale content extraction
$ scrapyer http://example.com /path/to/save --crawl --enable-quality-filter
```

#### When to Use Quality Filtering

Quality filtering is particularly useful when:
- Extracting content from news articles, blog posts, or research papers
- You want to filter out navigation menus, sidebars, and footer text
- Crawling multiple pages and only want informative content
- Processing content for text analysis or machine learning

**Note:** Quality filtering requires the base installation. NLP enhancement requires the `nlp` extras (see Installation section).

## Features

- **Web page archiving** - Download and save complete web pages with all assets
- **Web crawling** - Automatically discover and extract content from linked pages on the same domain
- **Crawl limiting** - Control the scope of crawling with configurable page limits
- **Smart content quality filtering** - Intelligent filtering to distinguish informative content from UI/navigation elements using linguistic and structural signals
- **Text-only mode** - Extract only text content without downloading any media files (images, videos, audio)
- **Unique content filenames** - Each crawled page gets a unique content filename based on its URL, preventing overwrites
- **SSL/TLS support** - Flexible SSL configuration for secure connections
- **Retry logic** - Automatic retry with configurable attempts for transient network failures
- **Timeout handling** - Comprehensive timeout and error handling for robust scraping
- **Plain text extraction** - Extract clean text content from HTML documents
- **Structured content preservation** - Optionally preserve document structure with headings and paragraphs
- **Organized output** - Each crawled page is saved in its own subdirectory with unique naming

## NLP Features

Scrapyer includes lightweight natural language processing (NLP) capabilities using the MiniLM ONNX model for efficient query processing, intent classification, and enhanced content quality filtering.

### Setup

1. Install scrapyer with NLP dependencies (see Installation section above)

2. Download and set up the model:
```shell
$ python setup_model.py
```

3. The model will be automatically downloaded, converted to ONNX format, and saved in the `nlp/onnx/` directory.

### Usage

#### Programmatic API

```python
from nlp.onnx_nlp_model import ONNXNLPModel

# Initialize the model
model = ONNXNLPModel()

# Process a query
result = model.predict("How do I scrape a web page?")

# Compute similarity between texts
similarity = model.get_similarity("scrape website", "extract web data")
```

#### Enhanced Quality Filtering

The NLP model can optionally enhance content quality filtering with semantic analysis:

```python
from scrapyer.quality_filter import NLPEnhancedQualityFilter

# Initialize with NLP enhancement
filter = NLPEnhancedQualityFilter(min_quality_score=0.6, use_nlp=True)

# Check if text is quality content
is_quality = filter.is_quality_content("Sample text from web page")

# Calculate detailed quality scores
score, details = filter.calculate_quality_score("Sample text")
print(f"Quality score: {score:.2f}")
print(f"Details: {details}")
```

When using the command-line tool, NLP enhancement is automatically enabled if the model is available (unless `--no-nlp-quality` is specified).

### Requirements

- onnxruntime
- transformers
- numpy
- torch
- aiohttp

Install all requirements: `pip install -r requirements.txt` or `pip install ".[nlp]"`