# frontend/streamlit_app.py
import streamlit as st
import requests
import pickle
import os
from typing import List, Dict
from datetime import datetime

# Support environment variable for backend URL (for cloud deployments)
# Try Streamlit secrets first, then environment variable, then default
try:
    API_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))
except:
    API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Poem Recommender", layout="wide", initial_sidebar_state="expanded")

# Backend health check
def check_backend_available(url: str) -> bool:
    """Check if backend is available"""
    try:
        r = requests.get(url.rstrip("/") + "/health", timeout=5)
        return r.status_code == 200
    except:
        return False

# Session persistence helpers
SESSION_CACHE_DIR = ".streamlit_cache"
SESSION_FILE = os.path.join(SESSION_CACHE_DIR, "session.pkl")

def save_session():
    """Save session state to disk"""
    try:
        os.makedirs(SESSION_CACHE_DIR, exist_ok=True)
        cache_data = {
            "messages": st.session_state.messages,
            "explanations": st.session_state.explanations,
            "translations": st.session_state.translations,
            "language": st.session_state.language,
            "use_llm": st.session_state.use_llm,
            "timestamp": datetime.now()
        }
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(cache_data, f)
    except Exception as e:
        print(f"Error saving session: {e}")

def load_session():
    """Load session state from disk"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'rb') as f:
                cache_data = pickle.load(f)
            # Check if cache is less than 24 hours old
            if (datetime.now() - cache_data.get("timestamp", datetime.min)).days < 1:
                return cache_data
    except Exception as e:
        print(f"Error loading session: {e}")
    return None

# Initialize session state
if "messages" not in st.session_state:
    cached = load_session()
    if cached:
        st.session_state.messages = cached.get("messages", [])
        st.session_state.explanations = cached.get("explanations", {})
        st.session_state.translations = cached.get("translations", {})
        st.session_state.language = cached.get("language", "en")
        st.session_state.use_llm = cached.get("use_llm", True)
    else:
        st.session_state.messages = []
        st.session_state.explanations = {}
        st.session_state.translations = {}
        st.session_state.language = "en"
        st.session_state.use_llm = True
if "explanations" not in st.session_state:
    st.session_state.explanations = {}  # Cache explanations by key
if "translations" not in st.session_state:
    st.session_state.translations = {}  # Cache poem translations by poem_id
if "language" not in st.session_state:
    st.session_state.language = "en"
if "use_llm" not in st.session_state:
    st.session_state.use_llm = True
if "api_key_entered" not in st.session_state:
    st.session_state.api_key_entered = False
if "stored_api_key" not in st.session_state:
    st.session_state.stored_api_key = ""

# Translations
TRANSLATIONS = {
    "en": {
        "title": "📜 Poem Recommender",
        "subtitle": "Discover similar poems and authors using AI",
        "settings": "Settings",
        "api_url": "Backend API URL",
        "top_k": "Top k results",
        "force_author": "Force author search",
        "force_poem": "Force poem search",
        "language": "Language",
        "input_placeholder": "Ask a question, paste a poem, or enter an author name...",
        "send": "Send",
        "examples_title": "Examples",
        "example1": "Find authors similar to Pushkin",
        "example2": "Show me poems like this:",
        "example3": "(paste poem text)",
        "example4": "Authors like Akhmatova",
        "querying": "🔍 Searching...",
        "searching_author": "🔍 Finding similar authors...",
        "translating_results": "✨ Found results! Translating names for your convenience...",
        "you": "You",
        "author_results": "Author Results",
        "results": "Results",
        "sample": "Sample",
        "poem_text": "Poem text",
        "poem_sample": "Poem sample",
        "no_text": "Full poem text not available.",
        "count": "count",
        "history": "Chat History",
        "show_history": "Show previous conversations",
        "use_llm": "Use AI-powered search (handles typos & cross-language)",
        "explain_similarity": "🔍 Explain Similarity",
        "explanation": "Literary Analysis",
        "loading_explanation": "Generating literary analysis...",
        "translate_poem": "📖 Translate to English",
        "translation": "English Translation",
        "loading_translation": "Translating poem..."
    },
    "ru": {
        "title": "📜 Рекомендатель стихов",
        "subtitle": "Находите похожие стихи и авторов с помощью ИИ",
        "settings": "Настройки",
        "api_url": "URL бэкенда",
        "top_k": "Количество результатов",
        "force_author": "Искать только авторов",
        "force_poem": "Искать только стихи",
        "language": "Язык",
        "input_placeholder": "Задайте вопрос, вставьте стихотворение или введите имя автора...",
        "send": "Отправить",
        "examples_title": "Примеры",
        "example1": "Найди авторов похожих на Пушкина",
        "example2": "Покажи стихи похожие на это:",
        "example3": "(вставьте текст стихотворения)",
        "example4": "Авторы похожие на Ахматову",
        "querying": "🔍 Поиск...",
        "searching_author": "🔍 Поиск похожих авторов...",
        "translating_results": "✨ Результаты найдены! Перевод имён для удобства...",
        "you": "Вы",
        "author_results": "Результаты поиска авторов",
        "results": "Результаты",
        "sample": "Пример",
        "poem_text": "Текст стихотворения",
        "poem_sample": "Пример стихотворения",
        "no_text": "Полный текст стихотворения недоступен.",
        "count": "количество",
        "history": "История чата",
        "show_history": "Показать предыдущие разговоры",
        "use_llm": "Использовать ИИ-поиск (понимает опечатки и кросс-язык)",
        "explain_similarity": "🔍 Объяснить сходство",
        "explanation": "Литературный анализ",
        "loading_explanation": "Генерация литературного анализа..."
    }
}

lang = st.session_state.language
t = TRANSLATIONS[lang]

# API Key Gate Screen
if not st.session_state.api_key_entered:
    st.title("📜 Poem Recommender")
    st.markdown("### Welcome! Please enter your OpenAI API key to continue")
    st.markdown("""This app requires an OpenAI API key for full functionality including:
    - Semantic search with LLM-powered intent detection
    - Cross-language understanding
    - Author matching and translations
    - Similarity explanations
    """)
    
    with st.form("api_key_form"):
        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Get your API key from https://platform.openai.com/api-keys"
        )
        submit = st.form_submit_button("Continue", type="primary")
        
        if submit:
            if api_key_input and api_key_input.startswith("sk-"):
                st.session_state.stored_api_key = api_key_input
                st.session_state.api_key_entered = True
                st.rerun()
            else:
                st.error("Please enter a valid OpenAI API key (starts with 'sk-')")
    
    st.stop()  # Don't render anything else until key is entered

# Use stored API key
api_key = st.session_state.stored_api_key

# Sidebar
with st.sidebar:
    st.header(t["settings"])
    
    # Show API key status
    st.subheader("🔑 API Configuration")
    if api_key:
        st.success("✅ API Key configured")
        if st.button("Change API Key"):
            st.session_state.api_key_entered = False
            st.session_state.stored_api_key = ""
            st.rerun()
    else:
        st.warning("⚠️ No API key")
    
    st.divider()
    
    # Language selector
    language_options = {"English": "en", "Русский": "ru"}
    selected_lang = st.selectbox(
        t["language"],
        options=list(language_options.keys()),
        index=0 if lang == "en" else 1
    )
    
    # Clear cache button
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.session_state.explanations = {}
        st.session_state.translations = {}
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()
    new_lang = language_options[selected_lang]
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()
    
    st.divider()
    
    # API settings
    api_url = st.text_input(t["api_url"], value=API_URL)
    
    # Backend status check
    backend_status = check_backend_available(api_url)
    if backend_status:
        st.success("✅ Backend connected")
    else:
        st.error("⚠️ Backend not available")
        st.warning("Deploy the backend to use full features. See [DEPLOYMENT.md](DEPLOYMENT.md)")
    
    k = st.slider(t["top_k"], 1, 20, 8)
    
    st.divider()
    
    # Force modes
    st.subheader("Search Mode")
    use_llm = st.checkbox(t["use_llm"], value=st.session_state.use_llm)
    if use_llm != st.session_state.use_llm:
        st.session_state.use_llm = use_llm
    
    author_mode = st.checkbox(t["force_author"], value=False)
    poem_mode = st.checkbox(t["force_poem"], value=False)

    # Similarity score toggle (default off)
    show_scores = st.checkbox("Show similarity scores", value=False)
    st.session_state["show_scores"] = show_scores
    
    st.divider()
    
    # History toggle
    show_history = st.checkbox(t["show_history"], value=False)

# Main content
st.title(t["title"])
st.caption(t["subtitle"])

def get_headers():
    """Get headers with API key if available"""
    headers = {}
    if api_key:
        headers["X-OpenAI-Key"] = api_key
    return headers

def call_chat_api(text: str, k: int = 8, language: str = "en"):
    """Call rule-based chat endpoint"""
    url = api_url.rstrip("/") + "/chat"
    payload = {"text": text, "k": k, "language": language}
    try:
        r = requests.post(url, json=payload, headers=get_headers(), timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "❌ Backend server is not available. Please deploy the backend separately or run it locally. See deployment instructions."}
    except Exception as e:
        return {"error": str(e)}

def call_chat_llm(text: str, k: int = 8, language: str = "en"):
    """Call LLM-powered chat endpoint"""
    url = api_url.rstrip("/") + "/chat/llm"
    payload = {"text": text, "k": k, "language": language}
    try:
        r = requests.post(url, json=payload, headers=get_headers(), timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "❌ Backend server is not available. Please deploy the backend separately or run it locally. See deployment instructions."}
    except Exception as e:
        return {"error": str(e)}

def call_search_poems(text: str, k: int = 8, language: str = "en"):
    url = api_url.rstrip("/") + "/search/poems"
    payload = {"text": text, "k": k, "language": language}
    r = requests.post(url, json=payload, headers=get_headers(), timeout=30)
    r.raise_for_status()
    return r.json()

def call_search_authors(author: str, k: int = 8, language: str = "en"):
    url = api_url.rstrip("/") + "/search/authors"
    payload = {"author": author, "k": k, "language": language}
    # Author search can trigger multiple translations; allow more time
    r = requests.post(url, json=payload, headers=get_headers(), timeout=60)
    r.raise_for_status()
    return r.json()

def call_explain_poem(query_text: str, poem_id, score: float, language: str = "en"):
    """Request explanation for poem similarity"""
    url = api_url.rstrip("/") + "/explain/poem"
    payload = {
        "query_text": query_text,
        "poem_id": poem_id,
        "similarity_score": score,
        "language": language
    }
    r = requests.post(url, json=payload, headers=get_headers(), timeout=60)
    r.raise_for_status()
    return r.json()

def call_explain_author(query_author: str, similar_author: str, score: float, sample_poem_ids: list, language: str = "en"):
    """Request explanation for author similarity"""
    url = api_url.rstrip("/") + "/explain/author"
    payload = {
        "query_author": query_author,
        "similar_author": similar_author,
        "similarity_score": score,
        "sample_poem_ids": sample_poem_ids,
        "language": language
    }
    r = requests.post(url, json=payload, headers=get_headers(), timeout=60)
    r.raise_for_status()
    return r.json()

def call_translate_poem(poem_id, poem_text: str):
    """Request English translation of a Russian poem"""
    url = api_url.rstrip("/") + "/translate/poem"
    payload = {
        "poem_id": poem_id,
        "poem_text": poem_text
    }
    r = requests.post(url, json=payload, headers=get_headers(), timeout=90)
    r.raise_for_status()
    return r.json()

# Input area with modern chat-like interface
with st.container():
    col_input, col_button = st.columns([6, 1])
    
    with col_input:
        user_input = st.text_area(
            label="input",
            placeholder=t["input_placeholder"],
            height=100,
            label_visibility="collapsed"
        )
    
    with col_button:
        st.write("")  # spacing
        st.write("")  # spacing
        submit = st.button(t["send"], use_container_width=True, type="primary")

# Examples in an expander
with st.expander(f"💡 {t['examples_title']}", expanded=False):
    st.markdown(f"- {t['example1']}")
    st.markdown(f"- {t['example2']}")
    st.markdown(f"  {t['example3']}")
    st.markdown(f"- {t['example4']}")

st.divider()

# Process input
if submit and user_input.strip():
    st.session_state.messages.append({"role": "user", "text": user_input})

    lower_q = user_input.lower()
    poem_indicators = ["poem", " стих", "стихо", "verse", "строк"]
    author_indicators = ["author", "authors", "poet", "автор", "поэт"]
    similarity_phrases = ["similar to", "authors like", "authors similar", "похож", "похожие авторы"]

    def is_poem_context():
        return any(tok in lower_q for tok in poem_indicators)

    def is_author_context():
        if any(tok in lower_q for tok in author_indicators):
            return True
        if any(ph in lower_q for ph in similarity_phrases) and not is_poem_context():
            return True
        return False

    author_flag = is_author_context()
    poem_flag = is_poem_context()

    if author_mode:
        search_type = "author"
    elif poem_mode:
        search_type = "poem"
    else:
        if author_flag and not poem_flag:
            search_type = "author"
        elif poem_flag and not author_flag:
            search_type = "poem"
        else:
            search_type = "ambiguous"  # needs LLM routing

    resolved_author = None

    if search_type == "author":
        # Phase 1: quick author resolution
        with st.spinner(t["searching_author"]):
            match_url = api_url.rstrip("/") + "/match_author"
            try:
                r = requests.post(match_url, json={"text": user_input, "language": st.session_state.language}, timeout=15)
                r.raise_for_status()
                match_payload = r.json()
            except Exception as e:
                match_payload = {"matched": False, "error": str(e)}

        if match_payload.get("matched") and match_payload.get("resolved_author"):
            resolved_author = match_payload["resolved_author"]
        else:
            # fallback to poem search
            search_type = "poem"

    if search_type == "author" and resolved_author:
        # Phase 2: similar authors search (two-phase UX)
        # Show immediate success message before longer translation phase
        if st.session_state.language == "en":
            st.success(f"✓ Author found: {resolved_author}. Translating names & fetching similarities...")
        else:
            st.success(f"✓ Автор найден: {resolved_author}. Переводим имена и ищем похожих авторов...")
        with st.spinner(t["translating_results"] if st.session_state.language == "en" else t["querying"]):
            try:
                resp = call_search_authors(resolved_author, k=k, language=st.session_state.language)
                # include resolution info for rendering
                resp["author_resolution"] = {"original": user_input, "resolved": resolved_author}
                st.session_state.messages.append({"role": "assistant", "type": "author_results", "payload": resp, "query": user_input})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "type": "error", "payload": str(e)})

    elif search_type == "ambiguous":
        # Let LLM decide route; it returns either poem or author style results
        with st.spinner(t["querying"]):
            try:
                resp = call_chat_llm(user_input, k=k, language=st.session_state.language)
                st.session_state.messages.append({"role": "assistant", "type": "chat_results", "payload": resp, "query": user_input})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "type": "error", "payload": str(e)})

    else:  # poem search
        with st.spinner(t["querying"]):
            try:
                if poem_mode:  # direct vector poem search
                    resp = call_search_poems(user_input, k=k, language=st.session_state.language)
                    st.session_state.messages.append({"role": "assistant", "type": "poem_results", "payload": resp, "query": user_input})
                else:
                    if st.session_state.use_llm:
                        resp = call_chat_llm(user_input, k=k, language=st.session_state.language)
                    else:
                        resp = call_chat_api(user_input, k=k, language=st.session_state.language)
                    st.session_state.messages.append({"role": "assistant", "type": "chat_results", "payload": resp, "query": user_input})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "type": "error", "payload": str(e)})

    save_session()
    st.rerun()

# Display messages
messages_to_show = st.session_state.messages if show_history else st.session_state.messages[-2:] if len(st.session_state.messages) > 0 else []

for msg_idx, msg in enumerate(reversed(messages_to_show)):
    real_idx = len(st.session_state.messages) - len(messages_to_show) + msg_idx
    
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg['text'])
    else:
        with st.chat_message("assistant"):
            payload = msg.get("payload", {})
            original_query = msg.get("query", "")
            
            # Check for errors first
            if payload.get("error"):
                st.error(payload["error"])
                # Show LLM reasoning even if there's an error
                if payload.get("llm_reasoning"):
                    with st.expander("🤖 AI Reasoning", expanded=False):
                        st.info(payload["llm_reasoning"])
                continue  # Skip rendering results if there's an error
            
            # Show LLM reasoning if available
            if payload.get("llm_reasoning"):
                with st.expander("🤖 AI Reasoning", expanded=False):
                    st.info(payload["llm_reasoning"])
            
            # Show author resolution if happened
            if payload.get("author_resolution"):
                st.success(f"✓ Understood '{payload['author_resolution']['original']}' as '{payload['author_resolution']['resolved']}'")
            
            # Check for author results FIRST (before poem results)
            if msg.get("type") == "author_results" or (msg.get("type") == "chat_results" and payload.get("query_author")):
                results = payload.get("results", [])
                # Use bilingual query author if available
                query_author = payload.get("query_author", original_query)
                
                # Show a friendly message when results are ready with translations
                if results and st.session_state.language == "en":
                    st.success(f"✨ Found {len(results)} similar authors! Names translated for your convenience.")
                
                st.markdown(f"**{t['author_results']}**")
                
                for a_idx, a in enumerate(results):
                    # Use bilingual author name if available (for English UI)
                    author_name = a.get('author')  # This is already formatted as bilingual by backend
                    author_ru = a.get('author_ru', author_name)  # Fallback to author if author_ru not present
                    score = a.get('score', 0.0)
                    
                    # Author header with explain button
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        # Removed count display per user request
                        score_text = f" — score {score:.3f}" if st.session_state.get("show_scores", False) else ""
                        st.write(f"**{author_name}**{score_text}")
                    with col2:
                        explain_key = f"author_{real_idx}_{a_idx}"
                        if st.button(t["explain_similarity"], key=f"btn_{explain_key}", use_container_width=True):
                            # Request explanation (use Russian name for explanation API)
                            with st.spinner(t["loading_explanation"]):
                                try:
                                    sample_ids = [p.get('poem_id') for p in a.get("sample_poems", [])]
                                    explanation = call_explain_author(
                                        query_author=payload.get("query_author_ru", query_author),
                                        similar_author=author_ru,
                                        score=score,
                                        sample_poem_ids=sample_ids,
                                        language=st.session_state.language
                                    )
                                    st.session_state.explanations[explain_key] = explanation
                                    save_session()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    # Show explanation if available
                    if explain_key in st.session_state.explanations:
                        with st.container():
                            st.markdown(f"**{t['explanation']}:**")
                            st.markdown(st.session_state.explanations[explain_key]["explanation"])
                    
                    # Show sample poems
                    for p_idx, p in enumerate(a.get("sample_poems", [])):
                        # Use bilingual author name for sample poem
                        sample_author = p.get('author_display', p.get('author'))
                        sample_title = p.get('title_display', p.get('title')) or '(no title)'
                        with st.expander(f"{t['sample']}: {sample_title} — {sample_author}"):
                            if p.get("text"):
                                st.text_area(t["poem_sample"], value=p.get("text"), height=140, key=f"sample_{real_idx}_{a_idx}_{p_idx}", label_visibility="collapsed")
                                
                                # Add translation button for English UI
                                if st.session_state.language == "en" and p.get('poem_id'):
                                    translate_key = f"trans_{p.get('poem_id')}"
                                    if translate_key not in st.session_state.translations:
                                        if st.button(t["translate_poem"], key=f"btn_trans_sample_{real_idx}_{a_idx}_{p_idx}"):
                                            with st.spinner(t["loading_translation"]):
                                                try:
                                                    translation_result = call_translate_poem(p.get('poem_id'), p.get('text'))
                                                    st.session_state.translations[translate_key] = translation_result["translation"]
                                                    save_session()
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Translation error: {e}")
                                    else:
                                        st.markdown(f"**{t['translation']}:**")
                                        st.text_area("Translation", value=st.session_state.translations[translate_key], height=140, key=f"sample_trans_{real_idx}_{a_idx}_{p_idx}", label_visibility="collapsed")
                            else:
                                st.write(t["no_text"])
            
            elif msg.get("type") == "poem_results" or (msg.get("type") == "chat_results" and payload.get("results")):
                results = payload.get("results", [])
                
                # Show a friendly message when results are ready with translations
                if results and st.session_state.language == "en":
                    st.success(f"✨ Found {len(results)} similar poems! Titles translated for your convenience.")
                
                st.markdown(f"**{t['results']}**")
                
                for r_idx, r in enumerate(results):
                    poem_id = r.get('poem_id')
                    # Use translated title if available
                    poem_title = r.get('title_display', r.get('title')) or '(no title)'
                    # Use bilingual author name if available (for English UI)
                    poem_author = r.get('author_display', r.get('author'))
                    score = r.get('score', 0.0)
                    text = r.get("text")
                    
                    # Header with title, author, score, and explain button
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        score_text = f" — score {score:.3f}" if st.session_state.get("show_scores", False) else ""
                        st.write(f"**{poem_title}** — {poem_author}{score_text}")
                    with col2:
                        explain_key = f"poem_{real_idx}_{r_idx}"
                        if st.button(t["explain_similarity"], key=f"btn_{explain_key}", use_container_width=True):
                            with st.spinner(t["loading_explanation"]):
                                try:
                                    explanation = call_explain_poem(
                                        query_text=original_query,
                                        poem_id=poem_id,
                                        score=score,
                                        language=st.session_state.language
                                    )
                                    st.session_state.explanations[explain_key] = explanation
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    # Show explanation if available
                    if explain_key in st.session_state.explanations:
                        st.markdown(f"**{t['explanation']}:**")
                        exp = st.session_state.explanations[explain_key]
                        st.markdown(exp["explanation"])
                        if exp.get("themes"):
                            st.write("**Themes:** " + ", ".join(exp["themes"]))
                    
                    # Poem text in expander
                    with st.expander(f"📖 {t['poem_text']}"):
                        if text:
                            st.text_area(t["poem_text"], value=text, height=160, key=f"poem_{real_idx}_{r_idx}", label_visibility="collapsed")
                            
                            # Add translation button for English UI
                            if st.session_state.language == "en":
                                translate_key = f"trans_{poem_id}"
                                if translate_key not in st.session_state.translations:
                                    if st.button(t["translate_poem"], key=f"btn_trans_{real_idx}_{r_idx}"):
                                        with st.spinner(t["loading_translation"]):
                                            try:
                                                translation_result = call_translate_poem(poem_id, text)
                                                st.session_state.translations[translate_key] = translation_result["translation"]
                                                save_session()
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Translation error: {e}")
                                else:
                                    st.markdown(f"**{t['translation']}:**")
                                    st.text_area("Translation", value=st.session_state.translations[translate_key], height=160, key=f"poem_trans_{real_idx}_{r_idx}", label_visibility="collapsed")
                        else:
                            st.write(t["no_text"])
            
            elif msg.get("type") == "error":
                st.error(f"Error: {payload}")
            else:
                st.write(payload)
