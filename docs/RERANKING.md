# Reranking Design

## Purpose
Improve semantic relevance beyond raw embedding similarity by applying a cross-encoder that directly scores (query, poem_text) pairs.

## Pipeline Position
```
Embed Query → FAISS Retrieval (top_n) → Cross-Encoder Score → Sort → Return
```
`top_n = max(k*5, 50)` ensures enough diversity for reranking to be effective.

## Models
| Role | Model | Characteristics |
|------|-------|-----------------|
| Embedding | `intfloat/multilingual-e5-base` | Robust multilingual sentence representation |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Lightweight pairwise relevance scorer |

## Scoring Mechanics
- FAISS stage yields initial similarity (cosine via inner product on normalized vectors).
- Cross-encoder performs joint encoding of concatenated query + poem text → relevance score.
- Final ordering strictly by reranker score when available.

## Fallback Behavior
| Condition | Action |
|-----------|--------|
| Reranker load exception | Log warning; use FAISS ranking |
| Runtime scoring error | Skip reranking for that request |

## Performance Notes
| Factor | Impact |
|--------|--------|
| Candidate size | Linear increase in reranking latency |
| Poem text length | Longer inputs increase encoding time; potential truncation internally |
| Model choice | Larger cross-encoders yield higher quality but slower response |

## Tuning Parameters (Future)
| Parameter | Potential Adjustment |
|-----------|----------------------|
| `top_n` heuristic | Dynamic scaling based on query length or term rarity |
| Cross-encoder model | Upgrade to stronger (e.g., `ms-marco-MiniLM-L-12-v2`) or distill smaller |
| Batch scoring | Group (query, text) pairs for throughput (currently per-request) |

## Quality Rationale
Embedding similarity captures coarse semantic space; cross-encoder reinterprets query with full poem context, improving:
- Nuanced thematic alignment
- Handling of polysemy
- Relevance ordering for stylistically similar texts

## Diagnostics Ideas
| Check | Insight |
|-------|--------|
| Compare top-10 FAISS vs reranked | Measures reranker impact |
| Score distribution histogram | Identifies threshold anomalies |
| Mean score vs poem length | Detects bias toward shorter texts |

## Potential Cache Strategy
- Key: hash(query text)
- Value: reranked list (poem_id + score)
- Invalidate on rebuild (embedding version change)

## Summary
Reranking introduces a precision layer that refines broad semantic retrieval into higher fidelity matches while maintaining graceful degradation if unavailable.
