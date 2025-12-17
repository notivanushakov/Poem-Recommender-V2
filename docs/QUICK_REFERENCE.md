# 🚀 Quick Reference Card

## Start System
```powershell
# Terminal 1: Backend
python -m uvicorn backend.app:app --reload --port 8000

# Terminal 2: Frontend  
streamlit run frontend/frontend.py
```

## Test Queries

### Typo Handling
```
"Find autors like Puskin"          # typos
"Simular to Ahmatova"              # more typos
```

### Cross-Language
```
"Show me Pushkin's poems"          # English → Пушкин
"Lermontov romantic poetry"        # English → Лермонтов
```

### Natural Language
```
"Who writes like Yesenin?"
"Authors similar to Anna Akhmatova"
"Poems about love and nature"
```

## Configuration (.env)

### Free (Ollama)
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
```

### Paid (OpenAI)
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

### Paid (Claude)
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /chat/llm` | LLM-powered search |
| `POST /explain/poem` | Get poem explanation |
| `POST /explain/author` | Get author explanation |
| `POST /search/poems` | Direct poem search |
| `POST /search/authors` | Direct author search |

## UI Controls

**Sidebar:**
- ☑️ Use AI-powered search (enable LLM)
- ☐ Force author search
- ☐ Force poem search

**Results:**
- Click [🔍 Explain Similarity] for literary analysis

## Files

| File | Purpose |
|------|---------|
| `utils/llm_provider.py` | LLM abstraction |
| `utils/llm_agent.py` | Intent + explanations |
| `utils/author_matcher.py` | Typo tolerance |
| `backend/app.py` | API endpoints |
| `frontend/frontend.py` | UI |
| `.env` | Configuration |

## Troubleshooting

**"LLM features disabled"**
```powershell
# Check Ollama
ollama list

# Check .env
Get-Content .env
```

**Slow responses**
```bash
# Use faster model
LLM_MODEL=llama3.1  # not :70b

# Or switch to cloud
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

**No explanations**
- Check `data/processed/poems.parquet` exists
- Verify LLM provider is working

## Documentation

- `README_LLM.md` - Quick start
- `SETUP_GUIDE.md` - Full setup
- `MIGRATION_GUIDE.md` - Upgrade guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details

## Testing
```powershell
python test_llm_features.py
```

---
**Default**: Ollama (free) | **Fast**: GPT-4o-mini ($0.50) | **Best**: Claude ($5)
