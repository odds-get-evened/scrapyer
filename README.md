# scrapyer

---

#### a web page archiver with NLP capabilities

```shell
$ scrapyer "http://example.com/page?id=12345#yup" /some/place/to/store/files/
```

## NLP Features

Scrapyer now includes lightweight natural language processing (NLP) capabilities using the MiniLM ONNX model for efficient query processing and intent classification.

### Setup

1. Install dependencies and download the model:
```shell
$ python setup_model.py
```

2. The model will be automatically downloaded, converted to ONNX format, and saved in the `nlp/onnx/` directory.

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
- aiohttp
- numpy

Install all requirements: `pip install -r requirements.txt`