"""
Tests for the smart content quality filter
"""

import unittest
from scrapyer.quality_filter import ContentQualityFilter, NLPEnhancedQualityFilter


class TestContentQualityFilter(unittest.TestCase):
    """Test the base ContentQualityFilter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.filter = ContentQualityFilter(min_quality_score=0.6)
    
    def test_high_quality_research_content(self):
        """Test that research content scores highly"""
        text = """Researchers found that depression in older adults may signal early stages 
        of Parkinson's disease. The study, published in the Journal of Neurology, analyzed 
        data from over 50,000 participants. Scientists discovered that 27% of patients with 
        late-onset depression later developed Parkinson's symptoms. According to the research 
        team, this finding could help identify at-risk individuals years before motor symptoms appear."""
        
        score, details = self.filter.calculate_quality_score(text)
        
        # Should score highly
        self.assertGreater(score, 0.6, "Research content should score above 0.6")
        self.assertTrue(self.filter.is_quality_content(text))
        
        # Check individual components
        self.assertGreater(details['research_indicators'], 0.5, 
                          "Should detect research language")
        self.assertGreater(details['information_density'], 0.5,
                          "Should detect high information density")
    
    def test_low_quality_navigation_content(self):
        """Test that navigation/UI text scores poorly"""
        text = """Top 10
        View All
        Next Page
        1 2 3 4 5
        Category | News | Archives
        More Articles"""
        
        score, details = self.filter.calculate_quality_score(text)
        
        # Should score poorly
        self.assertLess(score, 0.5, "Navigation content should score below 0.5")
        self.assertFalse(self.filter.is_quality_content(text))
        
        # Noise penalty should be low (high noise)
        self.assertLess(details['noise_penalty'], 0.5,
                       "Should detect navigation patterns")
    
    def test_sentence_complexity_scoring(self):
        """Test sentence complexity detection"""
        # Varied sentence lengths (natural prose)
        varied_text = """This is short. This is a much longer sentence with more words. Brief. 
        Here's another lengthy sentence that contains several clauses and ideas."""
        
        # Uniform sentence lengths (UI text)
        uniform_text = """Click here. View more. Read this. Learn now."""
        
        varied_score = self.filter._score_sentence_complexity(varied_text)
        uniform_score = self.filter._score_sentence_complexity(uniform_text)
        
        self.assertGreater(varied_score, uniform_score,
                          "Varied sentences should score higher than uniform")
    
    def test_vocabulary_richness_scoring(self):
        """Test Type-Token Ratio calculation"""
        # Diverse vocabulary
        rich_text = """Scientists conducted extensive research analyzing various phenomena 
        through systematic investigation of different methodologies."""
        
        # Repetitive vocabulary
        poor_text = """The test test test showed test results. The test was a test of tests."""
        
        rich_score = self.filter._score_vocabulary_richness(rich_text)
        poor_score = self.filter._score_vocabulary_richness(poor_text)
        
        self.assertGreater(rich_score, poor_score,
                          "Diverse vocabulary should score higher")
    
    def test_information_density_scoring(self):
        """Test information density detection"""
        # High information density
        dense_text = """The study examined 50,000 participants over 15 years. Results showed 
        a 27% increase in symptoms. Dr. Smith reported that 3.5 million people are affected."""
        
        # Low information density
        sparse_text = """Something happened. There were people involved. Things changed."""
        
        dense_score = self.filter._score_information_density(dense_text)
        sparse_score = self.filter._score_information_density(sparse_text)
        
        self.assertGreater(dense_score, sparse_score,
                          "Information-dense text should score higher")
    
    def test_research_indicators_detection(self):
        """Test research language pattern detection"""
        research_text = """Researchers found that the evidence suggests a correlation. 
        According to the study published in Nature, scientists discovered new insights."""
        
        non_research_text = """I think this is interesting. Maybe we should consider it."""
        
        research_score = self.filter._score_research_indicators(research_text)
        non_research_score = self.filter._score_research_indicators(non_research_text)
        
        self.assertGreater(research_score, non_research_score,
                          "Research language should be detected")
        self.assertGreater(research_score, 0.5,
                          "Should detect multiple research patterns")
    
    def test_noise_penalty_detection(self):
        """Test navigation/UI noise detection"""
        # Clean prose
        clean_text = """The comprehensive analysis revealed significant findings about the 
        underlying mechanisms. These discoveries have important implications for future research."""
        
        # Noisy navigation text
        noisy_text = """Top 10 | Next | Previous
        /rss/feed/
        View All Articles
        1 2 3 4 5"""
        
        clean_score = self.filter._score_noise_penalty(clean_text)
        noisy_score = self.filter._score_noise_penalty(noisy_text)
        
        self.assertGreater(clean_score, noisy_score,
                          "Clean text should have lower noise penalty")
        self.assertGreater(clean_score, 0.8, "Clean text should score high")
        self.assertLess(noisy_score, 0.5, "Noisy text should score low")
    
    def test_filter_paragraphs(self):
        """Test paragraph-level filtering"""
        text = """Researchers discovered a significant correlation in their study of over 50,000 participants. 
        The evidence shows that systematic investigation yields valuable insights into complex phenomena. 
        Scientists demonstrated that the methodology applied was robust, reliable, and reproducible across multiple trials.
        This represents an important advance in understanding the underlying mechanisms.
        
        Top 10 | Next | Previous
        
        According to published research, the findings indicate strong patterns and relationships in the data.
        Studies show that careful analysis of statistical evidence can reveal important correlations.
        The research team found that 27% of participants exhibited significant changes over the study period.
        
        View All Articles | More | Read More"""
        
        filtered = self.filter.filter_paragraphs(text)
        
        # Should keep quality paragraphs and remove navigation
        # At least one quality paragraph should be kept
        self.assertGreater(len(filtered), 0, "Should keep at least one quality paragraph")
        # Check for research content (any part of the quality paragraphs)
        self.assertTrue(
            "research" in filtered.lower() or "studies" in filtered.lower(),
            "Should keep research-related content"
        )
        # Navigation text should be removed
        self.assertNotIn("Top 10", filtered)
        self.assertNotIn("View All", filtered)
    
    def test_short_text_handling(self):
        """Test handling of very short text"""
        short_text = "Hi"
        score, details = self.filter.calculate_quality_score(short_text)
        
        self.assertEqual(score, 0.0, "Very short text should score 0")
        self.assertFalse(self.filter.is_quality_content(short_text))
    
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        empty_text = ""
        score, details = self.filter.calculate_quality_score(empty_text)
        
        self.assertEqual(score, 0.0, "Empty text should score 0")
        self.assertFalse(self.filter.is_quality_content(empty_text))
    
    def test_custom_threshold(self):
        """Test custom quality threshold"""
        strict_filter = ContentQualityFilter(min_quality_score=0.8)
        lenient_filter = ContentQualityFilter(min_quality_score=0.4)
        
        text = """The study examined various factors. Results showed some interesting patterns."""
        
        score, _ = strict_filter.calculate_quality_score(text)
        
        # Same score, different thresholds
        self.assertEqual(score, lenient_filter.calculate_quality_score(text)[0])
        
        # But different is_quality results
        if score < 0.8:
            self.assertFalse(strict_filter.is_quality_content(text))
        if score > 0.4:
            self.assertTrue(lenient_filter.is_quality_content(text))


