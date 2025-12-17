# utils/author_matcher.py
"""
Intelligent author name matching with typo tolerance and cross-language support.
Handles: typos, different transliterations, English<->Russian names
"""

import json
import unicodedata
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from difflib import SequenceMatcher

# Transliteration mapping for matching English spellings to Russian names
TRANSLIT_MAP = {
    'shch': 'щ', 'sh': 'ш', 'ch': 'ч', 'zh': 'ж', 'kh': 'х', 'ts': 'ц',
    'yu': 'ю', 'ya': 'я', 'yo': 'ё', 'ye': 'е',
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е',
    'z': 'з', 'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м',
    'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т',
    'u': 'у', 'f': 'ф', 'y': 'ы', 'w': 'в'
}

def transliterate_to_russian(text: str) -> str:
    """Convert English text to Russian using transliteration (for matching)"""
    text = text.lower()
    result = []
    i = 0
    while i < len(text):
        # Try to match longer patterns first
        matched = False
        for length in [4, 3, 2, 1]:  # Try 4-char, 3-char, 2-char, then 1-char patterns
            if i + length <= len(text):
                substr = text[i:i+length]
                if substr in TRANSLIT_MAP:
                    result.append(TRANSLIT_MAP[substr])
                    i += length
                    matched = True
                    break
        if not matched:
            result.append(text[i])
            i += 1
    return ''.join(result)


