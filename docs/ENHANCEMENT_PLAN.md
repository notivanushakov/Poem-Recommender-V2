# LLM-Powered RAG Enhancement Plan

## Current Problems
1. ❌ Rule-based intent detection fails with typos or varied phrasing
2. ❌ Cannot search Russian authors using English names (e.g., "Pushkin" vs "Пушкин")
3. ❌ Cannot compare English poem queries to Russian poem database
4. ❌ No semantic understanding - just pattern matching
5. ❌ No explanations of WHY poems are similar (lack of interpretability)

## Proposed Solution: LLM with Function Calling + RAG

### Architecture Overview

```
User Query (any language, typos OK)
    ↓
LLM Agent (GPT-4/Claude/Llama)
    ↓
┌─────────────────────────────────────┐
│ 1. Translate/normalize query        │
│ 2. Understand intent & context      │
│ 3. Decide which function(s) to call │
│ 4. Extract parameters (author name, │
│    poem text, etc.)                 │
└─────────────────────────────────────┘
    ↓
Function Calling
    ↓
┌──────────────┬──────────────┬──────────────┐
│ search_poems │search_authors│get_author_bio│
└──────────────┴──────────────┴──────────────┘
    ↓
Retrieve Results (embeddings + metadata)
    ↓
LLM Post-Processing
    ↓
┌─────────────────────────────────────┐
│ 1. Analyze retrieved poems/authors  │
│ 2. Explain similarities             │
│ 3. Provide literary context         │
│ 4. Format response naturally        │
└─────────────────────────────────────┘
    ↓
User-friendly Response
```

## Implementation Plan

### Phase 1: LLM Integration Layer
**Duration: 2-3 days**

#### 1.1 Create LLM Service Module (`utils/llm_service.py`)
```python
from openai import OpenAI  # or anthropic, or ollama for local
import json

class LLMAgent:
    def __init__(self, model="gpt-4o-mini"):  # or "claude-3-5-sonnet"
        self.client = OpenAI()
        self.model = model
        
    def process_query(self, user_query: str, conversation_history: list = None):
        """
        Main entry point: takes user query, returns structured response
        with function calls and explanations
        """
        pass
```

**Tools to define:**
- `search_poems_by_content(query: str, k: int)` - semantic poem search
- `search_authors_by_name(author_name: str, k: int)` - author similarity
- `search_poems_by_author(author_name: str, k: int)` - get author's poems
- `translate_author_name(name: str, target_lang: str)` - cross-language names

#### 1.2 Add Author Name Translation Database
Create `data/author_translations.json`:
```json
{
  "Пушкин Александр Сергеевич": {
    "en": "Alexander Pushkin",
    "variants": ["Pushkin", "A.S. Pushkin", "Aleksandr Pushkin"]
  },
  "Ахматова Анна Андреевна": {
    "en": "Anna Akhmatova",
    "variants": ["Akhmatova", "A.A. Akhmatova"]
  }
}
```

**Auto-generate this from existing data + Wikipedia API**

### Phase 2: Cross-Language Query Support
**Duration: 1-2 days**

#### 2.1 Query Translation Pipeline
```python
# utils/translation.py
from deep_translator import GoogleTranslator

def translate_query_if_needed(query: str, target_lang: str = "ru") -> dict:
    """
    Detect query language and translate if needed
    Returns: {
        "original": str,
        "translated": str,
        "detected_lang": str
    }
    """
```

#### 2.2 Multilingual Embedding Search
Your current model `paraphrase-multilingual-MiniLM-L12-v2` already supports cross-language!
- English query → embedding → matches Russian poems ✅
- Just need to ensure query is properly embedded

**Test**: "Find poems about love and loss" should match Russian poems about любовь и потеря

### Phase 3: Function Calling Implementation
**Duration: 2-3 days**

#### 3.1 Define OpenAI Function Schemas
```python
# utils/function_schemas.py
FUNCTION_SCHEMAS = [
    {
        "name": "search_poems_by_content",
        "description": "Search for poems similar to given text or theme. Use when user provides poem text, describes themes, or asks for similar poems.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The poem text or thematic description to search for"
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_similar_authors",
        "description": "Find authors with similar writing style to a given author. Use when user asks about authors similar to X.",
        "parameters": {
            "type": "object",
            "properties": {
                "author_name": {
                    "type": "string",
                    "description": "Name of the author (in any language, with typos OK)"
                },
                "k": {"type": "integer", "default": 8}
            },
            "required": ["author_name"]
        }
    },
    {
        "name": "get_author_poems",
        "description": "Retrieve poems by a specific author",
        "parameters": {
            "type": "object",
            "properties": {
                "author_name": {"type": "string"},
                "k": {"type": "integer", "default": 5}
            },
            "required": ["author_name"]
        }
    }
]
```

