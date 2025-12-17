# utils/intent.py
import re
from typing import Literal, Optional, Dict, List

Intent = Literal["author_search", "poem_search", "unknown"]

def detect_intent(text: str, known_authors: Optional[List[str]] = None) -> Intent:
    """
    Very simple rule-based intent detection:
    - If text contains known author name (exact or substring match, case-insensitive) -> author_search
    - If text has many line breaks or length > 250 chars -> poem_search
    - If text includes the word 'author' or 'автор' and a name -> author_search
    - If text includes 'similar'/'похожие' likely comparing -> check for author or poem
    """
    if not text or not text.strip():
        return "unknown"
    t = text.strip()

    # if user pasted a multi-line poem -> poem search
    if t.count("\n") >= 2 or len(t) > 250:
        return "poem_search"

    # keywords that hint author intent
    if re.search(r"\b(author|автор|похож|similar|like)\w*\b", t, flags=re.I):
        # if known_authors provided, check for names
        if known_authors:
            found = find_author_in_text(t, known_authors)
            if found:
                return "author_search"
        # otherwise ambiguous -> default to author_search if 'author' word present
        if re.search(r"\b(author|автор)\w*\b", t, flags=re.I):
            return "author_search"

    # check if exact known author appears
    if known_authors:
        found = find_author_in_text(t, known_authors)
        if found:
            return "author_search"

    # fallback: short queries are likely author name or title; treat as author search first
    if len(t.split()) <= 5:
        return "author_search"

    return "poem_search"

def find_author_in_text(text: str, known_authors: List[str]) -> Optional[str]:
    """
    Case-insensitive substring match over known_authors.
    Returns matched author (first) or None.
    Checks both: if author name is in text, OR if any word from text matches author surname.
    Supports fuzzy matching for Russian declensions (падежи).
    """
    t = text.lower()
    
    def stem_russian(word: str) -> str:
        """Simple Russian stemming - remove common endings for fuzzy matching"""
        # Remove common case endings
        for ending in ['ова', 'ову', 'овой', 'овы', 'ина', 'ину', 'иной', 'ины', 
                       'ева', 'еву', 'евой', 'евы', 'а', 'у', 'ой', 'ы', 'е', 'ё']:
            if len(word) > 4 and word.endswith(ending):
                return word[:-len(ending)]
        return word
    
    # sort authors by length descending to prefer longer matches
    for a in sorted(known_authors, key=lambda x: -len(x)):
        a_lower = a.lower()
        # Check if full author name appears in text
        if a_lower in t:
            return a
        # Check if any significant word from text appears in author name (surname matching)
        words = [w.strip('.,!?;:') for w in t.split() if len(w.strip('.,!?;:')) > 3]
        for word in words:
            # Direct match
            if word in a_lower:
                return a
            # Fuzzy match with stemming for Russian names
            word_stem = stem_russian(word)
            for author_word in a_lower.split():
                author_stem = stem_russian(author_word)
                if len(word_stem) > 3 and word_stem in author_stem:
                    return a
                if len(author_stem) > 3 and author_stem in word_stem:
                    return a
    return None
