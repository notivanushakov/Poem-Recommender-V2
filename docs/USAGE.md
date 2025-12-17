# Usage Guide

## Environment Preparation (Windows PowerShell)
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Starting Services
```powershell
# Backend
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
cd backend
python app.py

# Frontend (new terminal)
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
streamlit run frontend/frontend.py
```
Default ports: FastAPI (8000), Streamlit (8501).

## Basic Poem Search (API)
```bash
POST /search/poems
{
  "query": "любовь и природа",
  "k": 10
}
```
Response includes reranked results if cross-encoder loaded.

## Author Search (API)
```bash
POST /search/authors
{
  "query": "Пушкин",
  "k": 5
}
```
Returns top similar authors.

## Recommended Query Styles
| Type | Example | Purpose |
|------|---------|---------|
| Thematic | "melancholy winter night" | Concept matching |
| Emotional | "poems about loss" | Mood-based retrieval |
| Cross-lingual | "revolutionary Russian futurism" | English→Russian bridging |
| Author similarity | "authors like Ахматова" | Style proximity |

## Reranker Fallback Detection
If reranking disabled (log warning on startup), ordering reflects pure FAISS scores.

## Rebuild Artifacts
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
python scripts\rebuild_embeddings.py
```
Run after: model change, dataset update, or artifact corruption.

## Latency Considerations
| Stage | Typical Cost |
|-------|--------------|
| Embedding (query) | ~5–15 ms |
| FAISS retrieval | <5 ms |
| Cross-encoder (50–100 pairs) | 300–800 ms |

Reduce latency by lowering `k` (implicitly reduces `top_n`) or disabling reranker (temporary).

## Troubleshooting Quick Reference
| Symptom | Action |
|---------|--------|
| "Model not found" | Reinstall `sentence-transformers` in venv |
| Empty results | Check query language / encoding errors |
| High latency spikes | Lower candidate pool size or inspect reranker load |
| Backend crash on startup | Verify presence of all artifact files; rebuild if absent |

## Safe Operations
| Action | Impact |
|--------|--------|
| Rebuild script | Archives old artifacts; regenerates complete set |
| Restart backend | Reloads embeddings + reranker in memory |
| Changing `k` | Adjusts result count and reranker workload |

## Not in Scope (Current Phase)
- LLM explanation endpoints (legacy) not actively documented here
- Evaluation metrics (future enhancement)

## Summary
Activate environment, start backend + frontend, issue semantic queries. Rebuild artifacts only when underlying data or model changes. Reranker enhances precision; system degrades gracefully without it.
