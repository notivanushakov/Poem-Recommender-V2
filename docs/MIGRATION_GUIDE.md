# Migration Guide: Adding LLM Features to Existing System

This guide helps you upgrade your existing poem recommender with LLM capabilities.

## ✅ What Changed

### New Files Added
```
utils/
  ├── llm_provider.py      # LLM abstraction layer (NEW)
  ├── llm_agent.py         # Intent detection & explanations (NEW)
  └── author_matcher.py    # Fuzzy author matching (NEW)

backend/app.py             # Updated with new endpoints
frontend/frontend.py       # Updated with explanation buttons
requirements.txt           # Added LLM dependencies
.env.example              # Configuration template (NEW)
```

### Existing Files Modified
1. **backend/app.py**:
   - Added imports for LLM utilities
   - New global variables: `llm_agent`, `explanation_agent`, `author_matcher`
   - Modified `load_resources()` to initialize LLM components
   - New endpoints: `/chat/llm`, `/explain/poem`, `/explain/author`
   - Old `/chat` endpoint kept for backward compatibility

2. **frontend/frontend.py**:
   - Added session state for LLM toggle and explanations cache
   - New UI controls: "Use AI-powered search" checkbox
   - New API functions: `call_chat_llm()`, `call_explain_poem()`, `call_explain_author()`
   - Updated result display with "Explain Similarity" buttons
   - Shows LLM reasoning and author resolution

3. **requirements.txt**:
   - Added: `openai>=1.0.0`, `anthropic>=0.7.0`

### Nothing Broken
- ✅ Old `/chat` endpoint still works (rule-based fallback)
- ✅ All existing `/search/poems` and `/search/authors` work unchanged
- ✅ Can toggle LLM features on/off in UI
- ✅ System works without LLM if not configured (graceful degradation)

## 🔄 Step-by-Step Migration

### Step 1: Backup Current Code
```powershell
# Create backup
Copy-Item -Recurse . ..\poem_recommender_backup
```

### Step 2: Install New Dependencies
```powershell
pip install openai anthropic
# Or just:
pip install -r requirements.txt
```

### Step 3: Setup Ollama (Free Option)
```powershell
# Install Ollama
winget install Ollama.Ollama

# Pull model
ollama pull llama3.1

# Verify it's running
ollama list
```

### Step 4: Configure Environment
```powershell
# Copy template
Copy-Item .env.example .env

# .env content (for Ollama):
# LLM_PROVIDER=ollama
# LLM_MODEL=llama3.1
```

### Step 5: Test Backend
```powershell
# Start backend
python -m uvicorn backend.app:app --reload --port 8000

# Check logs for:
# "LLM agents initialized with provider: ollama" ✅
# Or: "LLM features will be disabled" ⚠️ (need to configure)
```

### Step 6: Test Frontend
```powershell
# Start frontend
streamlit run frontend/frontend.py

# Check sidebar for:
# ☑️ "Use AI-powered search" checkbox (should appear)
```

### Step 7: Test LLM Features
1. Enable "Use AI-powered search" in sidebar
2. Try: "Find autors like Puskin" (typos!)
3. Check results have "🔍 Explain Similarity" buttons
4. Click one and verify explanation generates

### Step 8: Validate Backward Compatibility
1. Disable "Use AI-powered search"
2. Verify old search still works
3. Check `/search/poems` and `/search/authors` API endpoints directly

## 🐛 Troubleshooting Migration

### Issue: "LLM features will be disabled" in logs

**Cause**: LLM provider not configured

**Fix**:
```powershell
# Check Ollama is running
ollama list

# Check .env file exists
Get-Content .env

# Restart backend
```

### Issue: Frontend doesn't show LLM checkbox

**Cause**: Old frontend cached

**Fix**:
```powershell
# Force reload Streamlit
# Press Ctrl+C and restart
streamlit run frontend/frontend.py
```

### Issue: Explain buttons do nothing

**Cause**: Backend not configured or poem texts missing

**Fix**:
1. Check backend logs for errors
2. Verify `data/processed/poems.parquet` exists
3. Test explanation endpoint directly:
   ```powershell
   curl -X POST http://localhost:8000/explain/poem `
     -H "Content-Type: application/json" `
     -d '{"poem_id":0,"similarity_score":0.9,"query_text":"test"}'
   ```

### Issue: Slow responses

**Cause**: Large Ollama model on CPU

**Fix**:
```powershell
# Use smaller model
ollama pull llama3.1  # Not :70b

# Or switch to cloud
# Edit .env:
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
# OPENAI_API_KEY=sk-...
```

## 📊 Feature Comparison

| Feature | Before | After |
|---------|--------|-------|
| **Typo handling** | ❌ Fails | ✅ LLM understands |
| **Cross-language** | ❌ English names don't work | ✅ Auto-translates |
| **Intent detection** | ⚠️ Rule-based (fragile) | ✅ LLM-powered (robust) |
| **Explanations** | ❌ None | ✅ On-demand AI analysis |
| **Query variations** | ⚠️ Limited patterns | ✅ Natural language |

## 🔀 Switching Back (Rollback)

If you need to revert:

### Option 1: Disable LLM features (keep code)
```powershell
# In .env, comment out or remove:
# LLM_PROVIDER=...

# Or in UI: uncheck "Use AI-powered search"
```

### Option 2: Full rollback
```powershell
# Restore backup
Remove-Item -Recurse .
Copy-Item -Recurse ..\poem_recommender_backup\* .
```

## ✨ Optional Enhancements

### Use Cloud LLM (better quality)

**GPT-4o-mini** (fast, cheap):
```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

**Claude 3.5 Sonnet** (best literary analysis):
```bash
# .env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

### Build Author Translation Database

Generate comprehensive author name translations:
```python
# Run once to build database
from utils.author_matcher import build_author_translation_database
import json

# Get all authors
with open('models/id_map.json', 'r', encoding='utf-8') as f:
    idmap = json.load(f)

authors = list(set([m.get('author', '') for m in idmap if m.get('author')]))

# Build database
build_author_translation_database(
    author_list=authors,
    output_path='data/author_translations.json'
)
```

Then update `load_resources()` to load it:
```python
translation_db_path = BASE / "data" / "author_translations.json"
author_matcher = AuthorMatcher(all_authors, translation_db_path)
```

## 📋 Checklist

Migration complete when you can:

- [ ] Backend starts without errors
- [ ] See "LLM agents initialized" in logs
- [ ] Frontend shows "Use AI-powered search" checkbox
- [ ] Can search with typos: "Puskin" works
- [ ] Can search with English names: "Pushkin" works
- [ ] "Explain Similarity" buttons appear on results
- [ ] Clicking explanation button generates analysis
- [ ] Old rule-based search still works (toggle off LLM)
- [ ] All existing features unchanged

## 🎓 What You Gained

1. **Robustness**: Handles real-world messy queries
2. **Accessibility**: English speakers can search Russian poetry
3. **Explainability**: AI explains WHY poems are similar
4. **Flexibility**: Easy to switch between free/paid LLM providers
5. **Maintainability**: Clean abstraction layers

Perfect for academic demonstration of:
- Modern RAG architectures
- Explainable AI in recommendations
- Cross-language information retrieval
- LLM orchestration patterns

## 📞 Need Help?

1. Check `SETUP_GUIDE.md` for detailed provider configuration
2. Run `test_llm_features.py` for automated validation
3. Check backend logs for detailed error messages
4. Try fallback mode (disable LLM toggle) to isolate issues

---

**Your existing system is preserved - LLM features are additive! 🚀**
