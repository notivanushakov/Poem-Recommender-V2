# Architecture Overview

## High-Level Flow
```
User Query
   │
   ├─> Embedding (E5 model)
   │      Vector (768-dim, L2-normalized)
   │
   ├─> FAISS Candidate Retrieval (IndexFlatIP)
   │      top_n = max(k*5, 50)
   │
   ├─> Cross-Encoder Reranking (if available)
   │      Pairwise (query, poem_text) scoring
   │
   └─> Response Assembly (metadata + scores)
```

## Components
| Component | File | Responsibility |
|-----------|------|----------------|
| FastAPI Backend | `backend/app.py` | Endpoints: poem search, author search, reranking integration |
| Frontend UI | `frontend/frontend.py` | User interaction, querying backend, displaying results |
| Rebuild Script | `scripts/rebuild_embeddings.py` | Deterministic artifact regeneration + archiving |
| Intent / Legacy Logic | `utils/intent.py` | Basic intent handling (legacy) |
| Data Artifacts | `data/embeddings/` | Embeddings, indices, metadata, backups |

## Retrieval Strategy
1. Encode query with `intfloat/multilingual-e5-base` (consistent sentence prefixing already handled internally by model design).
2. Normalize embedding to unit length.
3. Perform inner-product search on FAISS index (cosine similarity via normalization).
4. Expand candidate pool (top_n) to allow effective reranking.
5. Apply cross-encoder `ms-marco-MiniLM-L-6-v2` scoring on (query, full poem text) pairs.
6. Sort by reranker score; fallback to raw FAISS similarity if reranker unavailable.

## Author Similarity
- Author embedding = mean of all poem vectors for that author (already normalized before mean).
- Author index built separately (`author_faiss.index`).
- Search endpoint embeds query, retrieves top authors directly.

## Normalization & Similarity
- All poem vectors L2-normalized after embedding.
- Index type: `IndexFlatIP` (fast, no quantization).
- Similarity measure: `score = dot(query_norm, doc_norm)` → cosine.

## Reranker Details
- Cross-encoder processes full text (may be truncated internally if model limit reached).
- Potential performance consideration: candidate size trade-off (larger `top_n` improves quality but increases latency).

## Failure Modes & Fallbacks
| Scenario | Behavior |
|----------|----------|
| Reranker load failure | Log warning; use FAISS ranking only |
| Encoding exception | Return empty result set with error message |
| Missing artifacts | Backend initialization error; requires rebuild |

## Archiving Strategy
- Pre-rebuild artifacts renamed with timestamp + `.bak` placed in `data/embeddings/archive/`.
- Guarantees rollback possibility and reproducibility.

## Extensibility Points
| Area | Possible Enhancement |
|------|----------------------|
| Evaluation | Add benchmark set + nDCG/MRR scripts |
| Query Handling | Language detection & adaptive preprocessing |
| Performance | Introduce approximate ANN (e.g., HNSW) if scale grows |
| Reranking | Swap to stronger cross-encoder or lightweight distillation |
| Caching | Store frequent reranked results in memory or Redis |

## Current Constraints
- Rebuild time is substantial (full corpus embedding pass).
- Cross-encoder adds latency proportional to candidate count.
- Memory footprint driven by dense embeddings (N x 768 float32).

## Data Integrity Checks (Recommended Later)
- Verify embedding count == metadata count.
- Ensure FAISS index ntotal matches embedding rows.
- Confirm each poem_id appears exactly once in `poem_metadata.jsonl`.

## Summary
Architecture emphasizes clear separation: deterministic artifact generation, stateless retrieval, optional reranking enhancement, and safe fallbacks. This supports iterative quality improvements without destabilizing baseline search.
