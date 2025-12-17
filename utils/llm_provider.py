# utils/llm_provider.py
"""
Interoperable LLM provider abstraction.
Supports: Ollama (local), OpenAI (GPT), Anthropic (Claude), xAI (Grok)
Easy to switch between providers via config.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os


class LLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate completion from messages"""
        pass
    
    @abstractmethod
    def complete_with_functions(
        self, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate completion with function calling support"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider (local, free)"""
    
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("Please install requests: pip install requests")
    
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate completion using Ollama API"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = self.requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["message"]["content"]
    
    def complete_with_functions(
        self, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Ollama doesn't have native function calling, so we simulate it
        by instructing the model to output JSON with function calls
        """
        # Add system message with function schemas
        function_prompt = self._create_function_calling_prompt(functions)
        
        enhanced_messages = [
            {"role": "system", "content": function_prompt}
        ] + messages
        
        response_text = self.complete(enhanced_messages, temperature, max_tokens=1000)
        
        # Parse the response to extract function calls
        try:
            parsed = json.loads(response_text)
            return {
                "content": parsed.get("reasoning", ""),
                "function_call": parsed.get("function_call"),
                "finish_reason": "function_call" if parsed.get("function_call") else "stop"
            }
        except json.JSONDecodeError:
            # If model didn't return valid JSON, treat as regular completion
            return {
                "content": response_text,
                "function_call": None,
                "finish_reason": "stop"
            }
    
    def _create_function_calling_prompt(self, functions: List[Dict[str, Any]]) -> str:
        """Create a system prompt that instructs the model to use functions"""
        func_descriptions = []
        for func in functions:
            func_descriptions.append(
                f"- {func['name']}: {func['description']}\n"
                f"  Parameters: {json.dumps(func['parameters'], indent=2)}"
            )
        
        functions_text = "\n".join(func_descriptions)
        
        return f"""You are a helpful assistant with access to the following functions:

{functions_text}

When you need to use a function, respond with a JSON object in this exact format:
{{
    "reasoning": "Brief explanation of why you're calling this function",
    "function_call": {{
        "name": "function_name",
        "arguments": {{
            "param1": "value1",
            "param2": "value2"
        }}
    }}
}}

If you don't need to call a function, just respond normally without JSON."""


class OpenAIProvider(LLMProvider):
    """OpenAI provider (GPT models)"""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate completion using OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def complete_with_functions(
        self, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate completion with native function calling"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=functions,
            temperature=temperature
        )
        
        message = response.choices[0].message
        
        result = {
            "content": message.content or "",
            "function_call": None,
            "finish_reason": response.choices[0].finish_reason
        }
        
        if message.function_call:
            result["function_call"] = {
                "name": message.function_call.name,
                "arguments": json.loads(message.function_call.arguments)
            }
        
        return result


class AnthropicProvider(LLMProvider):
    """Anthropic provider (Claude models)"""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        self.model = model
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate completion using Anthropic API"""
        # Anthropic requires system message separate
        system_msg = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg,
            messages=user_messages
        )
        
        return response.content[0].text
    
    def complete_with_functions(
        self, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Claude has tool calling support"""
        # Convert functions to Claude's tool format
        tools = []
        for func in functions:
            tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"]
            })
        
        # Separate system message
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=temperature,
            system=system_msg,
            messages=user_messages,
            tools=tools
        )
        
        result = {
            "content": "",
            "function_call": None,
            "finish_reason": response.stop_reason
        }
        
        # Extract text and tool calls
        for block in response.content:
            if block.type == "text":
                result["content"] = block.text
            elif block.type == "tool_use":
                result["function_call"] = {
                    "name": block.name,
                    "arguments": block.input
                }
                result["finish_reason"] = "tool_use"
        
        return result


class XAIProvider(LLMProvider):
    """xAI provider (Grok models) - uses OpenAI-compatible API"""
    
    def __init__(self, model: str = "grok-beta", api_key: Optional[str] = None):
        self.model = model
        try:
            from openai import OpenAI
            # xAI uses OpenAI-compatible API with different base URL
            self.client = OpenAI(
                api_key=api_key or os.getenv("XAI_API_KEY"),
                base_url="https://api.x.ai/v1"
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate completion using xAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def complete_with_functions(
        self, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """xAI supports function calling via OpenAI-compatible API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=functions,
            temperature=temperature
        )
        
        message = response.choices[0].message
        
        result = {
            "content": message.content or "",
            "function_call": None,
            "finish_reason": response.choices[0].finish_reason
        }
        
        if message.function_call:
            result["function_call"] = {
                "name": message.function_call.name,
                "arguments": json.loads(message.function_call.arguments)
            }
        
        return result


def get_llm_provider(provider_name: str = "ollama", **kwargs) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider.
    
    Args:
        provider_name: One of "ollama", "openai", "anthropic", "xai"
        **kwargs: Provider-specific arguments (model, api_key, etc.)
    
    Returns:
        LLMProvider instance
    
    Example:
        >>> llm = get_llm_provider("ollama", model="llama3.1")
        >>> llm = get_llm_provider("openai", model="gpt-4o-mini")
        >>> llm = get_llm_provider("anthropic", model="claude-3-5-sonnet-20241022")
    """
    providers = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,  # alias
        "xai": XAIProvider,
        "grok": XAIProvider  # alias
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(providers.keys())}"
        )
    
    return provider_class(**kwargs)
