# Data & Model Artifacts

Location: `data/embeddings/`

## Poem-Level Files
| File | Description | Notes |
|------|-------------|-------|
| `poem_embeddings.npy` | Float32 array (N x 768) of poem vectors | L2-normalized rows |
| `embeddings.npy` | Duplicate of poem embeddings | Backward compatibility |
| `poem_metadata.jsonl` | One JSON object per poem (id, author, title, text refs) | Newline-delimited JSON |
| `embedding_info.json` | Model + generation metadata (timestamp, dim, model name) | Update each rebuild |
| `faiss.index` | FAISS IndexFlatIP storing poem vectors | Requires normalized input |
| `id_map.json` | Mapping: internal index → poem_id | Used to resolve hits |

## Author-Level Files
| File | Description | Notes |
|------|-------------|-------|
| `author_embeddings.npy` | Mean-pooled author vectors (A x 768) | Row order matches metadata |
| `author_faiss.index` | FAISS IndexFlatIP of author vectors | Same similarity metric |
| `author_metadata.json` | Author ID/name list | Supports display & mapping |

## Archive Directory
`data/embeddings/archive/` contains timestamped backups:
```
20251130_145452_poem_embeddings.npy.bak
20251130_145452_poem_metadata.jsonl.bak
...
```
Purpose: rollback capability & historical reproducibility.

## Integrity Expectations
| Check | Condition |
|-------|-----------|
| Embedding count | `len(poem_metadata) == poem_embeddings.shape[0]` |
| Index total | `faiss_index.ntotal == poem_embeddings.shape[0]` |
| Dimension | `poem_embeddings.shape[1] == 768` |
| Normalization | `np.linalg.norm(row) ≈ 1.0` for all rows |
| ID map | Keys cover `[0 .. ntotal-1]` |

## Metadata Record Example (poem_metadata.jsonl)
```json
{
  "poem_id": 123456,
  "author": "Александр Пушкин",
  "title": "***",
  "text": "...",
  "text_norm": "..."
}
```

## Common Issues
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| Backend fails to load index | Missing/rebuild incomplete | Re-run rebuild script |
| Search returns zero results | Query embedding failure | Check model install / venv activation |
| Author search misaligned | Author metadata mismatch | Rebuild to re-sync files |

## Versioning Strategy
- Each rebuild archives prior state with timestamp.
- `embedding_info.json` documents active model & date.
- External change (model swap) always triggers full rebuild.

## Future Extensions
| Enhancement | Benefit |
|-------------|---------|
| Add checksum file | Fast corruption detection |
| Store text length stats | Reranker truncation planning |
| Embed language tags | Language-aware filtering |
| Compressed embeddings (FP16) | Reduced disk/memory footprint |

## Summary
Artifacts are designed for deterministic, inspectable retrieval. Consistent normalization and clear mapping ensure reliable search and facilitate future evaluation additions.
