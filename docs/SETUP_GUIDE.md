# LLM-Enhanced Poem Recommender - Setup & Usage Guide

## 🎯 What's New

This enhanced version adds **LLM-powered intelligence** to the poem recommender:

✅ **Typo Tolerance**: "Puskin" → automatically understands as "Pushkin"  
✅ **Cross-Language**: Search "Pushkin" (English) → finds "Пушкин" (Russian) poems  
✅ **Smart Intent Detection**: Understands varied query phrasings  
✅ **On-Demand Explanations**: Click "Explain Similarity" for literary analysis  
✅ **Provider Flexibility**: Easy switch between Ollama (free) ↔ GPT ↔ Claude ↔ Grok

## 🚀 Quick Start

### Option 1: Local Ollama (Recommended - FREE)

1. **Install Ollama** (if not already installed):
   ```powershell
   # Windows: Download from https://ollama.ai
   # Or use winget:
   winget install Ollama.Ollama
   ```

2. **Pull a model**:
   ```powershell
   ollama pull llama3.1
   # Or for better quality (requires more RAM):
   # ollama pull llama3.1:70b
   ```

3. **Configure environment**:
   ```powershell
   # Create .env file
   Copy-Item .env.example .env
   
   # Edit .env and set:
   # LLM_PROVIDER=ollama
   # LLM_MODEL=llama3.1
   ```

4. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Run the system**:
   ```powershell
   # Terminal 1: Start backend
   python -m uvicorn backend.app:app --reload --port 8000
   
   # Terminal 2: Start frontend
   streamlit run frontend/frontend.py
   ```

6. **Test it**:
   - Open browser at `http://localhost:8501`
   - Enable "Use AI-powered search" in sidebar
   - Try: "Find autors like Puskin" (note the typos!)
   - Try: "Show me Pushkin's poems" (English name for Russian author)

### Option 2: OpenAI GPT (Paid but Cheap)

1. **Get API key**: https://platform.openai.com/api-keys

2. **Configure**:
   ```powershell
   # Edit .env:
   # LLM_PROVIDER=openai
   # LLM_MODEL=gpt-4o-mini
   # OPENAI_API_KEY=sk-...
   ```

3. **Install & run** (same as Option 1, steps 4-6)

**Cost**: ~$0.15-0.60 per 1M tokens (very cheap for this use case)

### Option 3: Anthropic Claude (Best Quality)

1. **Get API key**: https://console.anthropic.com/

2. **Configure**:
   ```powershell
   # Edit .env:
   # LLM_PROVIDER=anthropic
   # LLM_MODEL=claude-3-5-sonnet-20241022
   # ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Install & run** (same as Option 1, steps 4-6)

**Cost**: ~$3-15 per 1M tokens (higher quality literary analysis)

### Option 4: xAI Grok

1. **Get API key**: https://x.ai/

2. **Configure**:
   ```powershell
   # Edit .env:
   # LLM_PROVIDER=xai
   # LLM_MODEL=grok-beta
   # XAI_API_KEY=xai-...
   ```

3. **Install & run** (same as Option 1, steps 4-6)

## 🧪 Testing the New Features

### Test 1: Typo Handling
```
Query: "Find autors liek Puschkin"
Expected: Should understand and find authors similar to Пушкин
```

### Test 2: Cross-Language Author Names
```
Query: "Show me poems by Pushkin"
Expected: Finds "Пушкин Александр Сергеевич" poems
```

### Test 3: English Poem → Russian Matches
```
Query: "I wandered lonely as a cloud, that floats on high..."
Expected: Finds similar Russian romantic poems
```

### Test 4: Varied Phrasings
```
Queries:
- "Similar authors to Akhmatova"
- "Who writes like Ahmatova?"
- "Authors similar to Anna Akhmatova"
All should work despite different phrasings and typos!
```

### Test 5: Literary Explanations
```
1. Search for "authors like Pushkin"
2. Click "🔍 Explain Similarity" button (visible immediately next to each result)
3. Should get detailed literary analysis explaining WHY they're similar
4. Switch language to Русский in sidebar → re-click → analysis now in Russian!
```

### Test 6: Language-Aware Explanations
```
1. Select "Русский" in sidebar language dropdown
2. Search: "найди стихи похожие на Пушкина"
3. Click "🔍 Объяснить сходство" → Analysis in Russian
4. Switch to "English" → Re-click → Analysis in English
```

## 🎨 UI Features

### Sidebar Controls

**Search Mode:**
- ☑️ **Use AI-powered search**: Enable LLM (handles typos, cross-language)
- ☐ **Force author search**: Always search authors (bypass intent detection)
- ☐ **Force poem search**: Always search poems

**Settings:**
- **Top k results**: Number of results to return (1-20)
- **Language**: English / Русский

### Chat Interface

**Input Types:**
1. **Author search**: "Find authors like Pushkin", "похожих на Маяковского"
2. **Poem search**: "Show me poems about love and nature"
3. **Specific author poems**: "Pushkin's romantic poems"

**Results Display:**
- **Poem results**: Title, author, score — with **🔍 Explain Similarity** button visible next to each
- **Author results**: Author name, poem count, score — with **🔍 Explain Similarity** button visible
- Click poem title expander to see full text
- Explanations appear below the result after clicking button

### AI Features

**Visible in UI:**
- 🤖 **AI Reasoning**: Why the LLM chose this search type (in expander)
- ✓ **Author Resolution**: Shows when typo/translation happened ("Mayakovsky → Маяковский Владимир Владимирович")
- 📝 **Literary Analysis**: On-demand explanations with themes
- 🌐 **Language-Aware**: Explanations generated in your UI language (toggle EN/RU in sidebar)

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│         Frontend (Streamlit)                    │
│  - User input                                   │
│  - Display results                              │
│  - Explanation buttons                          │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│         Backend API (FastAPI)                   │
│                                                 │
│  /chat/llm          - LLM-powered search       │
│  /search/poems      - Direct poem search       │
│  /search/authors    - Direct author search     │
│  /explain/poem      - Get poem explanation     │
│  /explain/author    - Get author explanation   │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│      LLM Agent (utils/llm_agent.py)            │
│  - Intent detection via function calling        │
│  - Author name resolution                       │
│  - Literary analysis generation                 │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│   LLM Provider (utils/llm_provider.py)         │
│  - Ollama / OpenAI / Claude / Grok             │
│  - Interoperable abstraction layer             │
└─────────────────────────────────────────────────┘
```