#### 3.2 New Backend Endpoint: `/chat/llm`
```python
@app.post("/chat/llm")
async def chat_with_llm(q: ChatQuery):
    """
    LLM-powered chat endpoint with function calling
    """
    from utils.llm_service import LLMAgent
    
    agent = LLMAgent()
    
    # Step 1: LLM decides what to do
    response = agent.process_query(q.text)
    
    # Step 2: Execute function calls
    results = []
    for func_call in response.function_calls:
        if func_call.name == "search_poems_by_content":
            results.append(search_poems_internal(**func_call.args))
        elif func_call.name == "search_similar_authors":
            results.append(search_authors_internal(**func_call.args))
    
    # Step 3: LLM analyzes results and generates explanation
    final_response = agent.generate_explanation(
        query=q.text,
        results=results
    )
    
    return {
        "query": q.text,
        "intent": response.intent,
        "results": results,
        "explanation": final_response.explanation,
        "literary_analysis": final_response.analysis
    }
```

### Phase 4: Explainable AI - Literary Analysis
**Duration: 3-4 days**

#### 4.1 Thematic Analysis System
```python
# utils/literary_analysis.py

def analyze_poem_similarities(query_poem: str, similar_poems: list, llm_client):
    """
    Uses LLM to provide literary analysis of WHY poems are similar
    """
    prompt = f"""
    You are a literary critic specializing in Russian poetry.
    
    Query poem:
    {query_poem}
    
    Similar poems found:
    {format_poems(similar_poems)}
    
    Analyze and explain:
    1. Common themes (love, nature, death, patriotism, etc.)
    2. Stylistic similarities (meter, rhyme scheme, imagery)
    3. Emotional tone
    4. Historical/cultural context
    5. Why the embedding model found these similar
    
    Provide scholarly but accessible explanation.
    """
    
    return llm_client.generate(prompt)
```

#### 4.2 Author Style Comparison
```python
def compare_author_styles(author1: str, author2: str, sample_poems: dict, llm_client):
    """
    Deep literary comparison between authors
    """
    prompt = f"""
    Compare the writing styles of {author1} and {author2}.
    
    Sample poems provided:
    {sample_poems}
    
    Analyze:
    - Thematic preferences
    - Linguistic choices
    - Historical period influence
    - Emotional range
    - Technical mastery (meter, form)
    """
    
    return llm_client.generate(prompt)
```

### Phase 5: Enhanced Frontend
**Duration: 1-2 days**

#### 5.1 Update Streamlit UI
Add new display components:
- **Explanation panel** showing literary analysis
- **Theme tags** extracted by LLM
- **Cross-language indicator** (showing original + translated query)
- **Confidence scores** with LLM reasoning

#### 5.2 Conversation Memory
Store conversation history to allow follow-up questions:
- "Tell me more about the first one"
- "Compare poems 2 and 5"
- "What about Akhmatova's later works?"

## Technology Stack Additions

### Required Packages
```bash
pip install openai  # or anthropic for Claude
pip install langchain  # optional, for easier orchestration
pip install langchain-community
pip install deep-translator  # for translation
pip install langdetect  # language detection
pip install tiktoken  # token counting for OpenAI
```

### LLM Options

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **GPT-4o-mini** | Fast, cheap, good function calling | Requires API key | ~$0.15-0.60/1M tokens |
| **GPT-4o** | Best quality, excellent reasoning | More expensive | ~$2.50-10/1M tokens |
| **Claude 3.5 Sonnet** | Great literary analysis, long context | API key needed | ~$3-15/1M tokens |
| **Llama 3.1 70B (local)** | Free, private, good performance | Needs GPU, slower | Free (hardware cost) |
| **Ollama (local)** | Free, easy setup, privacy | Lower quality | Free |

**Recommendation for academic project**: Start with **GPT-4o-mini** (cheap, fast) or **Ollama** (free, local)

## Validation Strategy

### Test Cases

#### 1. Typo Handling
```
Query: "Find autors like Puskin" (typos in "authors" and "Pushkin")
Expected: Should understand and find Pushkin-like authors
```

