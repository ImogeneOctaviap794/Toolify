# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Streaming detection and parsing for function calls.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple

from .parser import parse_function_calls_xml

logger = logging.getLogger(__name__)


class StreamingFunctionCallDetector:
    """Enhanced streaming function call detector, supports dynamic trigger signals, avoids misjudgment within <think> tags.
    
    Core features:
    1. Avoid triggering tool call detection within <think> blocks
    2. Normally output <think> block content to the user
    3. Supports nested think tags
    """
    
    def __init__(self, trigger_signal: str):
        self.trigger_signal = trigger_signal
        self.reset()
    
    def reset(self):
        self.content_buffer = ""
        self.state = "detecting"  # detecting, tool_parsing
        self.in_think_block = False
        self.think_depth = 0
        self.signal = self.trigger_signal
        self.signal_len = len(self.signal)
    
    def process_chunk(self, delta_content: str) -> Tuple[bool, str]:
        """
        Process streaming content chunk.
        Returns: (is_tool_call_detected, content_to_yield)
        """
        if not delta_content:
            return False, ""
        
        self.content_buffer += delta_content
        content_to_yield = ""
        
        if self.state == "tool_parsing":
            return False, ""
        
        if delta_content:
            logger.debug(
                f"🔧 Processing chunk: {repr(delta_content[:50])}{'...' if len(delta_content) > 50 else ''}, buffer length: {len(self.content_buffer)}, think state: {self.in_think_block}")
        
        i = 0
        while i < len(self.content_buffer):
            skip_chars = self._update_think_state(i)
            if skip_chars > 0:
                for j in range(skip_chars):
                    if i + j < len(self.content_buffer):
                        content_to_yield += self.content_buffer[i + j]
                i += skip_chars
                continue
            
            if not self.in_think_block and self._can_detect_signal_at(i):
                if self.content_buffer[i:i + self.signal_len] == self.signal:
                    logger.debug(
                        f"🔧 Improved detector: detected trigger signal in non-think block! Signal: {self.signal[:20]}...")
                    logger.debug(
                        f"🔧 Trigger signal position: {i}, think state: {self.in_think_block}, think depth: {self.think_depth}")
                    self.state = "tool_parsing"
                    self.content_buffer = self.content_buffer[i:]
                    return True, content_to_yield
            
            remaining_len = len(self.content_buffer) - i
            if remaining_len < self.signal_len or remaining_len < 8:
                break
            
            content_to_yield += self.content_buffer[i]
            i += 1
        
        self.content_buffer = self.content_buffer[i:]
        return False, content_to_yield
    
    def _update_think_state(self, pos: int):
        """Update think tag state, supports nesting."""
        remaining = self.content_buffer[pos:]
        
        if remaining.startswith('<think>'):
            self.think_depth += 1
            self.in_think_block = True
            logger.debug(f"🔧 Entering think block, depth: {self.think_depth}")
            return 7
        
        elif remaining.startswith('</think>'):
            self.think_depth = max(0, self.think_depth - 1)
            self.in_think_block = self.think_depth > 0
            logger.debug(f"🔧 Exiting think block, depth: {self.think_depth}")
            return 8
        
        return 0
    
    def _can_detect_signal_at(self, pos: int) -> bool:
        """Check if signal can be detected at the specified position."""
        return (pos + self.signal_len <= len(self.content_buffer) and 
                not self.in_think_block)
    
    def finalize(self) -> Optional[List[Dict[str, Any]]]:
        """Final processing when stream ends."""
        if self.state == "tool_parsing":
            return parse_function_calls_xml(self.content_buffer, self.trigger_signal)
        return None