class TestNLPEnhancedQualityFilter(unittest.TestCase):
    """Test the NLPEnhancedQualityFilter class"""
    
    def test_initialization_with_nlp_disabled(self):
        """Test initialization with NLP disabled"""
        filter = NLPEnhancedQualityFilter(min_quality_score=0.6, use_nlp=False)
        
        self.assertIsNone(filter.nlp_model, "NLP model should not be loaded")
        self.assertFalse(filter.use_nlp)
    
    def test_initialization_with_nlp_enabled(self):
        """Test initialization with NLP enabled (may not have model)"""
        filter = NLPEnhancedQualityFilter(min_quality_score=0.6, use_nlp=True)
        
        self.assertTrue(filter.use_nlp)
        # Model may or may not be available depending on setup
        # Just verify it doesn't crash
    
    def test_fallback_to_heuristics(self):
        """Test graceful fallback when NLP unavailable"""
        filter = NLPEnhancedQualityFilter(min_quality_score=0.6, use_nlp=True)
        
        text = """Researchers found important correlations. The study demonstrates 
        significant findings about the underlying mechanisms."""
        
        # Should work regardless of NLP availability
        score, details = filter.calculate_quality_score(text)
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0.0)
        self.assertIn('research_indicators', details)
    
    def test_semantic_quality_with_no_model(self):
        """Test semantic quality scoring without model"""
        filter = NLPEnhancedQualityFilter(use_nlp=False)
        
        score = filter._score_semantic_quality("test text")
        
        # Should return neutral score
        self.assertEqual(score, 0.5)
    
    def test_inherits_base_functionality(self):
        """Test that NLP filter inherits base filter methods"""
        filter = NLPEnhancedQualityFilter(min_quality_score=0.6)
        
        # Should have all base methods
        self.assertTrue(hasattr(filter, '_score_sentence_complexity'))
        self.assertTrue(hasattr(filter, '_score_vocabulary_richness'))
        self.assertTrue(hasattr(filter, '_score_information_density'))
        self.assertTrue(hasattr(filter, '_score_research_indicators'))
        self.assertTrue(hasattr(filter, '_score_noise_penalty'))
        self.assertTrue(hasattr(filter, 'filter_paragraphs'))


if __name__ == '__main__':
    unittest.main()