#### 2. Cross-Language Author Search
```
Query: "Show me poems by Pushkin" (English name)
Expected: Find "Пушкин Александр Сергеевич" poems
```

#### 3. English Poem → Russian Matches
```
Query: "I wandered lonely as a cloud..." (Wordsworth)
Expected: Find Russian romantic nature poems
```

#### 4. Complex Multi-Intent Query
```
Query: "Compare Pushkin and Lermontov's poems about freedom"
Expected: 
- Search poems by both authors with "freedom" theme
- Provide comparative literary analysis
```

#### 5. Follow-up Conversation
```
User: "Find poems like Akhmatova"
Bot: [returns results]
User: "What about her love poetry specifically?"
Expected: Context-aware refinement
```

### Evaluation Metrics

1. **Intent Classification Accuracy**: Manual evaluation on 100 test queries
2. **Cross-language Retrieval**: Precision@10 for English→Russian queries
3. **Explanation Quality**: Human evaluation (coherent, insightful, accurate)
4. **Response Time**: Should be < 5 seconds for query + explanation
5. **User Satisfaction**: Qualitative feedback from test users

### A/B Testing Plan
- **Control**: Current rule-based system
- **Treatment**: LLM-powered system
- **Metrics**: Success rate, user preference, time-to-result

## Implementation Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| 1 | Phase 1: LLM integration, function schemas | Working LLM agent with function calling |
| 2 | Phase 2: Cross-language support, author translation DB | English queries work on Russian data |
| 3 | Phase 3: Enhanced backend endpoints | New `/chat/llm` endpoint |
| 4 | Phase 4: Literary analysis system | Explainable similarity responses |
| 5 | Phase 5: Frontend updates, testing | Complete working system |
| 6 | Validation, documentation, presentation | Project report + demo |

## Cost Estimation

### OpenAI API (GPT-4o-mini)
- Average query: ~2000 tokens (prompt + completion)
- Cost per query: ~$0.0004
- 1000 queries for testing: ~$0.40
- **Total for project: < $5**

### Alternative: Free Local LLM
- Use Ollama with Llama 3.1 8B or Mistral
- Zero API cost
- Slower but sufficient for academic demo

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucinations in literary analysis | Medium | Fact-check against source poems, add disclaimers |
| API costs exceed budget | Low | Set rate limits, use caching, fallback to local LLM |
| Translation quality issues | Medium | Use human validation for common author names |
| Increased latency | Medium | Cache common queries, async processing, streaming |
| Over-reliance on LLM | Low | Keep rule-based fallback for simple queries |

## Success Criteria

✅ **Must Have:**
1. Handle typos in author names (>90% accuracy)
2. Cross-language author search works
3. Provides basic explanation of similarity

✅ **Should Have:**
4. Literary analysis explains themes/style
5. Multi-turn conversation support
6. Response time < 5 seconds

✅ **Nice to Have:**
7. Author biography integration
8. Historical context for poems
9. Comparative analysis between multiple poems

## Next Steps for Validation

1. **Create prototype** with minimal LLM integration (1-2 days)
2. **Test with 20 sample queries** covering all problem cases
3. **Measure accuracy** vs current system
4. **Demo to stakeholders** (professor/classmates)
5. **Iterate based on feedback**
6. **Full implementation** if validated

---

## Sample Queries to Test

```python
test_queries = [
    # Typos
    "Finde authros liek Puschkin",
    "Ahmatova pomes",
    
    # Cross-language
    "Show me Pushkin's romantic poems",
    "Authors similar to Akhmatova",
    
    # English poem input
    "Find Russian poems like: The woods are lovely, dark and deep...",
    
    # Complex analysis
    "Compare Pushkin and Lermontov's approaches to freedom",
    "What makes Tsvetaeva unique among Silver Age poets?",
    
    # Multi-intent
    "I want poems about autumn by Pushkin and similar authors",
    
    # Conversation
    "Tell me about Блок",  # Follow-up: "His symbolist period specifically"
]
```

## Questions for You

Before I start implementation, please confirm:

1. **LLM choice**: OpenAI (cheap, easy) or local Ollama (free, private)?
2. **Priority**: What's most important - cross-language, explanations, or typo handling?
3. **Scope**: Full implementation or proof-of-concept first?
4. **Timeline**: How soon do you need this? (affects depth of implementation)
5. **Evaluation**: Do you need formal metrics or just demo-quality?

Let me know and I can start coding! 🚀
