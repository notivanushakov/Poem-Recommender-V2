"""Rebuild poem and author embedding artifacts using upgraded model.

Steps:
1. Archive existing artifacts under data/embeddings/archive/*.bak
2. Load cleaned poems from data/processed/poems.parquet (fallback to raw CSV)
3. Generate poem embeddings with intfloat/multilingual-e5-base
4. Save poem embeddings (poem_embeddings.npy + embeddings.npy), metadata (jsonl), info JSON
5. Build poem FAISS index (faiss.index + id_map.json)
6. Compute author embeddings + author FAISS index (author_embeddings.npy, author_metadata.json, author_faiss.index)

Run:
  python scripts/rebuild_embeddings.py
"""
from __future__ import annotations

import json
import time
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import faiss

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROC_DIR = DATA_DIR / "processed"
EMB_DIR = DATA_DIR / "embeddings"
ARCHIVE_DIR = EMB_DIR / "archive"

RAW_CSV = DATA_DIR / "poems.csv"  # Fallback if parquet missing
PARQUET = PROC_DIR / "poems.parquet"

MODEL_NAME = "intfloat/multilingual-e5-base"
BATCH_SIZE = 64
MAX_TEXT_LEN = 10_000  # filter very long outliers

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def archive_old_artifacts():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    to_archive = [
        "embeddings.npy",
        "poem_embeddings.npy",
        "poem_metadata.jsonl",
        "embedding_info.json",
        "faiss.index",
        "id_map.json",
        "author_embeddings.npy",
        "author_metadata.json",
        "author_faiss.index",
    ]
    for fname in to_archive:
        src = EMB_DIR / fname
        if src.exists():
            dst = ARCHIVE_DIR / f"{fname}.bak"
            shutil.move(str(src), str(dst))
            print(f"[ARCHIVE] {fname} -> {dst.name}")
        else:
            print(f"[ARCHIVE] (skip) {fname} not found")


def load_clean_dataset() -> pd.DataFrame:
    if PARQUET.exists():
        print(f"[LOAD] Using cleaned parquet: {PARQUET}")
        return pd.read_parquet(PARQUET)
    if RAW_CSV.exists():
        print(f"[LOAD] Parquet missing. Loading raw CSV for minimal cleaning: {RAW_CSV}")
        df = pd.read_csv(RAW_CSV)
        # Minimal renaming to expected columns
        col_map = {"writer": "author", "poem": "title", "text": "text"}
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        # Drop rows without text
        df = df[df.get("text", "").notna() & (df.get("text", "") != "")]
        df["poem_id"] = range(len(df))
        # Provide fallback text_norm (lower + strip)
        df["text_norm"] = df["text"].astype(str).str.strip()
        return df[["poem_id", "author", "title", "text", "text_norm"]]
    raise FileNotFoundError("Neither processed parquet nor raw CSV found.")


def filter_texts(df: pd.DataFrame, max_len: int) -> pd.DataFrame:
    if max_len:
        lengths = df["text_norm"].str.len()
        mask = lengths <= max_len
        removed = (~mask).sum()
        if removed:
            print(f"[FILTER] Removed {removed} overly long poems (> {max_len} chars)")
        return df[mask].reset_index(drop=True)
    return df


def create_embeddings(df: pd.DataFrame) -> Tuple[np.ndarray, List[Dict], SentenceTransformer]:
    print("[EMB] Loading model:", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)
    texts = df["text_norm"].astype(str).tolist()
    print(f"[EMB] Encoding {len(texts)} poems (batch {BATCH_SIZE})...")
    start = time.time()
    embs = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_emb = model.encode(batch, convert_to_numpy=True, normalize_embeddings=False, show_progress_bar=False)
        embs.append(batch_emb)
    embs = np.vstack(embs)
    print(f"[EMB] Raw embedding shape: {embs.shape} in {time.time()-start:.1f}s")
    embs = normalize(embs, norm="l2", axis=1).astype("float32")
    metadata = df[["poem_id", "author", "title", "text"]].to_dict(orient="records")
    return embs, metadata, model


def save_poem_artifacts(embeddings: np.ndarray, metadata: List[Dict]):
    EMB_DIR.mkdir(parents=True, exist_ok=True)
    poem_np = EMB_DIR / "poem_embeddings.npy"
    np.save(poem_np, embeddings)
    dup_np = EMB_DIR / "embeddings.npy"  # backend expects this
    np.save(dup_np, embeddings)
    print(f"[SAVE] Poem embeddings saved: {poem_np.name} & {dup_np.name} shape={embeddings.shape}")

    meta_path = EMB_DIR / "poem_metadata.jsonl"
    with open(meta_path, "w", encoding="utf-8") as f:
        for item in metadata:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[SAVE] Metadata jsonl: {meta_path.name} count={len(metadata)}")

    info = {
        "model_name": MODEL_NAME,
        "embedding_dim": int(embeddings.shape[1]),
        "num_poems": int(embeddings.shape[0]),
        "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "batch_size": BATCH_SIZE,
        "max_text_length": MAX_TEXT_LEN,
    }
    with open(EMB_DIR / "embedding_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print("[SAVE] embedding_info.json written")


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"[FAISS] Built IndexFlatIP with {index.ntotal} vectors (dim={dim})")
    return index


def save_faiss_index(index: faiss.Index, metadata: List[Dict]):
    faiss_path = EMB_DIR / "faiss.index"
    faiss.write_index(index, str(faiss_path))
    print(f"[FAISS] Saved poem index: {faiss_path.name}")

    id_map_path = EMB_DIR / "id_map.json"
    with open(id_map_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"[FAISS] Saved id_map.json entries={len(metadata)})")


