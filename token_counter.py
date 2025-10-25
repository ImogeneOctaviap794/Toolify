# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Token counting functionality using tiktoken.
"""

import logging
import tiktoken

logger = logging.getLogger(__name__)


class TokenCounter:
    """Token counter using tiktoken."""
    
    # Model prefix to encoding mapping (from tiktoken source)
    MODEL_PREFIX_TO_ENCODING = {
        "o1-": "o200k_base",
        "o3-": "o200k_base",
        "o4-mini-": "o200k_base",
        # chat
        "gpt-5-": "o200k_base",
        "gpt-4.5-": "o200k_base",
        "gpt-4.1-": "o200k_base",
        "chatgpt-4o-": "o200k_base",
        "gpt-4o-": "o200k_base",
        "gpt-4-": "cl100k_base",
        "gpt-3.5-turbo-": "cl100k_base",
        "gpt-35-turbo-": "cl100k_base",  # Azure deployment name
        "gpt-oss-": "o200k_harmony",
        # fine-tuned
        "ft:gpt-4o": "o200k_base",
        "ft:gpt-4": "cl100k_base",
        "ft:gpt-3.5-turbo": "cl100k_base",
        "ft:davinci-002": "cl100k_base",
        "ft:babbage-002": "cl100k_base",
    }
    
    def __init__(self):
        self.encoders = {}
    
    def get_encoder(self, model: str):
        """Get or create encoder for the model."""
        if model not in self.encoders:
            encoding = None
            
            # First try to get encoding from model name directly
            try:
                self.encoders[model] = tiktoken.encoding_for_model(model)
                return self.encoders[model]
            except KeyError:
                pass
            
            # Try to find encoding by prefix matching
            for prefix, enc_name in self.MODEL_PREFIX_TO_ENCODING.items():
                if model.startswith(prefix):
                    encoding = enc_name
                    break
            
            # Default to o200k_base for newer models
            if encoding is None:
                logger.warning(f"Model {model} not found in prefix mapping, using o200k_base encoding")
                encoding = "o200k_base"
            
            try:
                self.encoders[model] = tiktoken.get_encoding(encoding)
            except Exception as e:
                logger.warning(f"Failed to get encoding {encoding} for model {model}: {e}. Falling back to cl100k_base")
                self.encoders[model] = tiktoken.get_encoding("cl100k_base")
                
        return self.encoders[model]
    
    def count_tokens(self, messages: list, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in message list."""
        encoder = self.get_encoder(model)
        
        # All modern chat models use similar token counting
        return self._count_chat_tokens(messages, encoder, model)
    
    def _count_chat_tokens(self, messages: list, encoder, model: str) -> int:
        """Accurate token calculation for chat models.
        
        Based on OpenAI's token counting documentation:
        - Each message has a fixed overhead
        - Content tokens are counted per message
        - Special tokens for message formatting
        """
        # Token overhead varies by model
        if model.startswith(("gpt-3.5-turbo", "gpt-35-turbo")):
            # gpt-3.5-turbo uses different message overhead
            tokens_per_message = 4  # <|start|>role<|separator|>content<|end|>
            tokens_per_name = -1  # Name is omitted if not present
        else:
            # Most models including gpt-4, gpt-4o, o1, etc.
            tokens_per_message = 3
            tokens_per_name = 1
        
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            
            # Count tokens for each field in the message
            for key, value in message.items():
                if key == "content":
                    # Handle case where content might be a list (multimodal messages)
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and item.get("type") == "text":
                                content_text = item.get("text", "")
                                num_tokens += len(encoder.encode(content_text))
                            # Note: Image tokens are not counted here as they have fixed costs
                    elif isinstance(value, str):
                        num_tokens += len(encoder.encode(value))
                elif key == "name":
                    num_tokens += tokens_per_name
                    if isinstance(value, str):
                        num_tokens += len(encoder.encode(value))
                elif key == "role":
                    # Role is already counted in tokens_per_message
                    pass
                elif isinstance(value, str):
                    # Other string fields
                    num_tokens += len(encoder.encode(value))
        
        # Every reply is primed with assistant role
        num_tokens += 3
        return num_tokens
    
    def count_text_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in plain text."""
        encoder = self.get_encoder(model)
        return len(encoder.encode(text))

