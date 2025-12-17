# LLM-Enhanced Poem Recommender 📖✨

AI-powered Russian poetry recommendation system with semantic embeddings, cross-language search, and explainable AI.

## 🌟 Key Features

### ✅ Problems Solved

| Problem | Solution |
|---------|----------|
| ❌ Typos break search | ✅ LLM understands "Puskin" = "Pushkin" |
| ❌ Can't search English→Russian | ✅ "Pushkin" finds "Пушкин" poems |
| ❌ Varied phrasings fail | ✅ Smart intent detection |
| ❌ No explanation of similarity | ✅ On-demand literary analysis |
| ❌ Locked to one LLM | ✅ Easy switch: Ollama ↔ GPT ↔ Claude ↔ Grok |

## 🚀 Quick Start

### 1. Install Ollama (Free LLM)
```powershell
# Download from https://ollama.ai or:
winget install Ollama.Ollama

# Pull a model
ollama pull llama3.1
```

### 2. Setup Project
```powershell
# Install dependencies
pip install -r requirements.txt

# Configure (use defaults for Ollama)
Copy-Item .env.example .env
```

### 3. Run
```powershell
# Terminal 1: Backend
python -m uvicorn backend.app:app --reload --port 8000

# Terminal 2: Frontend
streamlit run frontend/frontend.py
```

### 4. Test
Open http://localhost:8501 and try:
- "Find autors like Puskin" (typos!)
- "Show me Pushkin's poems" (English name)
- Click "🔍 Explain Similarity" buttons

## 📚 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup for all LLM providers
- **[ENHANCEMENT_PLAN.md](ENHANCEMENT_PLAN.md)** - Technical architecture & design
- **[test_llm_features.py](test_llm_features.py)** - Automated test suite

## 🏗️ Architecture

```
User Query → LLM Agent → Function Calling → Search (Embeddings + FAISS)
                ↓
         Author Matcher (typo tolerance + cross-language)
                ↓
         Results + Optional Explanation (on-demand)
```

### New Components

1. **`utils/llm_provider.py`** - Interoperable LLM abstraction (Ollama/GPT/Claude/Grok)
2. **`utils/llm_agent.py`** - Intent detection + explanation generation
3. **`utils/author_matcher.py`** - Fuzzy matching with cross-language support
4. **Backend endpoints**:
   - `/chat/llm` - LLM-powered search
   - `/explain/poem` - Generate poem similarity explanation
   - `/explain/author` - Generate author similarity explanation
5. **Frontend enhancements** - Explanation buttons + LLM toggle

## 🎯 Use Cases

### Typo Tolerance
```
❌ Before: "Puskin" → No results
✅ Now:    "Puskin" → Finds Пушкин Александр Сергеевич
           "маяковскго" → Finds Маяковский Владимир Владимирович
```

### Cross-Language
```
❌ Before: "Pushkin" (English) → No match in Russian DB
✅ Now:    "Pushkin" → Автоматически finds "Пушкин"
           "Mayakovsky" → Finds Маяковский Владимир Владимирович
```

### Explainable AI
```
❌ Before: Just similarity score (0.87) - why?
✅ Now:    Click "🔍 Explain Similarity" button next to each result
           → Literary analysis in your chosen language (EN/RU)
           → Themes, style, emotion, historical context
```

## 🔧 Configuration

Edit `.env` to switch providers:

```bash
# Free local (recommended for testing)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1

# Or paid cloud (recommended for production - better quality & speed)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o        # or gpt-4o-mini for cheaper
OPENAI_API_KEY=sk-...
```

**Free Tier Alert**: OpenAI offers free tier with generous limits!
- **gpt-4o**: 250K tokens/day FREE (~400-800 queries/day)
- **gpt-4o-mini**: 2.5M tokens/day FREE

No code changes needed to switch!

## 📊 Dataset

- **829,484 Russian poems** from classic authors
- Embedded using `paraphrase-multilingual-MiniLM-L12-v2`
- **18,529 unique poems** with metadata
- FAISS index for fast similarity search

## 🧪 Testing

```powershell
# Run automated tests
python test_llm_features.py
```

Tests validate:
1. Typo handling in author names
2. Cross-language author resolution
3. Intent detection accuracy
4. Explanation generation quality

## 💡 LLM Provider Options

| Provider | Cost | Quality | Setup |
|----------|------|---------|-------|
| **Ollama** | Free | Good | Easy (local) |
| **GPT-4o-mini** | ~$0.50 | Great | API key |
| **Claude 3.5** | ~$5 | Excellent | API key |
| **Grok** | Varies | Good | API key |

**Recommendation**: Start with Ollama (free), switch to GPT for speed or Claude for quality.

## 📖 Academic Context

TU Darmstadt - Embeddings Course Project

**Enhancements demonstrate**:
- Semantic embeddings + LLM orchestration
- Explainable AI in recommendation systems
- Cross-language information retrieval
- Modern RAG architecture patterns

## 🎨 UI Preview

**Features**:
- ☑️ Toggle: "Use AI-powered search"
- 🔍 Button: "Explain Similarity" (visible next to EACH result - poems AND authors)
- 🤖 Expander: "AI Reasoning" (shows LLM's thought process)
- ✓ Badge: Author resolution display
- 🌐 Language selector: Explanations adapt to UI language (English/Русский)

**Poem Results**:
```
[Poem Title — Author — Score 0.87] | [🔍 Explain Similarity]
  ↳ Click to expand poem text
  ↳ Click Explain → Literary analysis appears
```

**Author Results**:
```
[Author Name (count: 42) — Score 0.92] | [🔍 Explain Similarity]
  ↳ Sample poems shown below
  ↳ Click Explain → Comparative analysis appears
```

**Languages**: English / Русский (explanations generated in selected language)

## 🚦 Status

✅ Full implementation complete
✅ Interoperable LLM providers
✅ On-demand explanations
✅ Typo tolerance
✅ Cross-language support
✅ Comprehensive documentation
✅ Test suite

## 📝 Example Queries

**Author Search (with typos)**:
- "Find autors like Puskin"
- "Simular to Ahmatova"
- "Authors similar to Yesenin"

**Cross-Language**:
- "Show me Pushkin's poems" (English → Пушкин)
- "Lermontov romantic poetry"

**Poem Search**:
- "Poems about love and loss"
- "I wandered lonely as a cloud..." (English → Russian matches)

**Then click "🔍 Explain Similarity" for AI literary analysis!**

## 📄 License

Academic project - TU Darmstadt

---

**Happy poetry exploring! 🎭📚**
