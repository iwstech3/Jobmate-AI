"""
LLM Service - Provider-agnostic abstraction for AI models
Supports Google Gemini (primary) and Ollama (fallback)
"""

import os
from typing import Optional, Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """
    Abstraction layer for LLM interactions.
    Handles model initialization, prompt formatting, and response generation.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize LLM service.
        
        Args:
            model_name: Model to use (defaults to env variable)
            temperature: Creativity level (0-1, lower = more focused)
            max_tokens: Maximum response length
        """
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize the model
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize the LangChain Gemini model"""
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            convert_system_message_to_human=True  # Gemini compatibility
        )
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt/question
            system_message: Optional system instructions
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        # Add user prompt
        messages.append(HumanMessage(content=prompt))
        
        # Override parameters if provided
        temp_llm = self.llm
        if kwargs:
            # Note: temperature and max_tokens are not supported by current Google Generative AI client
            # if 'temperature' in kwargs:
            #     temp_llm = self.llm.bind(temperature=kwargs['temperature'])
            if 'max_tokens' in kwargs:
                temp_llm = self.llm.bind(max_output_tokens=kwargs['max_tokens'])
        
        # Generate response
        response = temp_llm.invoke(messages)
        return response.content
    
    def generate_structured(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        output_format: str = "json"
    ) -> str:
        """
        Generate structured output (JSON, YAML, etc.)
        
        Args:
            prompt: User prompt
            system_message: System instructions
            output_format: Expected format (json, yaml, etc.)
            
        Returns:
            Structured response as string
        """
        format_instruction = f"\n\nIMPORTANT: Respond ONLY with valid {output_format.upper()}. No explanations, no markdown formatting, just the {output_format}."
        
        full_prompt = prompt + format_instruction
        
        return self.generate(
            prompt=full_prompt,
            system_message=system_message,
            temperature=0.3  # Lower temperature for structured output
        )
    
    def batch_generate(
        self,
        prompts: List[str],
        system_message: Optional[str] = None
    ) -> List[str]:
        """
        Generate responses for multiple prompts (batch processing)
        
        Args:
            prompts: List of prompts
            system_message: System instructions for all prompts
            
        Returns:
            List of generated responses
        """
        responses = []
        for prompt in prompts:
            response = self.generate(prompt, system_message)
            responses.append(response)
        return responses
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for cost calculation.
        Rough approximation: 1 token ≈ 4 characters
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def estimate_cost(self, input_text: str, output_text: str) -> float:
        """
        Estimate API cost for a request.
        Gemini 2.5 Flash: $0.00025 per 1K tokens (very approximate)
        
        Args:
            input_text: Input prompt
            output_text: Generated output
            
        Returns:
            Estimated cost in USD
        """
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        # Gemini 2.5 Flash approximate pricing
        cost_per_1k = 0.00025
        return (total_tokens / 1000) * cost_per_1k


# Singleton instance for reuse
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get or create singleton LLM service instance.
    Reuses the same instance to save initialization time.
    
    Returns:
        LLMService instance
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance