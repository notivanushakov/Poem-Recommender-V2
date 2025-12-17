# utils/llm_agent.py
"""
LLM-powered agent for intelligent query processing with function calling.
Handles intent detection, author name resolution, and query routing.
"""

from typing import List, Dict, Any, Optional
from .llm_provider import LLMProvider, get_llm_provider
from .author_matcher import AuthorMatcher
import json


# Function schemas for LLM function calling
FUNCTION_SCHEMAS = [
    {
        "name": "search_poems_by_content",
        "description": """Search for poems similar to given text, theme, or description. 
        Use this when:
        - User provides poem text (multi-line or quoted text)
        - User describes themes/emotions (love, nature, sadness, freedom, etc.)
        - User asks for poems similar to a given text
        - User wants to find poems matching a mood or style""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The poem text, theme, or description to search for. Can be in English or Russian."
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_similar_authors",
        "description": """Find authors with similar writing style to a given author.
        Use this when:
        - User asks for authors similar to/like a specific author
        - User wants to discover new authors based on a known one
        - User compares authors (e.g., 'authors like Pushkin')""",
        "parameters": {
            "type": "object",
            "properties": {
                "author_name": {
                    "type": "string",
                    "description": "Name of the author to find similar ones. Can be in English or Russian, typos are OK."
                },
                "k": {
                    "type": "integer",
                    "description": "Number of similar authors to return (default: 8)",
                    "default": 8
                }
            },
            "required": ["author_name"]
        }
    },
    {
        "name": "search_poems_by_author",
        "description": """Get poems by a specific author.
        Use this when:
        - User asks to see/show/find poems BY a specific author
        - User wants to explore an author's work
        - User asks 'show me Pushkin's poems' or similar""",
        "parameters": {
            "type": "object",
            "properties": {
                "author_name": {
                    "type": "string",
                    "description": "Name of the author. Can be in English or Russian."
                },
                "k": {
                    "type": "integer",
                    "description": "Number of poems to return (default: 10)",
                    "default": 10
                }
            },
            "required": ["author_name"]
        }
    }
]


class LLMAgent:
    """
    Intelligent agent that uses LLM to understand queries and route them
    to appropriate search functions.
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        author_matcher: Optional[AuthorMatcher] = None,
        provider_name: str = "ollama",
        model: str = None
    ):
        """
        Args:
            llm_provider: Pre-configured LLM provider (optional)
            author_matcher: AuthorMatcher instance for name resolution
            provider_name: Provider to use if llm_provider not given
            model: Model name (provider-specific)
        """
        if llm_provider is None:
            # Auto-configure based on provider_name
            if model is None:
                model = {
                    "ollama": "llama3.1",
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "xai": "grok-beta"
                }.get(provider_name, "llama3.1")
            
            self.llm = get_llm_provider(provider_name, model=model)
        else:
            self.llm = llm_provider
        
        self.author_matcher = author_matcher
    
    def process_query(self, user_query: str, k: int = 10) -> Dict[str, Any]:
        """
        Process user query and determine appropriate function to call.
        
        Args:
            user_query: Natural language query from user
            k: Default number of results
        
        Returns:
            Dict with:
                - intent: Detected intent
                - function_call: Function to call with arguments
                - reasoning: Why this function was chosen (for debugging)
        """
        # Build messages for LLM
        messages = [
            {
                "role": "system",
                "content": """Poetry search assistant. Call functions:
- search_poems_by_content: for poem text/themes
- search_similar_authors: for "similar to X"
- search_poems_by_author: for "poems by X"
Handle English/Russian names and typos."""
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
        
        # Get LLM response with function calling
        response = self.llm.complete_with_functions(
            messages=messages,
            functions=FUNCTION_SCHEMAS,
            temperature=0.2  # Lower temp = less tokens, more consistent
        )
        
        result = {
            "intent": "unknown",
            "function_call": None,
            "reasoning": response.get("content", ""),
            "raw_response": response
        }
        
        # Extract function call if present
        if response.get("function_call"):
            func_call = response["function_call"]
            func_name = func_call["name"]
            func_args = func_call.get("arguments", {})
            
            # Resolve author names if needed
            if "author_name" in func_args and self.author_matcher:
                original_name = func_args["author_name"]
                resolved_name = self.author_matcher.match_author(original_name, debug=True)
                
                if resolved_name:
                    func_args["author_name"] = resolved_name
                    result["author_resolution"] = {
                        "original": original_name,
                        "resolved": resolved_name
                    }
                else:
                    print(f"[LLMAgent] WARNING: Could not resolve author name '{original_name}'")
            
            # Set default k if not provided
            if "k" not in func_args:
                func_args["k"] = k
            
            result["intent"] = func_name
            result["function_call"] = {
                "name": func_name,
                "arguments": func_args
            }
        
        return result
    
    def generate_search_summary(self, query: str, results: List[Dict], search_type: str) -> str:
        """
        Generate a brief natural language summary of search results.
        
        Args:
            query: Original user query
            results: Search results (poems or authors)
            search_type: "poems" or "authors"
        
        Returns:
            Natural language summary
        """
        if not results:
            return f"No {search_type} found matching your query."
        
        count = len(results)
        
        if search_type == "poems":
            prompt = f"""User searched for: "{query}"

Found {count} similar poems. Generate a brief (1-2 sentences) summary.

Sample results:
{self._format_poem_samples(results[:3])}

Keep it concise and engaging."""
        
        else:  # authors
            prompt = f"""User searched for authors similar to: "{query}"

Found {count} similar authors. Generate a brief (1-2 sentences) summary.

Authors found: {', '.join([r.get('author', 'Unknown') for r in results[:5]])}

Keep it concise and engaging."""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant for a poetry recommendation system."},
            {"role": "user", "content": prompt}
        ]
        
        summary = self.llm.complete(messages, temperature=0.7, max_tokens=100)
        return summary.strip()
    
    def _format_poem_samples(self, poems: List[Dict]) -> str:
        """Format poem samples for display"""
        formatted = []
        for i, poem in enumerate(poems, 1):
            title = poem.get('title', 'Untitled')
            author = poem.get('author', 'Unknown')
            formatted.append(f"{i}. '{title}' by {author}")
        return "\n".join(formatted)


class ExplanationAgent:
    """
    Specialized agent for generating explanations of why poems/authors are similar.
    This is called on-demand when user clicks "Explain Similarity" button.
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        provider_name: str = "ollama",
        model: str = None
    ):
        if llm_provider is None:
            if model is None:
                model = {
                    "ollama": "llama3.1",
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "xai": "grok-beta"
                }.get(provider_name, "llama3.1")
            
            self.llm = get_llm_provider(provider_name, model=model)
        else:
            self.llm = llm_provider
    
    def explain_poem_similarity(
        self,
        query_text: Optional[str],
        similar_poem: Dict[str, Any],
        similarity_score: float,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Explain why a specific poem is similar to the query.
        
        Args:
            query_text: Original query (poem text or theme)
            similar_poem: The similar poem found (with text, author, title)
            similarity_score: Embedding similarity score
            language: Language for explanation ("en" or "ru")
        
        Returns:
            Dict with explanation, themes, and analysis
        """
        poem_text = similar_poem.get('text', '')
        poem_title = similar_poem.get('title', 'Untitled')
        poem_author = similar_poem.get('author', 'Unknown')
        
        # Truncate texts if too long
        query_display = (query_text[:500] + "...") if query_text and len(query_text) > 500 else query_text
        poem_display = (poem_text[:500] + "...") if len(poem_text) > 500 else poem_text
        
        # Language-specific prompt
        if language == "ru":
            lang_instruction = "Объясни сходство на русском языке в 2-3 абзацах: темы, стиль, эмоции. Будь кратким и точным."
            system_msg = "Эксперт по русской поэзии. Отвечай на русском."
        else:
            lang_instruction = "Write your ENTIRE response in ENGLISH ONLY. Explain similarity in 2-3 concise paragraphs: themes, style, emotion. Be brief and precise."
            system_msg = "Russian poetry expert. You MUST write in English language only."
        
        prompt = f"""Literary analysis of Russian poetry similarity.

{"Query: " + query_display[:200] if query_text else ""}

Poem: "{poem_title}" by {poem_author}
{poem_display[:300]}

Score: {similarity_score:.3f}

{lang_instruction}"""

        messages = [
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        explanation = self.llm.complete(messages, temperature=0.7, max_tokens=400)
        
        # Extract themes (simple keyword extraction from explanation)
        themes = self._extract_themes(explanation)
        
        return {
            "explanation": explanation.strip(),
            "themes": themes,
            "similarity_score": similarity_score,
            "poem_title": poem_title,
            "poem_author": poem_author
        }
    
    def explain_author_similarity(
        self,
        query_author: str,
        similar_author: str,
        sample_poems: List[Dict],
        similarity_score: float,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Explain why two authors are similar.
        
        Args:
            query_author: Original author queried
            similar_author: Similar author found
            sample_poems: Sample poems from the similar author
            similarity_score: Similarity score
            language: Language for explanation ("en" or "ru")
        
        Returns:
            Dict with explanation and analysis
        """
        # Format sample poems
        samples_text = ""
        for i, poem in enumerate(sample_poems[:2], 1):
            samples_text += f"\nPoem {i}: {poem.get('title', 'Untitled')}\n"
            text = poem.get('text', '')
            samples_text += (text[:300] + "...") if len(text) > 300 else text
            samples_text += "\n"
        
        # Language-specific prompt
        if language == "ru":
            lang_instruction = "Объясни сходство на русском языке в 2-3 абзацах: стиль, темы, период. Будь кратким и точным."
            system_msg = "Эксперт по русской поэзии. Отвечай на русском."
        else:
            lang_instruction = "Write your ENTIRE response in ENGLISH ONLY. Explain similarity in 2-3 concise paragraphs: style, themes, period. Be brief and precise."
            system_msg = "Russian poetry expert. You MUST write in English language only."
        
        prompt = f"""Compare Russian poets: {query_author} vs {similar_author}

Score: {similarity_score:.3f}

Samples:{samples_text[:400]}

{lang_instruction}"""

        messages = [
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        explanation = self.llm.complete(messages, temperature=0.7, max_tokens=400)
        
        return {
            "explanation": explanation.strip(),
            "query_author": query_author,
            "similar_author": similar_author,
            "similarity_score": similarity_score
        }
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract theme keywords from explanation text"""
        # Common themes in Russian poetry
        theme_keywords = [
            "love", "любовь", "nature", "природа", "death", "смерть",
            "freedom", "свобода", "patriotism", "патриотизм", "loneliness", "одиночество",
            "nostalgia", "ностальгия", "revolution", "революция", "war", "война",
            "beauty", "красота", "suffering", "страдание", "hope", "надежда",
            "melancholy", "меланхолия", "romanticism", "романтизм", "symbolism", "символизм"
        ]
        
        text_lower = text.lower()
        found_themes = []
        
        for theme in theme_keywords:
            if theme in text_lower:
                found_themes.append(theme.capitalize())
        
        # Remove duplicates and return up to 5 themes
        return list(dict.fromkeys(found_themes))[:5]