def compute_author_embeddings(embeddings: np.ndarray, metadata: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
    from collections import defaultdict
    author_to_indices = defaultdict(list)
    for idx, m in enumerate(metadata):
        a = (m.get("author") or "").strip()
        if a:
            author_to_indices[a].append(idx)
    author_vecs = []
    author_meta = []
    for author, idxs in sorted(author_to_indices.items()):
        vec = embeddings[idxs].mean(axis=0)
        norm = np.linalg.norm(vec)
        if norm == 0:
            continue
        author_vecs.append(vec)
        author_meta.append({
            "author": author,
            "poem_indices": idxs,
            "count": len(idxs)
        })
    author_arr = np.vstack(author_vecs).astype("float32")
    author_arr = normalize(author_arr, norm="l2", axis=1).astype("float32")
    print(f"[AUTHOR] {len(author_meta)} author embeddings created")
    return author_arr, author_meta


def save_author_artifacts(author_embeddings: np.ndarray, author_metadata: List[Dict]):
    np.save(EMB_DIR / "author_embeddings.npy", author_embeddings)
    with open(EMB_DIR / "author_metadata.json", "w", encoding="utf-8") as f:
        json.dump(author_metadata, f, ensure_ascii=False, indent=2)
    index = faiss.IndexFlatIP(author_embeddings.shape[1])
    index.add(author_embeddings)
    faiss.write_index(index, str(EMB_DIR / "author_faiss.index"))
    print(f"[AUTHOR] Saved author embeddings + index: count={len(author_metadata)})")


def main():
    print("============== REBUILD EMBEDDINGS (E5) ==============")
    archive_old_artifacts()
    df = load_clean_dataset()
    print(f"[DATA] Loaded {len(df)} poems, columns={df.columns.tolist()}")
    df = filter_texts(df, MAX_TEXT_LEN)
    embeddings, metadata, _ = create_embeddings(df)
    save_poem_artifacts(embeddings, metadata)
    index = build_faiss_index(embeddings)
    save_faiss_index(index, metadata)
    author_embeddings, author_metadata = compute_author_embeddings(embeddings, metadata)
    save_author_artifacts(author_embeddings, author_metadata)
    print("✅ DONE: All artifacts rebuilt successfully.")


if __name__ == "__main__":
    main()
import time
from pathlib import Path
import shutil
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import faiss

MODEL_NAME = "intfloat/multilingual-e5-base"
MAX_TEXT_LENGTH = 10000
BATCH_SIZE = 64

DATA_DIR = Path("C:/Users/Ivan/Documents/Studies/TU Darmstadt/3 Semester/Embeddings/poem_recommender_llms/data")
EMB_DIR = DATA_DIR / "embeddings"
ARCHIVE_DIR = EMB_DIR / "archive"
CLEAN_PARQUET = DATA_DIR / "processed" / "poems.parquet"

def load_cleaned_poems(df: pd.DataFrame, max_length: int = None):
    df_embed = df.copy()
    if max_length:
        text_lengths = df_embed['text_norm'].str.len()
        df_embed = df_embed[text_lengths <= max_length].reset_index(drop=True)
    texts = df_embed['text_norm'].astype(str).tolist()
    metadata = df_embed[['poem_id', 'author', 'title', 'text']].to_dict(orient='records')
    return texts, metadata

def batch_encode(model: SentenceTransformer, texts, batch_size: int = 64):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = model.encode(batch, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=False)
        embeddings.append(emb)
    return np.vstack(embeddings)

def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    embeddings_norm = normalize(embeddings, norm='l2', axis=1)
    return embeddings_norm.astype('float32')

def archive_existing():
    EMB_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    moved = []
    for name in ["poem_embeddings.npy", "poem_metadata.jsonl", "embedding_info.json", "faiss.index", "id_map.json"]:
        src = EMB_DIR / name
        if src.exists():
            dst = ARCHIVE_DIR / f"{timestamp}_{name}"
            shutil.move(str(src), str(dst))
            moved.append(dst.name)
    return moved

def main():
    print("Archiving previous artifacts...")
    moved = archive_existing()
    if moved:
        print("Moved:", ", ".join(moved))
    else:
        print("No previous artifacts found.")

    print(f"Loading cleaned dataset: {CLEAN_PARQUET}")
    df = pd.read_parquet(CLEAN_PARQUET)

    print(f"Loading model: {MODEL_NAME}")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME)
    print(f"Model loaded in {time.time()-t0:.1f}s")

    texts, metadata = load_cleaned_poems(df, max_length=MAX_TEXT_LENGTH)
    print(f"Encoding {len(texts)} poems...")
    embeddings = batch_encode(model, texts, batch_size=BATCH_SIZE)
    embeddings = normalize_embeddings(embeddings)

    EMB_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMB_DIR / "poem_embeddings.npy", embeddings)
    with open(EMB_DIR / "poem_metadata.jsonl", "w", encoding="utf-8") as f:
        for item in metadata:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    # Build FAISS index (Inner Product for cosine with normalized embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype('float32'))
    faiss.write_index(index, str(EMB_DIR / "faiss.index"))
    # Build id_map.json aligned to embedding row indices
    id_map = []
    for i, m in enumerate(metadata):
        id_map.append({
            "poem_id": m.get("poem_id"),
            "author": m.get("author"),
            "title": m.get("title"),
        })
    with open(EMB_DIR / "id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)
    info = {
        "model_name": MODEL_NAME,
        "embedding_dim": embeddings.shape[1],
        "num_poems": embeddings.shape[0],
        "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "max_text_length": MAX_TEXT_LENGTH,
        "batch_size": BATCH_SIZE
    }
    with open(EMB_DIR / "embedding_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print("Saved new embeddings, FAISS index, and id_map.")

if __name__ == "__main__":
    main()
