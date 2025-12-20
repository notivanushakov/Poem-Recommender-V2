# backend/app.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
import json
import sys
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
from sklearn.preprocessing import normalize
import faiss
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from utils.intent import detect_intent, find_author_in_text
from utils.llm_agent import LLMAgent, ExplanationAgent
from utils.author_matcher import AuthorMatcher
import os
from dotenv import load_dotenv

load_dotenv()

MODELS_DIR = BASE / "data" / "embeddings"
PROC_DIR = BASE / "data" / "processed"

# Paths
POEM_INDEX_PATH = MODELS_DIR / "faiss.index"
POEM_EMB_PATH = MODELS_DIR / "embeddings.npy"
IDMAP_PATH = MODELS_DIR / "id_map.json"
POEMS_PARQUET = PROC_DIR / "poems.parquet"

AUTHOR_EMB_PATH = MODELS_DIR / "author_embeddings.npy"
AUTHOR_MAP_PATH = MODELS_DIR / "author_metadata.json"  # align with rebuild script output
AUTHOR_INDEX_PATH = MODELS_DIR / "author_faiss.index"

MODEL_NAME = "intfloat/multilingual-e5-base"

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_resources()
    print("\n" + "="*60)
    print("STARTUP DIAGNOSTICS")
    print("="*60)
    print(f"explanation_agent loaded: {explanation_agent is not None}")
    print(f"llm_agent loaded: {llm_agent is not None}")
    print(f"author_matcher loaded: {author_matcher is not None}")
    if explanation_agent:
        print(f"LLM provider available: {hasattr(explanation_agent, 'llm')}")
    print("="*60 + "\n")
    yield
    # Shutdown (optional cleanup)
    # Add any resource cleanup here if needed

