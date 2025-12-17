# Poem Recommender (Multilingual + Reranking)

Multilingual poetry search & recommendation system featuring upgraded semantic embeddings, cross-encoder reranking, reproducible artifact rebuilds, and author similarity search.

## ✅ Current Core Stack (2025-11-30)
| Layer | Component | Details |
|-------|-----------|---------|
| Embeddings | `intfloat/multilingual-e5-base` | 768-dim multilingual sentence embeddings (normalized) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Pairwise relevance scoring for top candidates |
| Vector Index | FAISS `IndexFlatIP` | Inner product over L2-normalized vectors (cosine) |
| Backend | FastAPI | Search endpoints + reranking pipeline |
| Frontend | Streamlit | Interactive search UI |
| Rebuild | `scripts/rebuild_embeddings.py` | Archive + full artifact regeneration |

## 🚀 Quick Start
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Backend
cd backend
python app.py

# Frontend (separate terminal)
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
streamlit run frontend/frontend.py
```
Open: http://localhost:8501

## 🔍 Search Flow
```
User Query → Embed (E5) → FAISS Top-N → Cross-Encoder Rerank → Final Results
                        ↘ (Fallback if reranker missing) → FAISS Ranking Only
```

## 📂 Project Structure (Relevant Now)
```
backend/app.py              # FastAPI + retrieval + reranking
frontend/frontend.py        # Streamlit UI
scripts/rebuild_embeddings.py # Full rebuild & archiving
data/embeddings/            # Active poem & author artifacts
data/embeddings/archive/    # Timestamped .bak backups
utils/intent.py             # Basic intent / legacy logic
models/                     # (Legacy) previous embedding dump (may be outdated)
```

## 📦 Artifacts (data/embeddings)
| File | Purpose |
|------|---------|
| `poem_embeddings.npy` | Primary poem embeddings (N x 768) |
| `embeddings.npy` | Backward compatibility duplicate |
| `poem_metadata.jsonl` | Per-poem metadata records |
| `embedding_info.json` | Model + generation metadata |
| `faiss.index` | Poem similarity index |
| `id_map.json` | Row index → poem_id mapping |
| `author_embeddings.npy` | Mean pooled author vectors |
| `author_faiss.index` | Author similarity index |
| `author_metadata.json` | Author id/name mapping |
| `archive/*.bak` | Timestamped backups from prior rebuilds |

## 🔁 Rebuild & Archiving
Regenerate all artifacts and archive previous versions:
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
python scripts\rebuild_embeddings.py
```
Workflow:
1. Move existing artifacts → `archive/` with timestamp `.bak`
2. Load cleaned parquet from `data/processed/poems.parquet`
3. Filter overly long texts (>10k chars)
4. Encode with E5 (batch 64) + L2 normalize
5. Persist poem embeddings + duplicate `embeddings.npy`
6. Build poem FAISS index + id map
7. Derive author embeddings (mean) + author FAISS index
8. Write metadata summaries

## ⚙️ Reranking Mechanics
- Candidate pool: `top_n = max(k*5, 50)` retrieved from FAISS
- Cross-encoder scores (query, poem_text) pairs
- Final ordering by reranker score; fallback to FAISS scores if reranker unavailable
- Safe exception handling prevents total failure if reranker errors

## 🧪 Planned Testing (Deferred)
To be executed later — will validate:
- Embedding integrity (shape, norm ≈1)
- FAISS retrieval vs reranked quality (manual spot checks)
- Author search consistency after rebuild

## ❗ Known Notes / Housekeeping
- Legacy LLM explanation & provider abstraction present but not focus of current phase
- Previous 384-dim MiniLM embeddings replaced (archived in `archive/`)
- Some older docs (LLM-centric) may be stale — this README reflects current active retrieval layer
- Sklearn version upgraded; econml warning irrelevant unless econml reintroduced

## 🔧 Configuration Highlights
- Always activate venv before running rebuild or backend
- Environment overrides for model names can be added later if needed
- Index assumes normalized embeddings (inner product = cosine)

## 🚀 Example Queries
```
"poems about любовь и природа"
"authors similar to Пушкин"
"melancholy night imagery" (English → Russian cross-lingual)
"modernist revolutionary style" (semantic thematic search)
```

## ➕ Future Improvements (Optional)
- Evaluation set + nDCG / MRR benchmarks
- Query language detection & adaptive preprocessing
- Reranker result caching for popular queries
- Lightweight distilled index for deployment

## 📜 License / Usage
Academic / internal project (TU Darmstadt embeddings course). Respect upstream model licenses.

---
Current README authored post-upgrade (E5 + reranker) to reflect real system state.
