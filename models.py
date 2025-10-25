# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Pydantic models for API requests and responses.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, ConfigDict


class ToolFunction(BaseModel):
    """Function definition for a tool."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]


class Tool(BaseModel):
    """Tool definition."""
    type: Literal["function"]
    function: ToolFunction


class Message(BaseModel):
    """Message in a conversation."""
    model_config = ConfigDict(extra="allow")
    
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ToolChoice(BaseModel):
    """Tool choice specification."""
    type: Literal["function"]
    function: Dict[str, str]


class ChatCompletionRequest(BaseModel):
    """OpenAI chat completion request."""
    model_config = ConfigDict(extra="allow")
    
    model: str
    messages: List[Dict[str, Any]]
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, ToolChoice]] = None
    stream: Optional[bool] = False
    stream_options: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    n: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None


class AnthropicMessage(BaseModel):
    """Anthropic Messages API request model."""
    model_config = ConfigDict(extra="allow")
    
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: int  # Required in Anthropic API
    system: Optional[Union[str, List[Dict[str, Any]]]] = None  # Can be string or array with cache_control
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: Optional[bool] = False
    stop_sequences: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None

