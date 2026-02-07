"""
ONNX NLP Model Handler

This module provides functionality to load and run NLP queries using the MiniLM ONNX model.
Compatible with 'microsoft/MiniLM-L6-H384-uncased' tokenizer for query tokenization.
Supports natural language query processing to predict intents and output class probabilities.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading

# Lazy imports to avoid ImportError during package installation
np = None
ort = None
AutoTokenizer = None
_import_lock = threading.Lock()


class ONNXNLPModel:
    """
    ONNX-based NLP model handler for natural language query processing.
    
    This class handles loading the ONNX model and tokenizer, and provides
    methods for processing natural language queries to predict intents.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        tokenizer_name: str = "microsoft/MiniLM-L6-H384-uncased"
    ):
        """
        Initialize the ONNX NLP Model handler.
        
        Args:
            model_path: Path to the ONNX model file. If None, uses default path.
            tokenizer_name: Name or path of the tokenizer to use.
        """
        # Import dependencies when actually using the model
        self._ensure_dependencies()
        
        if model_path is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent
            model_path = base_dir / "onnx" / "minilm-l6-h384-uncased.onnx"
        
        self.model_path = Path(model_path)
        self.tokenizer_name = tokenizer_name
        
        # Initialize session and tokenizer as None
        self.session = None
        self.tokenizer = None
        
        # Load model and tokenizer
        self._load_model()
        self._load_tokenizer()
    
    def _ensure_dependencies(self):
        """Ensure required dependencies are imported."""
        global np, ort, AutoTokenizer
        
        # Thread-safe lazy import
        with _import_lock:
            if np is None or ort is None or AutoTokenizer is None:
                try:
                    import numpy as _np
                    import onnxruntime as _ort
                    from transformers import AutoTokenizer as _AutoTokenizer
                    np = _np
                    ort = _ort
                    AutoTokenizer = _AutoTokenizer
                except ImportError as e:
                    raise ImportError(
                        f"Required packages not installed: {e}. "
                        f"Please install NLP dependencies with: pip install scrapyer[nlp]"
                    )
    
    def _load_model(self):
        """Load the ONNX model."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found at {self.model_path}. "
                f"Please run 'python setup_model.py' to download and convert the model."
            )
        
        try:
            # Create ONNX Runtime session
            self.session = ort.InferenceSession(
                str(self.model_path),
                providers=['CPUExecutionProvider']
            )
            print(f"Successfully loaded ONNX model from {self.model_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {e}")
    
    def _load_tokenizer(self):
        """Load the tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
            print(f"Successfully loaded tokenizer: {self.tokenizer_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to load tokenizer: {e}")
    
    def tokenize(self, text: str, max_length: int = 128) -> Dict[str, np.ndarray]:
        """
        Tokenize input text.
        
        Args:
            text: Input text to tokenize.
            max_length: Maximum sequence length.
            
        Returns:
            Dictionary containing tokenized inputs.
        """
        if self.tokenizer is None:
            raise RuntimeError("Tokenizer not loaded")
        
        # Tokenize the input text
        encoded = self.tokenizer(
            text,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='np'
        )
        
        # Convert to int64 for ONNX
        return {
            'input_ids': encoded['input_ids'].astype(np.int64),
            'attention_mask': encoded['attention_mask'].astype(np.int64)
        }
    
    def predict(self, text: str, max_length: int = 128) -> Dict[str, Any]:
        """
        Process a natural language query and predict intent.
        
        Args:
            text: Input query text.
            max_length: Maximum sequence length.
            
        Returns:
            Dictionary containing predictions and probabilities.
        """
        if self.session is None:
            raise RuntimeError("Model not loaded")
        
        # Tokenize input
        inputs = self.tokenize(text, max_length)
        
        # Prepare ONNX inputs
        onnx_inputs = {
            self.session.get_inputs()[0].name: inputs['input_ids'],
            self.session.get_inputs()[1].name: inputs['attention_mask']
        }
        
        # Run inference
        outputs = self.session.run(None, onnx_inputs)
        
        # Get embeddings/logits from the output
        embeddings = outputs[0]
        
        # For sentence embeddings, use mean pooling over sequence length
        # Shape: (batch_size, seq_length, hidden_size)
        # Apply mean pooling using attention mask
        attention_mask = inputs['attention_mask']
        
        # Validate attention mask is not all zeros
        if np.sum(attention_mask) == 0:
            raise ValueError("Invalid input: attention mask is all zeros")
        
        mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(attention_mask, axis=1, keepdims=True), a_min=1e-9, a_max=None)
        mean_embeddings = sum_embeddings / sum_mask
        
        # Return results
        return {
            'embeddings': mean_embeddings,
            'raw_output': embeddings,
            'text': text
        }
    
    def batch_predict(self, texts: List[str], max_length: int = 128) -> List[Dict[str, Any]]:
        """
        Process multiple queries in batch.
        
        Args:
            texts: List of input query texts.
            max_length: Maximum sequence length.
            
        Returns:
            List of prediction dictionaries.
        """
        return [self.predict(text, max_length) for text in texts]
    
    def get_similarity(self, text1: str, text2: str, max_length: int = 128) -> float:
        """
        Compute cosine similarity between two text inputs.
        
        Args:
            text1: First text input.
            text2: Second text input.
            max_length: Maximum sequence length.
            
        Returns:
            Cosine similarity score between 0 and 1.
        """
        # Get embeddings for both texts
        pred1 = self.predict(text1, max_length)
        pred2 = self.predict(text2, max_length)
        
        emb1 = pred1['embeddings'].flatten()
        emb2 = pred2['embeddings'].flatten()
        
        # Compute cosine similarity with zero-vector check
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        # Handle zero vectors
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        dot_product = np.dot(emb1, emb2)
        similarity = dot_product / (norm1 * norm2)
        
        return float(similarity)


def main():
    """
    Example usage of the ONNX NLP Model.
    """
    try:
        # Initialize the model
        print("Initializing ONNX NLP Model...")
        model = ONNXNLPModel()
        
        # Example queries
        queries = [
            "How do I scrape a web page?",
            "Extract data from a website",
            "Download HTML content"
        ]
        
        print("\n" + "="*60)
        print("Processing Natural Language Queries")
        print("="*60 + "\n")
        
        # Process each query
        for i, query in enumerate(queries, 1):
            print(f"Query {i}: {query}")
            result = model.predict(query)
            print(f"  - Embedding shape: {result['embeddings'].shape}")
            print(f"  - Embedding (first 5 values): {result['embeddings'].flatten()[:5]}")
            print()
        
        # Test similarity
        print("="*60)
        print("Testing Similarity")
        print("="*60 + "\n")
        
        similarity = model.get_similarity(queries[0], queries[1])
        print(f"Similarity between:")
        print(f"  - '{queries[0]}'")
        print(f"  - '{queries[1]}'")
        print(f"  Score: {similarity:.4f}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease ensure you have run 'python setup_model.py' first.")


if __name__ == "__main__":
    main()
