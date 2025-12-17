"""Test script to verify all fixes are working"""
import requests
import json

API_URL = "http://localhost:8000"

def test_bilingual_author_names():
    """Test Issue 1: Author names should be bilingual in English UI"""
    print("\n=== TEST 1: Bilingual Author Names ===")
    
    # Test with chat/llm endpoint
    response = requests.post(
        f"{API_URL}/chat/llm",
        json={"text": "Give me someone like Pushkin", "k": 3, "language": "en"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Query Author: {data.get('query_author')}")
        
        results = data.get('results', [])
        if results:
            first_author = results[0]
            author_name = first_author.get('author')
            author_ru = first_author.get('author_ru')
            
            print(f"First Result Author: {author_name}")
            print(f"Author RU: {author_ru}")
            
            # Check if bilingual format
            if "(" in author_name and ")" in author_name:
                print("✓ PASS: Author name is in bilingual format")
            else:
                print("✗ FAIL: Author name NOT in bilingual format")
                
            # Check sample poems
            samples = first_author.get('sample_poems', [])
            if samples:
                sample_author = samples[0].get('author')
                sample_author_display = samples[0].get('author_display')
                print(f"Sample Author: {sample_author}")
                print(f"Sample Author Display: {sample_author_display}")
                
                if sample_author_display and "(" in sample_author_display:
                    print("✓ PASS: Sample poem author is bilingual")
                else:
                    print("✗ FAIL: Sample poem author NOT bilingual")
        else:
            print("✗ No results returned")
    else:
        print(f"✗ FAIL: {response.text}")

def test_poem_translation():
    """Test Issue 2: Poem translation endpoint"""
    print("\n=== TEST 2: Poem Translation ===")
    
    test_poem = """Я вас любил: любовь еще, быть может,
В душе моей угасла не совсем;
Но пусть она вас больше не тревожит;
Я не хочу печалить вас ничем."""
    
    response = requests.post(
        f"{API_URL}/translate/poem",
        json={"poem_id": "test_123", "poem_text": test_poem}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        translation = data.get('translation', '')
        print(f"Translation: {translation[:200]}...")
        
        # Check if it's in English
        russian_chars = any(char in translation for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        if not russian_chars and len(translation) > 10:
            print("✓ PASS: Translation is in English")
        else:
            print("✗ FAIL: Translation appears to be in Russian or empty")
    else:
        print(f"✗ FAIL: {response.text}")

def test_explanation_language():
    """Test Issue 3: Explanations should be in English when language=en"""
    print("\n=== TEST 3: Explanation Language ===")
    
    # First get some poems
    search_response = requests.post(
        f"{API_URL}/search/poems",
        json={"text": "love", "k": 1, "language": "en"}
    )
    
    if search_response.status_code == 200:
        results = search_response.json().get('results', [])
        if results:
            poem = results[0]
            poem_id = poem['poem_id']
            
            # Request explanation
            exp_response = requests.post(
                f"{API_URL}/explain/poem",
                json={
                    "query_text": "love poems",
                    "poem_id": poem_id,
                    "similarity_score": 0.9,
                    "language": "en"
                }
            )
            
            print(f"Status: {exp_response.status_code}")
            if exp_response.status_code == 200:
                data = exp_response.json()
                explanation = data.get('explanation', '')
                print(f"Explanation preview: {explanation[:300]}...")
                
                # Check if it's in English (rough check)
                russian_word_count = sum(1 for word in explanation.split() 
                                        if any(char in word.lower() for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'))
                english_word_count = sum(1 for word in explanation.split() 
                                        if any(char in word.lower() for char in 'abcdefghijklmnopqrstuvwxyz'))
                
                print(f"Russian words: {russian_word_count}, English words: {english_word_count}")
                
                if english_word_count > russian_word_count * 2:
                    print("✓ PASS: Explanation is primarily in English")
                else:
                    print("✗ FAIL: Explanation appears to be in Russian")
                
                # Check if complete (not truncated)
                if len(explanation) > 100 and not explanation.endswith('...'):
                    print("✓ PASS: Explanation appears complete")
                else:
                    print("⚠ WARNING: Explanation might be truncated")
            else:
                print(f"✗ FAIL: {exp_response.text}")
        else:
            print("✗ No poems found")
    else:
        print(f"✗ FAIL: Search failed - {search_response.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Poetry Recommender Fixes")
    print("=" * 60)
    
    try:
        test_bilingual_author_names()
        test_poem_translation()
        test_explanation_language()
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to API. Make sure backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
