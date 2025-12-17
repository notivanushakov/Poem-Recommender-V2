# Rebuild & Archiving Guide

## When to Rebuild
| Trigger | Reason |
|---------|--------|
| Embedding model change | Dimension / semantic shift requires full regeneration |
| Dataset update | New or removed poems must be indexed |
| Corrupted artifact | Replace broken file(s) deterministically |
| Evaluation refresh | Ensure alignment with latest preprocessing |

## Command
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
python scripts\rebuild_embeddings.py
```

## Operations (Script Sequence)
1. Detect existing active artifacts.
2. Archive each by moving to `data/embeddings/archive/` with timestamp + original name + `.bak`.
3. Load cleaned dataset (`data/processed/poems.parquet`).
4. Filter overly long texts (>10,000 chars) to reduce embedding latency noise.
5. Embed poems using `intfloat/multilingual-e5-base` in batches (default 64).
6. L2-normalize embeddings; save `poem_embeddings.npy` + duplicate `embeddings.npy`.
7. Build FAISS `IndexFlatIP`; save as `faiss.index`.
8. Generate `id_map.json` mapping index row → poem_id.
9. Write `embedding_info.json` with metadata (timestamp, model, dimensions, counts).
10. Compute author embeddings (mean of poem vectors per author); build `author_faiss.index`.
11. Persist author metadata + embeddings.
12. Log completion summary.

## Archive Naming
Format:
```
YYYYMMDD_HHMMSS_<original_filename>.bak
```
Example:
```
20251130_145452_poem_embeddings.npy.bak
```

## Post-Rebuild Verification (Manual)
| Check | Command (Python snippet) |
|-------|--------------------------|
| Embedding shape | `np.load('data/embeddings/poem_embeddings.npy').shape` |
| Index count | Load FAISS; compare `index.ntotal` vs embedding rows |
| Metadata sync | Line count of `poem_metadata.jsonl` equals embedding rows |
| Author count | `author_embeddings.npy` rows == length of `author_metadata.json` |

## Rollback Procedure
1. Stop backend.
2. Move current active files to temporary folder.
3. Select desired backup in `archive/`.
4. Restore by renaming (remove timestamp + `.bak`).
5. Restart backend.

## Performance Tuning
| Parameter | Effect |
|-----------|-------|
| Batch size | Larger reduces total wall time; increases memory |
| Text filter threshold | Adjust length limit to balance coverage vs speed |
| Data loading path | Ensure parquet is optimized (categoricals, pruned columns) |

## Safety Principles
- Never delete archives automatically.
- Always duplicate critical embedding file as `embeddings.npy` for legacy compatibility.
- Fail fast if model load errors; avoid partial artifact set.

## Common Issues
| Symptom | Cause | Resolution |
|---------|-------|-----------|
| Missing author index | Script interrupted before author step | Re-run full rebuild |
| Mismatched dimensions | Model swap without rebuild | Run rebuild to reconcile |
| Slow encoding | Too small batch size or resource contention | Increase batch size if memory allows |

## Suggested Future Enhancements
| Idea | Benefit |
|------|--------|
| Incremental update mode | Avoid full re-embedding for small additions |
| Embedding checksum manifest | Integrity verification |
| Parallel encoding workers | Faster rebuild utilizing multi-core |
| FP16 storage option | Reduced disk & RAM usage |

## Summary
Rebuild process guarantees clean, reproducible artifact sets with full archival of prior states, enabling safe iteration over models and data without loss of historical configurations.
