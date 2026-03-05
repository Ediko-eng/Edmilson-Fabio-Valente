"""
Enhanced DFA Engine with Linguistic Selection
COMPLETE VERSION WITH ALL DFA CLASSES
"""

import re

# ============================================================================
# ORIGINAL DFA CLASS (For backward compatibility)
# ============================================================================

class DFAVocabularyAnalyzer:
    """DFA engine for lowercase word recognition"""
    
    def __init__(self):
        self.min_length = 3
        self.max_length = 15
    
    def process_text(self, text, min_length=3, max_length=15):
        """Process text and extract words within length range"""
        self.min_length = min_length
        self.max_length = max_length
        
        # Convert to lowercase and find all words
        text_lower = text.lower()
        words = re.findall(r'\b[a-z]{' + str(min_length) + ',' + str(max_length) + r'}\b', text_lower)
        
        # Remove duplicates and sort
        unique_words = sorted(list(set(words)))
        return unique_words
    
    def validate_word(self, word):
        """Validate if a word is accepted by the DFA"""
        if not isinstance(word, str):
            return False
        
        word_lower = word.lower()
        
        # Check length
        if len(word_lower) < self.min_length or len(word_lower) > self.max_length:
            return False
        
        # Check if only lowercase letters
        if not re.match(r'^[a-z]+$', word_lower):
            return False
        
        # Check for at least one vowel (for English)
        if not any(char in 'aeiou' for char in word_lower):
            return False
        
        return True


# ============================================================================
# ENHANCED DFA CLASS (New with language support)
# ============================================================================

class EnhancedDFAAnalyzer:
    """DFA engine with language-specific processing"""
    
    # Language-specific character sets - FIXED with proper diacritics
    LANGUAGE_ALPHABETS = {
        "English": r'a-z',
        "Indonesia": r'a-záéíóúàèìòùâêîôûãõç',  # Indonesian with diacritics
        "Tetum": r'a-záéíóúàèìòùâêîôûãõçñ',  # Tetum + Portuguese diacritics
        "General": r'a-z'  # Fallback
    }
    
    # Language-specific stop words
    LANGUAGE_STOP_WORDS = {
        "English": {
            'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but',
            'from', 'they', 'say', 'her', 'she', 'will', 'one', 'all', 'would', 'there',
        },
        "Indonesia": {
            'yang', 'dan', 'di', 'dengan', 'ini', 'itu', 'dari', 'untuk', 'pada',
            'ke', 'tidak', 'akan', 'ada', 'atau', 'juga', 'dalam', 'bisa', 'saya',
        },
        "Tetum": {
            'iha', 'ho', 'ba', 'de', 'no', 'ne', 'nee', 'neebe', 'hodi', 'tanba',
            'mak', 'mos', 'hotu', 'ida', 'nebe', 'liu', 'ona', 'nia', 'sira',
        }
    }
    
    def __init__(self, language="English"):
        self.min_length = 3
        self.max_length = 15
        self.language = language
        self.alphabet = self.LANGUAGE_ALPHABETS.get(language, self.LANGUAGE_ALPHABETS["General"])
    
    def process_text_with_language(self, text, min_length=3, max_length=15, filter_stop_words=True):
        """Process text with language-specific rules"""
        self.min_length = min_length
        self.max_length = max_length
        
        # Convert to lowercase for processing
        text_lower = text.lower()
        
        # Create regex pattern based on language alphabet
        pattern = r'\b[' + self.alphabet + ']{' + str(min_length) + ',' + str(max_length) + r'}\b'
        
        # Find all words matching the language alphabet
        words = re.findall(pattern, text_lower)
        
        # Filter stop words if requested
        if filter_stop_words and self.language in self.LANGUAGE_STOP_WORDS:
            stop_words = self.LANGUAGE_STOP_WORDS[self.language]
            words = [w for w in words if w not in stop_words]
        
        # Remove duplicates and sort
        unique_words = sorted(list(set(words)))
        return unique_words
    
    def validate_word(self, word, language=None):
        """Validate if a word is accepted by the language-specific DFA"""
        if not isinstance(word, str):
            return False
        
        word_lower = word.lower()
        
        # Check length
        if len(word_lower) < self.min_length or len(word_lower) > self.max_length:
            return False
        
        # Use specified language or default
        lang = language if language else self.language
        alphabet_pattern = self.LANGUAGE_ALPHABETS.get(lang, self.LANGUAGE_ALPHABETS["General"])
        
        # Check if only contains language-specific characters
        if not re.match(r'^[' + alphabet_pattern + ']+$', word_lower):
            return False
        
        # Language-specific validation rules
        if lang == "English":
            # English: Check for at least one vowel
            if not any(char in 'aeiou' for char in word_lower):
                return False
        
        elif lang == "Tetum":
            # Tetum: Common validation rules
            # Must have at least one vowel (a, e, i, o, u, or Tetum-specific)
            tetum_vowels = 'aeiouáéíóúàèìòùâêîôûãõ'
            if not any(char in tetum_vowels for char in word_lower):
                return False
        
        return True
    
    def get_language_stats(self, words):
        """Get language-specific statistics"""
        if not words:
            return {
                'total_words': 0,
                'min_length': 0,
                'max_length': 0,
                'avg_length': 0,
                'language': self.language,
                'fa_type': 'DFA'
            }
        
        lengths = [len(w) for w in words]
        
        # Count language-specific patterns
        vowel_counts = []
        for word in words:
            if self.language == "English":
                vowels = 'aeiou'
            elif self.language == "Tetum":
                vowels = 'aeiouáéíóúàèìòùâêîôûãõ'
            elif self.language == "Indonesia":
                vowels = 'aeiouáéíóúàèìòùâêîôûãõ'
            else:
                vowels = 'aeiou'
            
            vowel_count = sum(1 for char in word if char in vowels)
            vowel_counts.append(vowel_count)
        
        return {
            "total_words": len(words),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": round(sum(lengths) / len(words), 2),
            "avg_vowels": round(sum(vowel_counts) / len(vowel_counts), 2) if vowel_counts else 0,
            "language": self.language,
            "fa_type": "DFA"
        }


