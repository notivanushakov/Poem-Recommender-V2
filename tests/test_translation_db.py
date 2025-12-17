# Debug translation database
from utils.author_matcher import AuthorMatcher
import json

with open('models/author_map.json', 'r', encoding='utf-8') as f:
    author_map = json.load(f)

authors = [a['author'] for a in author_map]
matcher = AuthorMatcher(authors)

print("Translation database sample:")
for i, (russian, trans) in enumerate(list(matcher.translation_db.items())[:10]):
    print(f"\n{i+1}. Russian: {russian}")
    print(f"   English: {trans.get('en', 'N/A')}")
    print(f"   Variants: {trans.get('variants', [])}")

# Find Mayakovsky specifically
print("\n" + "="*60)
print("Looking for Маяковский in translation DB:")
for russian, trans in matcher.translation_db.items():
    if "Маяковский" in russian or "Mayakovsky" in trans.get('en', ''):
        print(f"\nRussian: {russian}")
        print(f"English: {trans.get('en', 'N/A')}")
        print(f"Variants: {trans.get('variants', [])}")