## 🔧 Troubleshooting

### Problem: "LLM features will be disabled"

**Cause**: LLM provider not configured or not accessible

**Solution**:
```powershell
# For Ollama:
1. Check Ollama is running: ollama list
2. Check model is available: ollama list
3. Test Ollama: ollama run llama3.1 "Hello"

# For OpenAI/Claude/Grok:
1. Verify API key in .env file
2. Check API key is valid
3. Ensure you have credits/quota
```

### Problem: Explanation button does nothing

**Cause**: LLM provider not configured or poem text missing

**Solution**:
1. Check backend logs for errors
2. Ensure `poems.parquet` file exists with text column
3. Verify LLM provider is working (see above)

### Problem: Author names not resolving

**Cause**: Author matcher not finding matches

**Solution**:
1. Check backend logs for author resolution
2. Try more specific names (e.g., "Pushkin" vs "Alexander Pushkin")
3. Threshold is 0.6 - very different spellings might not match

### Problem: Slow responses with Ollama

**Cause**: Large model on CPU

**Solutions**:
- Use smaller model: `ollama pull llama3.1` (not :70b)
- Use GPU if available: Install with GPU support
- Switch to cloud provider (OpenAI gpt-4o-mini is very fast)

## 📝 API Endpoints

### `/chat/llm` (POST)
LLM-powered intelligent search with typo tolerance and cross-language support.

**Request:**
```json
{
  "text": "Find autors like Puskin",
  "k": 10
}
```

**Response:**
```json
{
  "query_author": "Pushkin",
  "results": [...],
  "intent": "author_search",
  "llm_reasoning": "User is asking for similar authors...",
  "author_resolution": {
    "original": "Puskin",
    "resolved": "Пушкин Александр Сергеевич"
  }
}
```

### `/explain/poem` (POST)
Generate literary explanation for poem similarity (supports language parameter).

**Request:**
```json
{
  "query_text": "original search query",
  "poem_id": 12345,
  "similarity_score": 0.87,
  "language": "ru"
}
```

**Response:**
```json
{
  "explanation": "Это стихотворение разделяет несколько ключевых тем...",
  "themes": ["Love", "Nature", "Melancholy"],
  "similarity_score": 0.87,
  "poem_title": "...",
  "poem_author": "..."
}
```

### `/explain/author` (POST)
Generate literary explanation for author similarity (supports language parameter).

**Request:**
```json
{
  "query_author": "Пушкин Александр Сергеевич",
  "similar_author": "Лермонтов Михаил Юрьевич",
  "similarity_score": 0.92,
  "sample_poem_ids": [123, 456, 789],
  "language": "en"
}
```

**Response:**
```json
{
  "explanation": "Both authors belong to the Russian Romantic movement...",
  "query_author": "...",
  "similar_author": "...",
  "similarity_score": 0.92
}
```

## 🔄 Switching LLM Providers

Just edit `.env` file:

```bash
# Switch to GPT
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# OR switch to Claude
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...

# OR switch back to Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
```

**No code changes needed!** Restart backend and it works.

## 📚 Code Structure

```
poem_recommender_llms/
├── backend/
│   └── app.py                 # FastAPI server with new endpoints
├── frontend/
│   └── frontend.py            # Streamlit UI with explanation buttons
├── utils/
│   ├── llm_provider.py        # Interoperable LLM abstraction
│   ├── llm_agent.py           # Agent for intent detection & explanations
│   ├── author_matcher.py      # Fuzzy matching with cross-language support
│   └── intent.py              # Old rule-based (kept as fallback)
├── .env.example               # Configuration template
├── requirements.txt           # Updated dependencies
└── SETUP_GUIDE.md             # This file
```

## 🎓 Academic Context

This is an enhancement to a TU Darmstadt project on embeddings, adding:

1. **Explainable AI**: Literary analysis explains why embeddings matched
2. **Robustness**: Handles real-world queries with typos and variations
3. **Cross-Language**: Leverages multilingual embeddings properly
4. **User Experience**: On-demand explanations keep searches fast

Perfect for demonstrating:
- Semantic embeddings in practice
- LLM function calling architecture
- Explainable AI in recommendation systems
- Cross-language information retrieval

## 💡 Tips for Best Results

1. **For typos**: LLM mode handles them automatically
2. **For English queries on Russian data**: Works out of the box (multilingual embeddings)
3. **For explanations**: Works best with longer poems (more context)
4. **For speed**: Use Ollama with smaller models or GPT-4o-mini
5. **For quality**: Use Claude or GPT-4o for literary analysis

## 📧 Support

If you encounter issues:

1. Check backend logs for detailed error messages
2. Verify `.env` configuration
3. Test LLM provider independently
4. Try fallback mode (disable "Use AI-powered search")

---

**Happy poetry exploring! 📖✨**