class AuthorMatcher:
    """
    Fuzzy matching for author names with cross-language support.
    Handles typos, transliterations, and English/Russian variants.
    """
    
    def __init__(self, author_list: List[str], translation_db_path: Optional[Path] = None):
        """
        Args:
            author_list: List of known Russian author names
            translation_db_path: Path to author_translations.json (optional)
        """
        self.authors = author_list
        self.translation_db = {}
        
        # Load translation database if provided
        if translation_db_path and translation_db_path.exists():
            with open(translation_db_path, 'r', encoding='utf-8') as f:
                self.translation_db = json.load(f)
        else:
            # Build basic translation map from author names
            self._build_translation_map()
    
    def _build_translation_map(self):
        """Build a basic Russian->English translation map from author names"""
        # Common Russian->English name mappings
        common_translations = {
            "Пушкин": "Pushkin",
            "Александр": "Alexander",
            "Лермонтов": "Lermontov", 
            "Михаил": "Mikhail",
            "Ахматова": "Akhmatova",
            "Анна": "Anna",
            "Блок": "Blok",
            "Есенин": "Yesenin",
            "Сергей": "Sergey",
            "Цветаева": "Tsvetaeva",
            "Марина": "Marina",
            "Маяковский": "Mayakovsky",
            "Владимир": "Vladimir",
            "Пастернак": "Pasternak",
            "Борис": "Boris",
            "Тютчев": "Tyutchev",
            "Фёдор": "Fyodor",
            "Фет": "Fet",
            "Афанасий": "Afanasy",
            "Некрасов": "Nekrasov",
            "Николай": "Nikolai",
            "Бродский": "Brodsky",
            "Иосиф": "Joseph",
            "Мандельштам": "Mandelstam",
            "Осип": "Osip",
        }
        
        # For each author, try to create English version
        for author in self.authors:
            if author not in self.translation_db:
                english_name = self._transliterate_to_english(author, common_translations)
                self.translation_db[author] = {
                    "en": english_name,
                    "variants": [english_name]
                }
    
    def _transliterate_to_english(self, russian_name: str, mapping: Dict[str, str]) -> str:
        """Simple transliteration using common name mappings"""
        parts = russian_name.split()
        english_parts = []
        
        for part in parts:
            # Check if we have a direct translation
            if part in mapping:
                english_parts.append(mapping[part])
            else:
                # Keep as-is (will be handled by fuzzy matching)
                english_parts.append(part)
        
        return " ".join(english_parts)
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, remove accents, etc.)"""
        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        # Lowercase
        text = text.lower()
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0.0 to 1.0)"""
        str1_norm = self.normalize_text(str1)
        str2_norm = self.normalize_text(str2)
        
        return SequenceMatcher(None, str1_norm, str2_norm).ratio()
    
    def match_author(self, query: str, threshold: float = 0.6, debug: bool = False) -> Optional[str]:
        """
        Find best matching author name, handling typos and translations.
        
        Args:
            query: User input (can be English, Russian, with typos)
            threshold: Minimum similarity score (0.0-1.0)
            debug: Print debug information
        
        Returns:
            Best matching author name (Russian canonical form) or None
        """
        query_norm = self.normalize_text(query)
        best_match = None
        best_score = threshold
        
        # Check if query is in English (contains only Latin letters)
        is_english = all(ord(c) < 128 or c.isspace() for c in query)
        transliterated_query = None
        
        if is_english:
            # Transliterate English query to Russian for better matching
            transliterated_query = transliterate_to_russian(query_norm)
            if debug:
                print(f"[AuthorMatcher] English query detected, transliterated: '{query}' -> '{transliterated_query}'")
        
        if debug:
            print(f"[AuthorMatcher] Searching for: '{query}' (normalized: '{query_norm}')")
            print(f"[AuthorMatcher] Checking {len(self.authors)} authors with threshold {threshold}")
        
        for author in self.authors:
            # If query was English, check transliterated version against Russian surname
            if transliterated_query:
                author_parts = author.split()
                if author_parts:
                    # Russian names can be "Given Patronymic Surname" or "Surname Given Patronymic"
                    # Try both first and last parts
                    for ru_part in [author_parts[0], author_parts[-1]]:
                        ru_part_norm = self.normalize_text(ru_part)
                        score = self.calculate_similarity(transliterated_query, ru_part_norm)
                        if debug and score > 0.5:
                            print(f"[AuthorMatcher] Transliterated match '{transliterated_query}' vs '{ru_part_norm}': score={score:.3f}")
                        if score > best_score:
                            best_score = score
                            best_match = author
                            if debug:
                                print(f"[AuthorMatcher] NEW BEST (Transliterated): '{author}' ({ru_part}) score={score:.3f}")
            
            # Check Russian name (full)
            score = self.calculate_similarity(query, author)
            if score > best_score:
                best_score = score
                best_match = author
                if debug:
                    print(f"[AuthorMatcher] NEW BEST (Russian full): '{author}' score={score:.3f}")
            
            # Check Russian surname (first word - Russian name format is "Surname Name Patronymic")
            author_parts = author.split()
            if author_parts:
                ru_surname = author_parts[0]
                score = self.calculate_similarity(query, ru_surname)
                if debug and score > 0.6:
                    print(f"[AuthorMatcher] Checking Russian surname '{ru_surname}': score={score:.3f}")
                if score > best_score:
                    best_score = score
                    best_match = author
                    if debug:
                        print(f"[AuthorMatcher] NEW BEST (Russian surname): '{author}' ({ru_surname}) score={score:.3f}")
            
            # Check English translations
            if author in self.translation_db:
                trans_data = self.translation_db[author]
                
                # Check main English name
                if "en" in trans_data:
                    en_name = trans_data["en"]
                    score = self.calculate_similarity(query, en_name)
                    if debug and score > 0.5:
                        print(f"[AuthorMatcher] Checking English full '{en_name}' for '{author}': score={score:.3f}")
                    if score > best_score:
                        best_score = score
                        best_match = author
                        if debug:
                            print(f"[AuthorMatcher] NEW BEST (English full): '{author}' ({en_name}) score={score:.3f}")
                    
                    # Also check English surname (first word for Russian names in English)
                    en_parts = en_name.split()
                    if en_parts:
                        en_surname = en_parts[0]  # First part is usually surname
                        score = self.calculate_similarity(query, en_surname)
                        if debug and score > 0.5:
                            print(f"[AuthorMatcher] Checking English surname '{en_surname}': score={score:.3f}")
                        if score > best_score:
                            best_score = score
                            best_match = author
                            if debug:
                                print(f"[AuthorMatcher] NEW BEST (English surname): '{author}' ({en_surname}) score={score:.3f}")
                
                # Check variants
                for variant in trans_data.get("variants", []):
                    score = self.calculate_similarity(query, variant)
                    if score > best_score:
                        best_score = score
                        best_match = author
                        if debug:
                            print(f"[AuthorMatcher] NEW BEST (Variant): '{author}' ({variant}) score={score:.3f}")
            
            # Check surname only (last word)
            author_surname = author.split()[-1] if ' ' in author else author
            surname_score = self.calculate_similarity(query, author_surname)
            if surname_score > 0.8 and surname_score > best_score:
                best_score = surname_score
                best_match = author
                if debug:
                    print(f"[AuthorMatcher] NEW BEST (Surname): '{author}' ({author_surname}) score={surname_score:.3f}")
        
        if debug:
            print(f"[AuthorMatcher] FINAL RESULT: {best_match} (score={best_score:.3f})")
        
        return best_match
    
    def find_all_matches(self, query: str, threshold: float = 0.5, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find all matching authors with similarity scores.
        
        Args:
            query: User input
            threshold: Minimum similarity score
            top_k: Maximum number of results
        
        Returns:
            List of (author_name, score) tuples, sorted by score
        """
        matches = []
        query_norm = self.normalize_text(query)
        
        for author in self.authors:
            max_score = 0.0
            
            # Check Russian name
            score = self.calculate_similarity(query, author)
            max_score = max(max_score, score)
            
            # Check English translations
            if author in self.translation_db:
                trans_data = self.translation_db[author]
                
                if "en" in trans_data:
                    score = self.calculate_similarity(query, trans_data["en"])
                    max_score = max(max_score, score)
                
                for variant in trans_data.get("variants", []):
                    score = self.calculate_similarity(query, variant)
                    max_score = max(max_score, score)
            
            # Check surname only
            author_surname = author.split()[-1] if ' ' in author else author
            score = self.calculate_similarity(query, author_surname)
            if score > 0.8:  # Higher threshold for surname-only
                max_score = max(max_score, score)
            
            if max_score >= threshold:
                matches.append((author, max_score))
        
        # Sort by score descending
        matches.sort(key=lambda x: -x[1])
        
        return matches[:top_k]
    
    def extract_author_from_query(self, query: str) -> Optional[str]:
        """
        Extract author name from natural language query.
        
        Examples:
            "Find poems like Pushkin" -> "Pushkin"
            "Authors similar to Ahmatova" -> "Akhmatova"
            "Show me Lermontov's work" -> "Lermontov"
        """
        query_lower = query.lower()
        
        # Common query patterns
        patterns = [
            "like ", "similar to ", "by ", "from ", "about ",
            "похож на ", "автор ", "стихи ", "поэзия "
        ]
        
        # Try to extract author name from context
        for pattern in patterns:
            if pattern in query_lower:
                # Get text after pattern
                idx = query_lower.index(pattern) + len(pattern)
                remaining = query[idx:].strip()
                
                # Take first few words (author name is usually 1-3 words)
                words = remaining.split()[:3]
                for i in range(len(words), 0, -1):
                    candidate = " ".join(words[:i])
                    # Remove trailing punctuation
                    candidate = candidate.rstrip('.,!?;:')
                    
                    # Try to match
                    matched = self.match_author(candidate, threshold=0.5)
                    if matched:
                        return matched
        
        # If no pattern found, try matching the whole query
        # (in case user just typed an author name)
        if len(query.split()) <= 5:  # Short queries likely to be just names
            matched = self.match_author(query, threshold=0.5)
            if matched:
                return matched
        
        return None
    
    def get_english_name(self, russian_author: str) -> str:
        """Get English translation of Russian author name"""
        if russian_author in self.translation_db:
            return self.translation_db[russian_author].get("en", russian_author)
        return russian_author
    
    def get_russian_name(self, english_author: str) -> Optional[str]:
        """Get Russian name from English input"""
        # Check all Russian authors for matching English name
        for russian_name, trans_data in self.translation_db.items():
            if english_author.lower() == trans_data.get("en", "").lower():
                return russian_name
            if english_author.lower() in [v.lower() for v in trans_data.get("variants", [])]:
                return russian_name
        
        # Fallback to fuzzy matching
        return self.match_author(english_author)


def build_author_translation_database(author_list: List[str], output_path: Path):
    """
    Build and save author translation database.
    This can be run once to create the translation file.
    """
    matcher = AuthorMatcher(author_list)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(matcher.translation_db, f, ensure_ascii=False, indent=2)
    
    print(f"Saved translation database to {output_path}")
    print(f"Total authors: {len(matcher.translation_db)}")