app = FastAPI(title="Poem Recommender API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------
# Pydantic models
# -------------------
class TextQuery(BaseModel):
    text: str
    k: int = 10
    language: str = "en"  # For error messages and bilingual output

class AuthorQuery(BaseModel):
    author: str
    k: int = 10
    language: str = "en"  # For error messages and bilingual output

class ChatQuery(BaseModel):
    text: str
    k: int = 10
    language: str = "en"  # For error messages

class TranslatePoemRequest(BaseModel):
    poem_id: Any
    poem_text: str

class ExplainPoemRequest(BaseModel):
    query_text: str = None
    poem_id: Any
    similarity_score: float
    language: str = "en"  # "en" or "ru"

class ExplainAuthorRequest(BaseModel):
    query_author: str
    similar_author: str
    similarity_score: float
    sample_poem_ids: List[Any] = []
    language: str = "en"  # "en" or "ru"

class MatchAuthorQuery(BaseModel):
    text: str
    language: str = "en"

# -------------------
# Global in-memory objects loaded at startup
# -------------------
model = None
poem_index = None
poem_idmap = None  # list of dicts
poem_embeddings = None  # numpy array
poems_df = None

author_index = None
author_map = None  # list of dicts: {author, poem_indices, count}
author_embeddings = None
author_name_lookup = None  # list of author names for intent

# LLM-powered agents
llm_agent = None
explanation_agent = None
author_matcher = None
reranker = None

# Translation cache to avoid repeated LLM calls
translation_cache = {}  # {"russian_text": "English Translation"}

# -------------------
# Helpers
# -------------------
ERROR_MESSAGES = {
    "author_not_found": {
        "en": "Author '{}' not found. Please check the spelling or try a different name.",
        "ru": "Автор '{}' не найден. Пожалуйста, проверьте написание или попробуйте другое имя."
    },
    "empty_text": {
        "en": "Please enter some text to search.",
        "ru": "Пожалуйста, введите текст для поиска."
    },
    "empty_author": {
        "en": "Please enter an author name.",
        "ru": "Пожалуйста, введите имя автора."
    },
    "poem_not_found": {
        "en": "Poem {} not found.",
        "ru": "Стихотворение {} не найдено."
    },
    "service_unavailable": {
        "en": "Service not available. Please configure LLM provider.",
        "ru": "Сервис недоступен. Пожалуйста, настройте LLM провайдера."
    },
    "unknown_function": {
        "en": "Unknown function: {}",
        "ru": "Неизвестная функция: {}"
    },
    "explanation_error": {
        "en": "Error generating explanation: {}",
        "ru": "Ошибка при генерации объяснения: {}"
    }
}

def get_error_message(key: str, language: str = "en", *args) -> str:
    """Get localized error message"""
    template = ERROR_MESSAGES.get(key, {}).get(language, ERROR_MESSAGES.get(key, {}).get("en", "Error"))
    return template.format(*args) if args else template

def get_english_author_name(russian_name: str) -> str:
    """Get English translation of Russian author name using AuthorMatcher"""
    if author_matcher and russian_name in author_matcher.translation_db:
        return author_matcher.translation_db[russian_name].get("en", russian_name)
    return russian_name

def translate_russian_to_english(russian_text: str) -> str:
    """Translate Russian text to English using LLM with caching"""
    if not russian_text:
        return russian_text
    
    # Check cache first
    if russian_text in translation_cache:
        print(f"[TRANSLATE] Cache hit: '{russian_text}' -> '{translation_cache[russian_text]}'")
        return translation_cache[russian_text]
    
    # Check if LLM is available
    if not explanation_agent:
        print(f"[TRANSLATE] WARNING: explanation_agent not available, returning original: '{russian_text}'")
        return russian_text
    
    try:
        print(f"[TRANSLATE] Translating: '{russian_text}'...")
        messages = [
            {
                "role": "system",
                "content": "You are a translator. Translate Russian names and titles to English. Provide ONLY the English translation, nothing else."
            },
            {
                "role": "user",
                "content": f"Translate to English: {russian_text}"
            }
        ]
        
        translation = explanation_agent.llm.complete(messages, temperature=0.3, max_tokens=100)
        translation = translation.strip().strip('"').strip("'")
        
        # Cache the result
        translation_cache[russian_text] = translation
        print(f"[TRANSLATE] SUCCESS: '{russian_text}' -> '{translation}'")
        return translation
    except Exception as e:
        print(f"[TRANSLATE] ERROR for '{russian_text}': {e}")
        import traceback
        traceback.print_exc()
        return russian_text

def format_author_name_bilingual(russian_name: str, language: str = "en") -> str:
    """Format author name as 'English (Russian)' for English UI, or just Russian for Russian UI"""
    if language != "en":
        return russian_name
    
    # First try the manual translation database
    english_name = get_english_author_name(russian_name)
    if english_name != russian_name:
        result = f"{english_name} ({russian_name})"
        print(f"[AUTHOR_FORMAT] Manual DB: '{russian_name}' -> '{result}'")
        return result
    
    # No manual translation, use LLM
    english_name = translate_russian_to_english(russian_name)
    
    if english_name == russian_name:
        # Translation failed or returned same, return Russian only
        print(f"[AUTHOR_FORMAT] No translation for: '{russian_name}', returning as-is")
        return russian_name
    
    result = f"{english_name} ({russian_name})"
    print(f"[AUTHOR_FORMAT] LLM translated: '{russian_name}' -> '{result}'")
    return result

def l2_normalize(v: np.ndarray) -> np.ndarray:
    v = v.astype("float32")
    v = v.reshape(1, -1)
    v = normalize(v, norm='l2', axis=1)
    return v

def get_llm_agents_with_key(api_key: Optional[str] = None):
    """Get or create LLM agents with optional runtime API key"""
    # If API key provided, create new agents with that key
    if api_key:
        try:
            from utils.llm_provider import get_llm_provider
            all_authors = list(set([m.get("author", "") for m in poem_idmap if m.get("author")]))
            
            temp_matcher = AuthorMatcher(all_authors)
            temp_llm_agent = LLMAgent(
                provider_name="openai",
                model="gpt-4o-mini",
                author_matcher=temp_matcher
            )
            # Override API key in the provider
            if hasattr(temp_llm_agent.llm, 'client'):
                from openai import OpenAI
                temp_llm_agent.llm.client = OpenAI(api_key=api_key)
            
            temp_explanation_agent = ExplanationAgent(
                provider_name="openai",
                model="gpt-4o-mini"
            )
            # Override API key in the provider
            if hasattr(temp_explanation_agent.llm, 'client'):
                from openai import OpenAI
                temp_explanation_agent.llm.client = OpenAI(api_key=api_key)
            
            return temp_llm_agent, temp_explanation_agent, temp_matcher
        except Exception as e:
            print(f"Error creating agents with provided API key: {e}")
            return None, None, None
    
    # Otherwise return global agents (which may be None)
    return llm_agent, explanation_agent, author_matcher

def load_resources():
    global model, poem_index, poem_idmap, poem_embeddings, poems_df
    global author_index, author_map, author_embeddings, author_name_lookup
    global llm_agent, explanation_agent, author_matcher

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading poem artifacts...")
    poem_index = faiss.read_index(str(POEM_INDEX_PATH))
    poem_embeddings = np.load(str(POEM_EMB_PATH))
    with open(IDMAP_PATH, "r", encoding="utf-8") as fh:
        poem_idmap = json.load(fh)
    poems_df = None
    try:
        import pandas as pd
        print(f"Loading poems from {POEMS_PARQUET}...")
        poems_df = pd.read_parquet(POEMS_PARQUET)
        print(f"Loaded {len(poems_df)} poems with columns: {poems_df.columns.tolist()}")
    except Exception as e:
        print(f"Warning: Could not load poems parquet file: {e}")
        poems_df = None

    # load author artifacts if they exist
    if AUTHOR_EMB_PATH.exists() and AUTHOR_MAP_PATH.exists() and AUTHOR_INDEX_PATH.exists():
        print("Loading author artifacts...")
        author_embeddings = np.load(str(AUTHOR_EMB_PATH))
        with open(AUTHOR_MAP_PATH, "r", encoding="utf-8") as fh:
            author_map = json.load(fh)
        author_index = faiss.read_index(str(AUTHOR_INDEX_PATH))
        author_name_lookup = [a["author"] for a in author_map]
    else:
        print("Author artifacts not found. Author search will attempt fuzzy-match using poem metadata.")
        author_embeddings = None
        author_map = None
        author_index = None
        author_name_lookup = [m.get("author","") for m in poem_idmap]
    
    # Initialize LLM-powered components
    print("Initializing LLM agents...")
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = os.getenv("LLM_MODEL", None)
    
    print(f"[DEBUG] LLM_PROVIDER from env: {provider}")
    print(f"[DEBUG] LLM_MODEL from env: {model_name}")
    
    # Build author list for matcher
    all_authors = list(set([m.get("author", "") for m in poem_idmap if m.get("author")]))
    
    try:
        author_matcher = AuthorMatcher(all_authors)
        print(f"[DEBUG] AuthorMatcher initialized with {len(all_authors)} authors")
        
        llm_agent = LLMAgent(
            provider_name=provider,
            model=model_name,
            author_matcher=author_matcher
        )
        print(f"[DEBUG] LLMAgent initialized")
        
        explanation_agent = ExplanationAgent(
            provider_name=provider,
            model=model_name
        )
        print(f"[DEBUG] ExplanationAgent initialized")
        
        print(f"✅ LLM agents initialized successfully with provider: {provider}, model: {model_name}")
    except Exception as e:
        print(f"❌ ERROR initializing LLM agents: {e}")
        print(f"[DEBUG] Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("⚠️  LLM features will be disabled. Using fallback rule-based system.")
        llm_agent = None
        explanation_agent = None
        author_matcher = None
        author_map = None
        author_index = None
        author_name_lookup = [m.get("author","") for m in poem_idmap]

    # Initialize cross-encoder reranker
    try:
        print("Initializing cross-encoder reranker (ms-marco-MiniLM-L-6-v2)...")
        reranker_model = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        global reranker
        reranker = CrossEncoder(reranker_model)
        print("✅ Reranker initialized")
    except Exception as e:
        print(f"⚠️  Reranker initialization failed: {e}. Proceeding without reranking.")
        reranker = None

# map poem index to metadata
def make_poem_result(idx: int, score: float, language: str = "en") -> Dict[str,Any]:
    meta = poem_idmap[idx]
    poem_text = None
    if poems_df is not None:
        try:
            row = poems_df[poems_df['poem_id'] == meta['poem_id']]
            if not row.empty:
                poem_text = row.iloc[0]['text']
        except Exception:
            poem_text = None
    
    # Translate title if in English mode
    russian_title = meta.get("title")
    title_display = russian_title
    if language == "en" and russian_title:
        english_title = translate_russian_to_english(russian_title)
        if english_title != russian_title:
            title_display = f"{english_title} ({russian_title})"
    
    return {
        "poem_id": meta.get("poem_id"),
        "author": meta.get("author"),
        "title": meta.get("title"),
        "title_display": title_display,
        "year": meta.get("year"),
        "score": float(score),
        "text": poem_text
    }

# -------------------
# API endpoints
# -------------------
    # (Deprecated startup event removed; using lifespan handler instead)

@app.get("/health")
def health_check():
    """Health check endpoint for deployment and frontend status checking"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "poem_index_loaded": poem_index is not None,
        "author_index_loaded": author_index is not None
    }

@app.post("/search/poems")
def search_poems(q: TextQuery):
    txt = q.text
    k = q.k
    language = q.language
    
    if not txt:
        raise HTTPException(status_code=400, detail=get_error_message("empty_text", language))

    vec = model.encode([txt], convert_to_numpy=True)
    vec = normalize(vec, norm='l2', axis=1).astype("float32")
    # First-stage retrieval via FAISS
    top_n = max(k * 5, 50)
    D, I = poem_index.search(vec, top_n)
    candidate_idxs = I[0].tolist()
    candidate_scores = D[0].tolist()

    # Optional reranking with cross-encoder using poem text
    reranked = []
    if reranker is not None and poems_df is not None:
        pairs = []
        texts = []
        for idx in candidate_idxs:
            poem_text = None
            try:
                row = poems_df[poems_df['poem_id'] == poem_idmap[idx]['poem_id']]
                if not row.empty:
                    poem_text = row.iloc[0]['text']
            except Exception:
                poem_text = None
            if poem_text:
                pairs.append((txt, poem_text))
                texts.append((idx, poem_text))
            else:
                reranked.append((candidate_scores[candidate_idxs.index(idx)], idx))
        if pairs:
            try:
                ce_scores = reranker.predict(pairs).tolist()
                for (idx, _), s in zip(texts, ce_scores):
                    reranked.append((s, idx))
            except Exception as e:
                print(f"Reranker error: {e}. Falling back to FAISS scores.")
                reranked = list(zip(candidate_scores, candidate_idxs))
        reranked.sort(key=lambda x: -x[0])
    else:
        reranked = list(zip(candidate_scores, candidate_idxs))

    results = []
    for score, idx in reranked[:k]:
        result = make_poem_result(idx, score, language=language)
        if result.get("author") and language == "en":
            russian_author = result["author"]
            result["author_display"] = format_author_name_bilingual(russian_author, language)
            result["author_ru"] = russian_author
        results.append(result)
    return {"query": txt, "results": results}

@app.post("/search/authors")
def search_authors(q: AuthorQuery):
    name = q.author.strip()
    k = q.k
    language = q.language
    
    if not name:
        raise HTTPException(status_code=400, detail=get_error_message("empty_author", language))

    # Try exact/fuzzy match in author_map first
    if author_map:
        # find author index
        match_idx = None
        matched_name = name
        
        # 1. Try exact match
        for i, a in enumerate(author_map):
            if a["author"].lower() == name.lower():
                match_idx = i
                matched_name = a["author"]
                print(f"[SEARCH_AUTHORS] Exact match found: '{name}' -> '{matched_name}'")
                break
        
        # 2. Try fuzzy matching with AuthorMatcher (handles typos)
        if match_idx is None and author_matcher is not None:
            fuzzy_match = author_matcher.match_author(name, threshold=0.6, debug=True)
            if fuzzy_match:
                # Find index of fuzzy matched author
                for i, a in enumerate(author_map):
                    if a["author"] == fuzzy_match:
                        match_idx = i
                        matched_name = fuzzy_match
                        print(f"[SEARCH_AUTHORS] Fuzzy match found: '{name}' -> '{matched_name}' (typo corrected)")
                        break
        
        # 3. Fall back to substring match
        if match_idx is None:
            for i, a in enumerate(author_map):
                if name.lower() in a["author"].lower():
                    match_idx = i
                    matched_name = a["author"]
                    print(f"[SEARCH_AUTHORS] Substring match found: '{name}' -> '{matched_name}'")
                    break
        
        if match_idx is None:
            raise HTTPException(status_code=404, detail=get_error_message("author_not_found", language, name))

        # search author_index for similar authors
        vec = author_embeddings[match_idx:match_idx+1]
        D, I = author_index.search(vec.astype("float32"), k+1)  # +1 because first may be the same author
        authors_out = []
        for score, ai in zip(D[0].tolist(), I[0].tolist()):
            if ai == match_idx:
                continue
            a_meta = author_map[ai]
            # pick up to 3 sample poems for this author
            sample_poems = []
            for pidx in a_meta.get("poem_indices", [])[:3]:
                # Enable title translation according to request language
                sample = make_poem_result(pidx, 0.0, language=language)
                # Add bilingual author name to sample poems
                if sample.get("author") and language == "en":
                    russian_author = sample["author"]
                    sample["author_display"] = format_author_name_bilingual(russian_author, language)
                    sample["author_ru"] = russian_author
                sample_poems.append(sample)
            
            # Format author name with bilingual display for English UI
            author_name = a_meta["author"]
            author_display = format_author_name_bilingual(author_name, language)
            
            authors_out.append({
                "author": author_display,
                "author_ru": author_name,  # Keep Russian name for API consumers
                "count": a_meta.get("count", len(a_meta.get("poem_indices", []))),
                "score": float(score),
                "sample_poems": sample_poems
            })
        
        # Format matched author name too
        matched_display = format_author_name_bilingual(matched_name, language)
        return {"query_author": matched_display, "query_author_ru": matched_name, "results": authors_out[:k]}

    # if author_map missing: fallback to searching poem-level index for poems of the author and returning other authors
    # naive fallback:
    # find poem indices matching author substring
    candidate_indices = [i for i,m in enumerate(poem_idmap) if name.lower() in m.get("author","" ).lower()]
    if not candidate_indices:
        raise HTTPException(status_code=404, detail=get_error_message("author_not_found", language, name))
    # average their embeddings to get author vector
    vec = poem_embeddings[candidate_indices].mean(axis=0, keepdims=True)
    vec = normalize(vec, norm='l2', axis=1).astype("float32")
    D, I = poem_index.search(vec, 100)
    # collect authors and count occurrences
    seen = {}
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        meta = poem_idmap[idx]
        a = meta.get("author","")
        if a == "":
            continue
        if a not in seen:
            seen[a] = {"score": score, "sample": []}
        # Limit samples; translate titles if language is English
        if len(seen[a]["sample"]) < 2:
            seen[a]["sample"].append(make_poem_result(idx, score, language=language))
    # convert to list sorted by score
    authors_out = sorted([{"author":a,"score":v["score"],"sample_poems":v["sample"]} for a,v in seen.items()], key=lambda x: -x["score"])
    return {"query_author": name, "results": authors_out[:k]}

@app.post("/chat")
def chat(q: ChatQuery):
    """Original rule-based chat endpoint (kept for backward compatibility)"""
    txt = q.text
    k = q.k
    intent = detect_intent(txt, known_authors=[a.lower() for a in (author_name_lookup or [])])
    print(f"[CHAT] Query: '{txt}', Intent: {intent}")
    
    # If detect says author_search, try to extract author name
    if intent == "author_search":
        # try to find a known author by substring
        # check author lookup first
        candidate = None
        if author_map:
            candidate = find_author_in_text(txt, [a["author"] for a in author_map])
            print(f"[CHAT] Author candidate from known list: {candidate}")
        else:
            candidate = find_author_in_text(txt, [m.get("author","") for m in poem_idmap])
        if candidate:
            print(f"[CHAT] Routing to search_authors with: {candidate}")
            return search_authors(AuthorQuery(author=candidate, k=k))
        
        # Try to extract author name from phrases like "Find authors similar to X"
        import re
        match = re.search(r'(?:similar to|like|похож.*на|автор)\s+(.+?)(?:\s*$|[,.])', txt, re.I)
        if match:
            potential_author = match.group(1).strip()
            print(f"[CHAT] Extracted author from pattern: {potential_author}")
            return search_authors(AuthorQuery(author=potential_author, k=k))
        
        # maybe the user provided just an author name
        if len(txt.split()) <= 8:
            print(f"[CHAT] Short query, treating as author name: {txt}")
            return search_authors(AuthorQuery(author=txt, k=k))
        # fallback to poem search
    # otherwise poem search
    print(f"[CHAT] Falling through to poem search")
    return search_poems(TextQuery(text=txt, k=k))

@app.post("/chat/llm")
def chat_llm(q: ChatQuery, x_openai_key: Optional[str] = Header(None)):
    """
    LLM-powered chat endpoint with intelligent intent detection and function calling.
    Handles typos, cross-language queries, and varied phrasings.
    """
    language = q.language
    
    # Get appropriate agents (with runtime API key if provided)
    current_llm_agent, _, current_matcher = get_llm_agents_with_key(x_openai_key)
    
    if current_llm_agent is None:
        # Fallback to rule-based if LLM not available
        print("[CHAT/LLM] LLM agent not available, falling back to rule-based chat")
        return chat(q)
    
    txt = q.text
    k = q.k
    
    print(f"[CHAT/LLM] Processing query: '{txt}'")
    
    try:
        # Use LLM to understand query and determine function to call
        agent_response = current_llm_agent.process_query(txt, k=k)
        
        print(f"[CHAT/LLM] Intent detected: {agent_response['intent']}")
        
        if agent_response.get("author_resolution"):
            print(f"[CHAT/LLM] Author resolved: {agent_response['author_resolution']['original']} -> {agent_response['author_resolution']['resolved']}")
        
        # Execute the appropriate function
        function_call = agent_response.get("function_call")
        
        if not function_call:
            # No clear function call, fallback to poem search
            print("[CHAT/LLM] No function call detected, defaulting to poem search")
            return search_poems(TextQuery(text=txt, k=k, language=language))
        
        func_name = function_call["name"]
        func_args = function_call["arguments"]
        
        # Route to appropriate search function
        if func_name == "search_poems_by_content":
            result = search_poems(TextQuery(text=func_args["query"], k=func_args.get("k", k), language=language))
            result["intent"] = "poem_search"
            result["llm_reasoning"] = agent_response.get("reasoning", "")
            return result
        
        elif func_name == "search_similar_authors":
            try:
                result = search_authors(AuthorQuery(author=func_args["author_name"], k=func_args.get("k", k), language=language))
                result["intent"] = "author_search"
                result["llm_reasoning"] = agent_response.get("reasoning", "")
                if agent_response.get("author_resolution"):
                    result["author_resolution"] = agent_response["author_resolution"]
                return result
            except HTTPException as e:
                # Author not found - return friendly error response instead of raising exception
                if e.status_code == 404:
                    return {
                        "query": txt,
                        "author": func_args["author_name"],
                        "results": [],
                        "intent": "author_search",
                        "error": get_error_message("author_not_found", language, func_args["author_name"]),
                        "llm_reasoning": agent_response.get("reasoning", "")
                    }
                raise  # Re-raise other HTTP exceptions
        
        elif func_name == "search_poems_by_author":
            # Search for poems by specific author
            author_name = func_args["author_name"]
            
            # Find poems by this author
            matching_poems = []
            for idx, meta in enumerate(poem_idmap):
                if author_name.lower() in meta.get("author", "").lower():
                    poem_result = make_poem_result(idx, 1.0, language=language)
                    # Add bilingual author name
                    if language == "en":
                        russian_author = poem_result["author"]
                        poem_result["author_display"] = format_author_name_bilingual(russian_author, language)
                        poem_result["author_ru"] = russian_author
                    matching_poems.append(poem_result)
                    if len(matching_poems) >= func_args.get("k", k):
                        break
            
            return {
                "query": txt,
                "author": format_author_name_bilingual(author_name, language) if language == "en" else author_name,
                "author_ru": author_name,
                "results": matching_poems,
                "intent": "author_poems",
                "llm_reasoning": agent_response.get("reasoning", "")
            }
        
        else:
            raise HTTPException(status_code=500, detail=get_error_message("unknown_function", language, func_name))
    
    except Exception as e:
        print(f"[CHAT/LLM] Error: {e}")
        # Fallback to rule-based on error
        print("[CHAT/LLM] Falling back to rule-based chat due to error")
        return chat(q)

@app.post("/explain/poem")
def explain_poem(req: ExplainPoemRequest, x_openai_key: Optional[str] = Header(None)):
    """
    Generate literary explanation for why a specific poem is similar to the query.
    Called on-demand when user clicks 'Explain Similarity' button.
    """
    # Get appropriate agents (with runtime API key if provided)
    _, exp_agent, _ = get_llm_agents_with_key(x_openai_key)
    
    if exp_agent is None:
        raise HTTPException(
            status_code=503,
            detail=get_error_message("service_unavailable", req.language)
        )
    
    # Find the poem in question
    poem = None
    for meta in poem_idmap:
        if meta.get("poem_id") == req.poem_id:
            poem = meta.copy()
            break
    
    if not poem:
        raise HTTPException(status_code=404, detail=get_error_message("poem_not_found", req.language, req.poem_id))
    
    # Get poem text if available
    if poems_df is not None:
        try:
            import pandas as pd
            row = poems_df[poems_df['poem_id'] == req.poem_id]
            if not row.empty:
                poem['text'] = row.iloc[0]['text']
        except Exception as e:
            print(f"Warning: Could not load poem text: {e}")
    
    # Generate explanation
    try:
        explanation = exp_agent.explain_poem_similarity(
            query_text=req.query_text,
            similar_poem=poem,
            similarity_score=req.similarity_score,
            language=req.language
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@app.post("/explain/author")
def explain_author(req: ExplainAuthorRequest, x_openai_key: Optional[str] = Header(None)):
    """
    Generate literary explanation for why two authors are similar.
    Called on-demand when user clicks 'Explain Similarity' button.
    """
    # Get appropriate agents (with runtime API key if provided)
    _, exp_agent, _ = get_llm_agents_with_key(x_openai_key)
    
    if exp_agent is None:
        raise HTTPException(
            status_code=503,
            detail=get_error_message("service_unavailable", req.language)
        )
    
    # Get sample poems
    sample_poems = []
    for poem_id in req.sample_poem_ids[:3]:  # Max 3 samples
        for meta in poem_idmap:
            if meta.get("poem_id") == poem_id:
                poem = meta.copy()
                
                # Get poem text if available
                if poems_df is not None:
                    try:
                        import pandas as pd
                        row = poems_df[poems_df['poem_id'] == poem_id]
                        if not row.empty:
                            poem['text'] = row.iloc[0]['text']
                    except Exception:
                        pass
                
                sample_poems.append(poem)
                break
    
    # Generate explanation
    try:
        explanation = exp_agent.explain_author_similarity(
            query_author=req.query_author,
            similar_author=req.similar_author,
            sample_poems=sample_poems,
            similarity_score=req.similarity_score,
            language=req.language
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=get_error_message("explanation_error", req.language, str(e)))

@app.post("/translate/poem")
def translate_poem(req: TranslatePoemRequest, x_openai_key: Optional[str] = Header(None)):
    """
    Translate a Russian poem to English in a literary way, preserving meter, rhyme, and style.
    Uses LLM to generate high-quality literary translation.
    """
    # Get appropriate agents (with runtime API key if provided)
    _, exp_agent, _ = get_llm_agents_with_key(x_openai_key)
    
    if exp_agent is None:
        raise HTTPException(
            status_code=503,
            detail=get_error_message("service_unavailable", "en")
        )
    
    try:
        # Use the LLM to translate the poem
        messages = [
            {
                "role": "system",
                "content": "You are a literary translator specializing in Russian poetry. Translate to English preserving meter, rhyme, and style."
            },
            {
                "role": "user",
                "content": f"""Translate this Russian poem to English:

{req.poem_text}

Provide only the English translation, no commentary."""
            }
        ]
        
        response = exp_agent.llm.complete(messages, temperature=0.7, max_tokens=800)
        
        return {
            "original": req.poem_text,
            "translation": response,
            "poem_id": req.poem_id
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=get_error_message("explanation_error", "en", str(e)))

@app.post("/match_author")
def match_author(q: MatchAuthorQuery):
    """Lightweight endpoint to quickly resolve an author name from a user query.
    Returns bilingual display if language == 'en'."""
    txt = q.text.strip()
    if not txt:
        raise HTTPException(status_code=400, detail=get_error_message("empty_author", q.language))
    if author_matcher is None:
        raise HTTPException(status_code=503, detail=get_error_message("service_unavailable", q.language))

    # Try direct fuzzy matching on full text (extract best candidate)
    matched = author_matcher.match_author(txt, threshold=0.5, debug=True)
    if not matched:
        # Attempt to extract last capitalized token as heuristic
        import re
        tokens = re.findall(r"[A-Za-zА-Яа-яЁё]+", txt)
        candidate = tokens[-1] if tokens else txt
        matched = author_matcher.match_author(candidate, threshold=0.5, debug=True)

    if not matched:
        return {"matched": False, "reason": "no_match"}

    display = format_author_name_bilingual(matched, q.language)
    return {
        "matched": True,
        "author_ru": matched,
        "author_display": display,
    }

# -------------------
# run with `uvicorn backend.app:app --reload --port 8000`
# -------------------
if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)
