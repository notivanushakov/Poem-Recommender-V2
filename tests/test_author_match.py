# Quick test for author matching
from utils.author_matcher import AuthorMatcher
import json

# Load authors from author map
with open('models/author_map.json', 'r', encoding='utf-8') as f:
    author_map = json.load(f)

authors = [a['author'] for a in author_map]

print(f"Loaded {len(authors)} authors")
print(f"\nFirst few authors: {authors[:5]}")

# Create matcher
matcher = AuthorMatcher(authors)

# Test queries
test_queries = [
    "Mayakovsky",
    "mayakovsky", 
    "Маяковский",
    "маяковский",
    "маяковскго",  # typo
    "Pushkin",
    "Akhmatova"
]

print("\n" + "="*60)
print("TESTING AUTHOR MATCHING")
print("="*60)

for query in test_queries:
    print(f"\n{'='*60}")
    result = matcher.match_author(query, debug=True)
    print(f"Query: '{query}' => Result: '{result}'")
