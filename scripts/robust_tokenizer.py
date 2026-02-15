"""
robust_tokenizer.py - Improved sentence tokenization for semantic retrieval

This module provides robust sentence boundary detection that handles:
- Abbreviations (e.g., i.e., etc., Ph.D., et al.)
- Decimal numbers (0.45, 3.14159)
- URLs and domains (cdn.openai.com)
- Ellipses (...)
- Initials and titles (Dr., Mr., Mrs., Prof.)
- Common technical abbreviations

Requirements:
    pip install nltk

First-time setup:
    import nltk
    nltk.download('punkt')
    nltk.download('punkt_tab')

Usage:
    from robust_tokenizer import RobustSentenceTokenizer
    
    tokenizer = RobustSentenceTokenizer()
    sentences = tokenizer.tokenize(text)
    chunks = tokenizer.create_chunks(text, window_size=3, stride=2)

Author: Claude (Technical Review)
Date: 2026-02-02
"""

import re
from typing import List, Tuple
import warnings

# Try to import NLTK, fall back to regex-based approach if unavailable
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    warnings.warn("NLTK not available. Using regex-based fallback tokenizer.")


class RobustSentenceTokenizer:
    """
    A robust sentence tokenizer that handles edge cases common in technical documentation.
    
    Uses NLTK's Punkt tokenizer as the base, with custom pre/post-processing
    to handle abbreviations, URLs, decimal numbers, and other edge cases.
    """
    
    # Common abbreviations that should not end sentences
    ABBREVIATIONS = {
        # Latin
        'e.g', 'i.e', 'etc', 'et al', 'vs', 'cf', 'viz', 'ibid', 'op. cit',
        # Titles
        'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'rev', 'hon',
        # Academic
        'ph.d', 'b.s', 'm.s', 'b.a', 'm.a', 'j.d', 'm.d', 'ed.d',
        # Technical
        'fig', 'eq', 'sec', 'ch', 'vol', 'no', 'pp', 'p', 'approx',
        # Organizational
        'inc', 'corp', 'ltd', 'co', 'llc', 'plc',
        # Geographic
        'st', 'ave', 'blvd', 'rd', 'mt', 'ft',
        # Measurement
        'oz', 'lb', 'kg', 'km', 'cm', 'mm', 'ml', 'hr', 'min', 'sec',
        # Common in AI/ML papers
        'ref', 'tab', 'app', 'supp', 'al', 'arxiv'
    }
    
    # Patterns that should be protected from sentence splitting
    PROTECTION_PATTERNS = [
        # Decimal numbers: 0.45, 3.14159, -2.5
        (r'(\d+)\.(\d+)', r'\1<DECIMAL>\2'),
        # Version numbers: v1.2.3, 2.0, GPT-4.0
        (r'(\d+)\.(\d+)\.?(\d*)', r'\1<VERSION>\2<VERSION>\3'),
        # URLs and domains
        (r'(https?://[^\s]+)', lambda m: m.group(1).replace('.', '<DOT>')),
        (r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?)', 
         lambda m: m.group(1).replace('.', '<DOT>')),
        # Ellipses
        (r'\.\.\.', '<ELLIPSIS>'),
        # Section references: Sec. 3.2, Section 4.1
        (r'([Ss]ec(?:tion)?\.?\s*)(\d+)\.(\d+)', r'\1\2<SECREF>\3'),
        # Figure/Table references: Fig. 3, Table 2.1
        (r'([Ff]ig(?:ure)?\.?\s*)(\d+)\.?(\d*)', r'\1\2<FIGREF>\3'),
        (r'([Tt]ab(?:le)?\.?\s*)(\d+)\.?(\d*)', r'\1\2<TABREF>\3'),
    ]
    
    # Restoration patterns (reverse of protection)
    RESTORATION_PATTERNS = [
        ('<DECIMAL>', '.'),
        ('<VERSION>', '.'),
        ('<DOT>', '.'),
        ('<ELLIPSIS>', '...'),
        ('<SECREF>', '.'),
        ('<FIGREF>', '.'),
        ('<TABREF>', '.'),
    ]
    
    def __init__(self, min_sentence_length: int = 10):
        """
        Initialize the tokenizer.
        
        Args:
            min_sentence_length: Minimum character length for a valid sentence.
                                Sentences shorter than this are merged with adjacent ones.
        """
        self.min_sentence_length = min_sentence_length
        self._setup_nltk()
    
    def _setup_nltk(self):
        """Set up NLTK tokenizer with custom abbreviations."""
        if not NLTK_AVAILABLE:
            return
            
        try:
            # Try to use punkt tokenizer
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('punkt_tab', quiet=True)
            except Exception as e:
                warnings.warn(f"Could not download NLTK data: {e}. Using fallback tokenizer.")
        
        # Create custom Punkt parameters with our abbreviations
        try:
            self.punkt_params = PunktParameters()
            for abbrev in self.ABBREVIATIONS:
                self.punkt_params.abbrev_types.add(abbrev.lower().rstrip('.'))
            self.tokenizer = PunktSentenceTokenizer(self.punkt_params)
        except Exception:
            self.tokenizer = None
    
    def _protect_patterns(self, text: str) -> str:
        """Replace patterns that shouldn't cause sentence breaks with placeholders."""
        protected = text
        for pattern, replacement in self.PROTECTION_PATTERNS:
            if callable(replacement):
                protected = re.sub(pattern, replacement, protected)
            else:
                protected = re.sub(pattern, replacement, protected)
        return protected
    
    def _restore_patterns(self, text: str) -> str:
        """Restore protected patterns to their original form."""
        restored = text
        for placeholder, original in self.RESTORATION_PATTERNS:
            restored = restored.replace(placeholder, original)
        return restored
    
    def _protect_abbreviations(self, text: str) -> str:
        """Protect abbreviations from causing sentence breaks."""
        protected = text
        for abbrev in self.ABBREVIATIONS:
            # Case-insensitive replacement, but preserve original case
            pattern = re.compile(
                r'\b(' + re.escape(abbrev) + r')\.(\s)',
                re.IGNORECASE
            )
            protected = pattern.sub(r'\1<ABBR>\2', protected)
        return protected
    
    def _restore_abbreviations(self, text: str) -> str:
        """Restore abbreviation periods."""
        return text.replace('<ABBR>', '.')
    
    def _fallback_tokenize(self, text: str) -> List[str]:
        """
        Regex-based fallback tokenizer when NLTK is not available.
        
        This is less accurate than NLTK but handles common cases.
        """
        # Split on sentence-ending punctuation followed by space and capital letter
        # or followed by newline
        pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\n+'
        
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into sentences with robust handling of edge cases.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of sentence strings
        """
        if not text or not text.strip():
            return []
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Protect special patterns
        protected = self._protect_patterns(text)
        protected = self._protect_abbreviations(protected)
        
        # Tokenize
        if NLTK_AVAILABLE and self.tokenizer:
            try:
                raw_sentences = self.tokenizer.tokenize(protected)
            except Exception:
                raw_sentences = self._fallback_tokenize(protected)
        else:
            raw_sentences = self._fallback_tokenize(protected)
        
        # Restore patterns and clean up
        sentences = []
        for sent in raw_sentences:
            restored = self._restore_patterns(sent)
            restored = self._restore_abbreviations(restored)
            restored = restored.strip()
            
            if len(restored) >= self.min_sentence_length:
                sentences.append(restored)
            elif sentences:
                # Merge short sentence with previous
                sentences[-1] = sentences[-1] + ' ' + restored
        
        return sentences
    
    def create_chunks(
        self, 
        text: str, 
        window_size: int = 3, 
        stride: int = 2,
        min_chunk_length: int = 20
    ) -> List[str]:
        """
        Create overlapping chunks of sentences for semantic search.
        
        Args:
            text: Input text to chunk
            window_size: Number of sentences per chunk
            stride: Number of sentences to advance between chunks
            min_chunk_length: Minimum character length for valid chunks
            
        Returns:
            List of text chunks
        """
        sentences = self.tokenize(text)
        
        if not sentences:
            return []
        
        chunks = []
        for i in range(0, len(sentences), stride):
            window = sentences[i:i + window_size]
            chunk = ' '.join(window)
            
            if len(chunk) >= min_chunk_length:
                chunks.append(chunk)
            
            # Stop if we've processed all sentences
            if i + window_size >= len(sentences):
                break
        
        return chunks


def create_chunks_from_text(
    text: str,
    window_size: int = 3,
    stride: int = 2,
    min_sentence_length: int = 10,
    min_chunk_length: int = 20
) -> List[str]:
    """
    Convenience function for chunking text.
    
    This is a drop-in replacement for the original _chunk_text method
    in semantic_retriever.py and analyze_nlu.py.
    
    Args:
        text: Input text to chunk
        window_size: Number of sentences per chunk
        stride: Sentences to advance between chunks
        min_sentence_length: Minimum length for valid sentences
        min_chunk_length: Minimum length for valid chunks
        
    Returns:
        List of text chunks
    """
    tokenizer = RobustSentenceTokenizer(min_sentence_length=min_sentence_length)
    return tokenizer.create_chunks(
        text, 
        window_size=window_size, 
        stride=stride,
        min_chunk_length=min_chunk_length
    )


# ============================================================================
# INTEGRATION GUIDE
# ============================================================================
#
# To integrate this into your existing scripts:
#
# 1. In semantic_retriever.py, replace the _chunk_text method:
#
#    from robust_tokenizer import create_chunks_from_text
#
#    def _chunk_text(self, text: str) -> List[str]:
#        return create_chunks_from_text(
#            text,
#            window_size=WINDOW_SIZE,
#            stride=STRIDE,
#            min_sentence_length=10,
#            min_chunk_length=20
#        )
#
# 2. In analyze_nlu.py, make the same replacement:
#
#    from robust_tokenizer import create_chunks_from_text
#
#    def _chunk_text(self, text: str) -> List[str]:
#        return create_chunks_from_text(
#            text,
#            window_size=WINDOW_SIZE,
#            stride=STRIDE,
#            min_sentence_length=20,  # analyze_nlu uses 20
#            min_chunk_length=20
#        )
#
# ============================================================================


if __name__ == "__main__":
    # Test cases
    test_texts = [
        # Abbreviations
        "The model uses RLHF, i.e., reinforcement learning from human feedback. "
        "This is described in Sec. 3.2 of the paper. Dr. Smith et al. presented this.",
        
        # Decimal numbers
        "The threshold is set to 0.45 for precision. We achieved 95.3% accuracy. "
        "The model version is GPT-4.0 with a temperature of 0.7.",
        
        # URLs
        "See the documentation at https://cdn.openai.com/docs/safety.pdf for details. "
        "The model card is at anthropic.com/research/model-cards.",
        
        # Mixed edge cases
        "We use Constitutional AI (cf. Bai et al., 2022) for alignment. "
        "Fig. 3.1 shows the results. The ASL-3 threshold was met per the RSP v2.0 framework.",
        
        # Ellipses
        "The model sometimes responds with... unexpected outputs. "
        "We investigated this behavior and found...",
    ]
    
    tokenizer = RobustSentenceTokenizer()
    
    print("=" * 60)
    print("ROBUST SENTENCE TOKENIZER - TEST OUTPUT")
    print("=" * 60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input: {text[:80]}...")
        sentences = tokenizer.tokenize(text)
        print(f"Sentences ({len(sentences)}):")
        for j, sent in enumerate(sentences, 1):
            print(f"  {j}. {sent}")
        
        chunks = tokenizer.create_chunks(text, window_size=2, stride=1)
        print(f"Chunks ({len(chunks)}):")
        for j, chunk in enumerate(chunks, 1):
            print(f"  {j}. {chunk[:60]}...")
    
    print("\n" + "=" * 60)
    print("Tests complete. NLTK available:", NLTK_AVAILABLE)
    print("=" * 60)
