# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
XML parsing for function calls.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def remove_think_blocks(text: str) -> str:
    """
    Temporarily remove all <think>...</think> blocks for XML parsing.
    Supports nested think tags.
    Note: This function is only used for temporary parsing and does not affect the original content returned to the user.
    """
    while '<think>' in text and '</think>' in text:
        start_pos = text.find('<think>')
        if start_pos == -1:
            break
        
        pos = start_pos + 7
        depth = 1
        
        while pos < len(text) and depth > 0:
            if text[pos:pos + 7] == '<think>':
                depth += 1
                pos += 7
            elif text[pos:pos + 8] == '</think>':
                depth -= 1
                pos += 8
            else:
                pos += 1
        
        if depth == 0:
            text = text[:start_pos] + text[pos:]
        else:
            break
    
    return text


def parse_function_calls_xml(xml_string: str, trigger_signal: str) -> Optional[List[Dict[str, Any]]]:
    """
    Enhanced XML parsing function, supports dynamic trigger signals.
    1. Retain <think>...</think> blocks (they should be returned normally to the user)
    2. Temporarily remove think blocks only when parsing function_calls to prevent think content from interfering with XML parsing
    3. Find the last occurrence of the trigger signal
    4. Start parsing function_calls from the last trigger signal
    """
    logger.debug(f"🔧 Improved parser starting processing, input length: {len(xml_string) if xml_string else 0}")
    logger.debug(f"🔧 Using trigger signal: {trigger_signal[:20]}...")
    
    if not xml_string or trigger_signal not in xml_string:
        logger.debug(f"🔧 Input is empty or doesn't contain trigger signal")
        return None
    
    cleaned_content = remove_think_blocks(xml_string)
    logger.debug(f"🔧 Content length after temporarily removing think blocks: {len(cleaned_content)}")
    
    signal_positions = []
    start_pos = 0
    while True:
        pos = cleaned_content.find(trigger_signal, start_pos)
        if pos == -1:
            break
        signal_positions.append(pos)
        start_pos = pos + 1
    
    if not signal_positions:
        logger.debug(f"🔧 No trigger signal found in cleaned content")
        return None
    
    logger.debug(f"🔧 Found {len(signal_positions)} trigger signal positions: {signal_positions}")
    
    last_signal_pos = signal_positions[-1]
    content_after_signal = cleaned_content[last_signal_pos:]
    logger.debug(f"🔧 Content starting from last trigger signal: {repr(content_after_signal[:100])}")
    
    calls_content_match = re.search(r"<function_calls>([\s\S]*?)</function_calls>", content_after_signal)
    if not calls_content_match:
        logger.debug(f"🔧 No function_calls tag found")
        return None
    
    calls_content = calls_content_match.group(1)
    logger.debug(f"🔧 function_calls content: {repr(calls_content)}")
    
    results = []
    call_blocks = re.findall(r"<function_call>([\s\S]*?)</function_call>", calls_content)
    logger.debug(f"🔧 Found {len(call_blocks)} function_call blocks")
    
    for i, block in enumerate(call_blocks):
        logger.debug(f"🔧 Processing function_call #{i + 1}: {repr(block)}")
        
        tool_match = re.search(r"<tool>(.*?)</tool>", block)
        if not tool_match:
            logger.debug(f"🔧 No tool tag found in block #{i + 1}")
            continue
        
        name = tool_match.group(1).strip()
        args = {}
        
        args_block_match = re.search(r"<args>([\s\S]*?)</args>", block)
        if args_block_match:
            args_content = args_block_match.group(1)
            # Support arg tag names containing hyphens (e.g., -i, -A); match any non-space, non-'>' and non-'/' chars
            arg_matches = re.findall(r"<([^\s>/]+)>([\s\S]*?)</\1>", args_content)

            def _coerce_value(v: str):
                try:
                    return json.loads(v)
                except Exception:
                    pass
                return v

            for k, v in arg_matches:
                args[k] = _coerce_value(v)
        
        result = {"name": name, "args": args}
        results.append(result)
        logger.debug(f"🔧 Added tool call: {result}")
    
    logger.debug(f"🔧 Final parsing result: {results}")
    return results if results else None

