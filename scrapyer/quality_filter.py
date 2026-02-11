"""
Smart Content Quality Filter

This module provides intelligent content quality filtering using linguistic and structural
signals to distinguish informative prose content from UI/navigation elements.
"""

import re
import statistics
from typing import Dict, Tuple, Optional


class ContentQualityFilter:
    """
    Base heuristic-based content quality filter.
    
    Uses multiple linguistic and structural signals to score content quality:
    - Sentence complexity (varied sentence lengths indicate natural prose)
    - Vocabulary richness (Type-Token Ratio)
    - Information density (numbers, dates, proper nouns, research terms)
    - Research language indicators
    - Noise penalty (navigation/UI patterns)
    
    Example:
        >>> filter = ContentQualityFilter(min_quality_score=0.6)
        >>> sample = "Researchers found that depression in older adults may signal early stages of Parkinson's disease."
        >>> score, details = filter.calculate_quality_score(sample)
        >>> print(f"Score: {score:.2f}")
        >>> print(f"Details: {details}")
    """
    
    # Scoring weights for different quality signals
    WEIGHTS = {
        'sentence_complexity': 0.2,
        'vocabulary_richness': 0.15,
        'information_density': 0.25,
        'research_indicators': 0.3,
        'noise_penalty': 0.1,
    }
    
    # Research language patterns
    RESEARCH_PATTERNS = [
        r'\bresearchers?\s+(?:found|discovered|showed|demonstrated)',
        r'\bstud(?:y|ies)\s+(?:show|showed|suggest|found|indicate)',
        r'\bscientists?\s+(?:found|discovered|believe|think)',
        r'\bevidence\s+suggests?',
        r'\baccording\s+to\s+(?:the\s+)?(?:study|research|scientists?|researchers?)',
        r'\bpublished\s+in\s+(?:the\s+)?',
        r'\bdata\s+(?:shows?|indicates?|suggests?)',
        r'\bfindings?\s+(?:show|showed|suggest|indicate)',
    ]
    
    # Noise/navigation patterns to penalize
    NOISE_PATTERNS = [
        r'^(?:Top\s+\d+|View\s+All|More|Next|Previous|Read\s+More)\b',
        r'^\d+\s*$',  # Standalone numbers (pagination)
        r'^(?:\d{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}$',  # Standalone dates
        r'/(?:rss|feed|top|category|tag)/',  # Path-like text
        r'\s*\|\s*',  # Pipe separators (common in menus)
    ]
    
    def __init__(self, min_quality_score: float = 0.6):
        """
        Initialize the quality filter.
        
        Args:
            min_quality_score: Minimum score (0-1) for content to be considered quality
        """
        self.min_quality_score = min_quality_score
        self._research_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.RESEARCH_PATTERNS]
        self._noise_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.NOISE_PATTERNS]
    
    def _score_sentence_complexity(self, text: str) -> float:
        """
        Score based on sentence length variance.
        Quality prose has varied sentence lengths, while UI text tends to be uniform.
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0 and 1
        """
        # Split into sentences (simple approach)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return 0.3  # Too few sentences
        
        # Calculate word counts per sentence
        word_counts = [len(s.split()) for s in sentences]
        
        # Calculate coefficient of variation (std dev / mean)
        if not word_counts or statistics.mean(word_counts) == 0:
            return 0.3
        
        try:
            cv = statistics.stdev(word_counts) / statistics.mean(word_counts)
            # Normalize: CV of 0.3-0.7 is typical for natural prose
            # Higher variance = higher score (more natural)
            score = min(1.0, cv / 0.7)
            return max(0.0, score)
        except statistics.StatisticsError:
            return 0.3
    
    def _score_vocabulary_richness(self, text: str) -> float:
        """
        Score based on Type-Token Ratio (unique words / total words).
        Quality content uses diverse vocabulary.
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0 and 1
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        if len(words) < 10:
            return 0.4  # Too short to evaluate
        
        unique_words = len(set(words))
        total_words = len(words)
        ttr = unique_words / total_words
        
        # TTR typically ranges from 0.4-0.8 for quality prose
        # Lower for repetitive UI text
        if ttr < 0.3:
            return 0.2
        elif ttr > 0.7:
            return 1.0
        else:
            # Linear scale from 0.3 to 0.7
            return (ttr - 0.3) / 0.4
    
    def _score_information_density(self, text: str) -> float:
        """
        Score based on presence of numbers, dates, proper nouns, and technical terms.
        Informative content tends to have higher information density.
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        words = text.split()
        
        if len(words) < 10:
            return 0.3
        
        # Count numbers (including percentages, decimals)
        numbers = len(re.findall(r'\b\d+(?:\.\d+)?%?\b', text))
        if numbers > 0:
            score += 0.3
        
        # Count capitalized words (potential proper nouns, excluding sentence starts)
        sentences = re.split(r'[.!?]+', text)
        proper_nouns = 0
        for sentence in sentences:
            words_in_sentence = sentence.strip().split()
            # Skip first word (sentence start)
            for word in words_in_sentence[1:]:
                if word and word[0].isupper() and len(word) > 1:
                    proper_nouns += 1
        
        if proper_nouns > 2:
            score += 0.3
        
        # Check for long words (technical/academic terms)
        long_words = len([w for w in words if len(w) > 8])
        if long_words > len(words) * 0.1:  # More than 10% long words
            score += 0.2
        
        # Check for statistics-related terms
        stats_terms = len(re.findall(r'\b(?:million|billion|percent|average|median|rate)\b', text, re.IGNORECASE))
        if stats_terms > 0:
            score += 0.2
        
        return min(1.0, score)
    
    def _score_research_indicators(self, text: str) -> float:
        """
        Score based on presence of research/scientific language patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0 and 1
        """
        matches = 0
        for pattern in self._research_regex:
            if pattern.search(text):
                matches += 1
        
        # More matches = higher score
        # Cap at 1.0 for 3+ matches
        return min(1.0, matches / 3.0)
    
    def _score_noise_penalty(self, text: str) -> float:
        """
        Penalize content for navigation/UI patterns.
        Returns a score where 1.0 = no noise, 0.0 = heavy noise.
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0 and 1 (inverted - higher is better)
        """
        lines = text.split('\n')
        noise_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in self._noise_regex:
                if pattern.search(line):
                    noise_lines += 1
                    break
        
        if not lines:
            return 1.0
        
        # Calculate noise ratio and invert
        noise_ratio = noise_lines / max(1, len([l for l in lines if l.strip()]))
        return 1.0 - min(1.0, noise_ratio)
    
    def calculate_quality_score(self, text: str) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall quality score and detailed breakdown.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (overall_score, detailed_scores)
        """
        if not text or len(text.strip()) < 50:
            return 0.0, {}
        
        scores = {
            'sentence_complexity': self._score_sentence_complexity(text),
            'vocabulary_richness': self._score_vocabulary_richness(text),
            'information_density': self._score_information_density(text),
            'research_indicators': self._score_research_indicators(text),
            'noise_penalty': self._score_noise_penalty(text),
        }
        
        # Calculate weighted average
        overall_score = sum(scores[key] * self.WEIGHTS[key] for key in scores)
        
        return overall_score, scores
    
    def is_quality_content(self, text: str) -> bool:
        """
        Check if text meets the quality threshold.
        
        Args:
            text: Text to check
            
        Returns:
            True if quality score meets or exceeds threshold
        """
        score, _ = self.calculate_quality_score(text)
        return score >= self.min_quality_score
    
    def filter_paragraphs(self, text: str) -> str:
        """
        Filter text to keep only quality paragraphs.
        
        Args:
            text: Text with multiple paragraphs
            
        Returns:
            Filtered text with only quality paragraphs
        """
        # Split into paragraphs (double newlines)
        paragraphs = re.split(r'\n\s*\n', text)
        
        quality_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if paragraph meets quality threshold
            if self.is_quality_content(para):
                quality_paragraphs.append(para)
        
        return '\n\n'.join(quality_paragraphs)


class NLPEnhancedQualityFilter(ContentQualityFilter):
    """
    Enhanced quality filter that uses ONNX model for semantic analysis.
    Falls back to heuristics if NLP model is unavailable.
    
    Example:
        >>> filter = NLPEnhancedQualityFilter(min_quality_score=0.6, use_nlp=True)
        >>> score, details = filter.calculate_quality_score("Sample text")
    """
    
    # Quality prose templates for semantic comparison
    QUALITY_TEMPLATES = [
        "Researchers conducted a comprehensive study analyzing the effects and implications.",
        "The scientific evidence demonstrates significant findings about the phenomenon.",
        "According to published research, the data indicates important correlations.",
        "Scientists discovered new insights through systematic investigation and analysis.",
    ]
    
    def __init__(self, min_quality_score: float = 0.6, use_nlp: bool = True):
        """
        Initialize enhanced quality filter with optional NLP.
        
        Args:
            min_quality_score: Minimum score for quality content
            use_nlp: Whether to use NLP model (falls back if unavailable)
        """
        super().__init__(min_quality_score)
        self.nlp_model = None
        self.use_nlp = use_nlp
        
        if use_nlp:
            self._load_nlp_model()
    
    def _load_nlp_model(self):
        """Load ONNX NLP model if available."""
        try:
            from nlp.onnx_nlp_model import ONNXNLPModel
            self.nlp_model = ONNXNLPModel()
            print("✓ NLP quality enhancement enabled")
        except (ImportError, FileNotFoundError, RuntimeError) as e:
            print(f"ℹ️  NLP model not available, using heuristics only: {type(e).__name__}")
            self.nlp_model = None
    
    def _score_semantic_quality(self, text: str) -> float:
        """
        Score content based on semantic similarity to quality prose templates.
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0 and 1
        """
        if self.nlp_model is None:
            return 0.5  # Neutral score if NLP unavailable
        
        try:
            # Get maximum similarity across all quality templates
            similarities = []
            for template in self.QUALITY_TEMPLATES:
                sim = self.nlp_model.get_similarity(text, template)
                similarities.append(sim)
            
            # Return the best match
            return max(similarities) if similarities else 0.5
        except Exception as e:
            print(f"⚠️  NLP scoring failed: {e}")
            return 0.5  # Neutral score on error
    
    def calculate_quality_score(self, text: str) -> Tuple[float, Dict[str, float]]:
        """
        Calculate quality score with optional NLP enhancement.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (overall_score, detailed_scores)
        """
        # Get base heuristic scores
        base_score, scores = super().calculate_quality_score(text)
        
        # Add semantic quality if NLP is available
        if self.nlp_model is not None:
            semantic_score = self._score_semantic_quality(text)
            scores['semantic_quality'] = semantic_score
            
            # Recalculate with NLP weight (adjust weights to include semantic)
            # Reduce other weights slightly to make room for semantic (10%)
            adjusted_weights = {k: v * 0.9 for k, v in self.WEIGHTS.items()}
            adjusted_weights['semantic_quality'] = 0.1
            
            overall_score = sum(scores[key] * adjusted_weights.get(key, 0) for key in scores)
            return overall_score, scores
        
        return base_score, scores