# ============================================================================
# NFA CLASS (Unchanged)
# ============================================================================

class NFAVocabularyAnalyzer:
    """NFA engine for pattern-based word recognition"""
    
    def __init__(self):
        self.patterns = {
            "English Words": r'\b[a-z]{3,}\b',
            "Words with 'ing'": r'\b[a-z]*ing\b',
            "Words with 'tion'": r'\b[a-z]*tion\b',
            "Words with Prefix 'un'": r'\bun[a-z]{2,}\b',
            "Words with Suffix 'ly'": r'\b[a-z]*ly\b',
            "Compound Words": r'\b[a-z]+[a-z]+\b',
            "Tetum Words": r'\b(ha|na|ma|ba|sa|ta)[a-z]*\b',
            "Indonesian Words": r'\b(me|ber|di|ter|pe)[a-z]*\b',
            "Numbers in Text": r'\b\d+\b',
            "Email Patterns": r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b',
            "Simple 3-Letter Words": r'\b[a-z]{3}\b',
            "Words Ending with 's'": r'\b[a-z]+s\b',
            "Words Starting with Vowel": r'\b[aeiou][a-z]*\b',
            "Words with Double Letters": r'\b[a-z]*([a-z])\1[a-z]*\b',
            "Palindromes (3-5 letters)": r'\b([a-z])([a-z])?\2?\1\b'
        }
    
    def get_patterns(self):
        """Return available NFA patterns"""
        return list(self.patterns.keys())
    
    def process_with_pattern(self, text, pattern_name):
        """Process text using selected NFA pattern"""
        if pattern_name not in self.patterns:
            return []
        
        pattern = self.patterns[pattern_name]
        
        try:
            matches = re.findall(pattern, text.lower())
            
            # For some patterns, we need to flatten the matches
            if matches and isinstance(matches[0], tuple):
                matches = [match[0] for match in matches if match]
            
            return list(set(matches))
        except:
            return []
    
    def explain_pattern(self, pattern_name):
        """Explain what the pattern does"""
        explanations = {
            "English Words": "Matches any lowercase English word with 3 or more letters",
            "Words with 'ing'": "Matches words ending with 'ing' (present participles)",
            "Words with 'tion'": "Matches words ending with 'tion' (nouns)",
            "Words with Prefix 'un'": "Matches words starting with 'un-' prefix",
            "Words with Suffix 'ly'": "Matches words ending with '-ly' (adverbs)",
            "Compound Words": "Matches words with at least 2 syllables",
            "Tetum Words": "Matches Tetum words with common prefixes: ha, na, ma, ba, sa, ta",
            "Indonesian Words": "Matches Indonesian words with common prefixes: me, ber, di, ter, pe",
            "Numbers in Text": "Extracts numerical values from text",
            "Email Patterns": "Finds email addresses in text",
            "Simple 3-Letter Words": "Matches exactly 3-letter words",
            "Words Ending with 's'": "Matches plural forms or verb conjugations",
            "Words Starting with Vowel": "Matches words starting with a vowel (a, e, i, o, u)",
            "Words with Double Letters": "Matches words containing double letters (like 'book', 'happy')",
            "Palindromes (3-5 letters)": "Matches short palindrome words (like 'mom', 'dad', 'level')"
        }
        return explanations.get(pattern_name, "No explanation available")