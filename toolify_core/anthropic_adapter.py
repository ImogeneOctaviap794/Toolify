# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Anthropic API format conversion utilities.
"""

import json
import uuid
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def anthropic_to_openai_request(anthropic_req: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Anthropic request format to OpenAI format."""
    openai_req = {
        "model": anthropic_req.get("model", "gpt-4"),
        "messages": [],
        "stream": anthropic_req.get("stream", False)
    }
    
    # Handle system message (can be string or array with cache_control)
    if "system" in anthropic_req and anthropic_req["system"]:
        system_content = anthropic_req["system"]
        
        # If system is an array (with cache_control), extract text content
        if isinstance(system_content, list):
            text_parts = []
            for block in system_content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            system_text = "\n\n".join(text_parts) if text_parts else ""
        else:
            # Simple string format
            system_text = system_content
        
        if system_text:
            openai_req["messages"].append({
                "role": "system",
                "content": system_text
            })
    
    # Add messages
    for msg in anthropic_req.get("messages", []):
        # Handle tool_result messages (Anthropic format)
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            # Convert content array to OpenAI format
            text_parts = []
            for content_block in msg["content"]:
                if content_block.get("type") == "text":
                    text_parts.append(content_block.get("text", ""))
                elif content_block.get("type") == "tool_result":
                    # Convert tool_result to tool message
                    openai_req["messages"].append({
                        "role": "tool",
                        "tool_call_id": content_block.get("tool_use_id", ""),
                        "content": content_block.get("content", "")
                    })
            if text_parts:
                openai_req["messages"].append({
                    "role": "user",
                    "content": " ".join(text_parts)
                })
        else:
            # Regular message
            content = msg.get("content")
            if isinstance(content, list):
                # Extract text from content array
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                content = " ".join(text_parts) if text_parts else ""
            
            openai_req["messages"].append({
                "role": msg.get("role"),
                "content": content
            })
    
    # Convert tools from Anthropic to OpenAI format
    if "tools" in anthropic_req and anthropic_req["tools"]:
        openai_tools = []
        for tool in anthropic_req["tools"]:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)
        openai_req["tools"] = openai_tools
        logger.debug(f"🔧 Converted {len(openai_tools)} Anthropic tools to OpenAI format")
    
    # Map parameters
    if "max_tokens" in anthropic_req:
        openai_req["max_tokens"] = anthropic_req["max_tokens"]
    if "temperature" in anthropic_req:
        openai_req["temperature"] = anthropic_req["temperature"]
    if "top_p" in anthropic_req:
        openai_req["top_p"] = anthropic_req["top_p"]
    if "stop_sequences" in anthropic_req:
        openai_req["stop"] = anthropic_req["stop_sequences"]
    
    return openai_req


def openai_to_anthropic_response(openai_resp: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
    """Convert OpenAI response format to Anthropic format."""
    if stream:
        # For streaming, we'll handle this in the streaming function
        return openai_resp
    
    # Non-streaming response
    choice = openai_resp.get("choices", [{}])[0]
    message = choice.get("message", {})
    finish_reason = choice.get("finish_reason")
    
    # Build content array
    content = []
    
    # Add text content if present
    if message.get("content"):
        content.append({
            "type": "text",
            "text": message.get("content")
        })
    
    # Convert tool_calls to Anthropic's tool_use format
    if message.get("tool_calls"):
        for tool_call in message["tool_calls"]:
            if tool_call.get("type") == "function":
                function = tool_call.get("function", {})
                try:
                    # Parse arguments JSON string to dict
                    args = json.loads(function.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                
                content.append({
                    "type": "tool_use",
                    "id": tool_call.get("id", f"toolu_{uuid.uuid4().hex}"),
                    "name": function.get("name", ""),
                    "input": args
                })
        logger.debug(f"🔧 Converted {len(message['tool_calls'])} tool_calls to Anthropic tool_use format")
    
    # If no content at all, add empty text
    if not content:
        content.append({
            "type": "text",
            "text": ""
        })
    
    # Map finish_reason
    if finish_reason == "tool_calls":
        stop_reason = "tool_use"
    elif finish_reason == "stop":
        stop_reason = "end_turn"
    elif finish_reason == "length":
        stop_reason = "max_tokens"
    else:
        stop_reason = finish_reason or "end_turn"
    
    anthropic_resp = {
        "id": openai_resp.get("id", f"msg_{uuid.uuid4().hex}"),
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": openai_resp.get("model", ""),
        "stop_reason": stop_reason,
        "usage": {
            "input_tokens": openai_resp.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": openai_resp.get("usage", {}).get("completion_tokens", 0)
        }
    }
    
    return anthropic_resp


async def stream_openai_to_anthropic(openai_stream_generator):
    """Convert OpenAI streaming response to Anthropic streaming format."""
    logger.debug("🔧 Starting OpenAI to Anthropic stream conversion")
    
    # Send message_start event
    message_id = f"msg_{uuid.uuid4().hex}"
    message_start = {
        'type': 'message_start',
        'message': {
            'id': message_id,
            'type': 'message',
            'role': 'assistant',
            'content': [],
            'model': '',
            'usage': {'input_tokens': 0, 'output_tokens': 0}
        }
    }
    yield f"event: message_start\ndata: {json.dumps(message_start)}\n\n"
    logger.debug(f"🔧 Sent message_start event: {message_id}")
    
    # Track current content block
    current_block_index = 0
    current_block_type = None
    tool_call_started = False
    current_tool_call = {}
    chunk_count = 0
    
    try:
        async for chunk in openai_stream_generator:
            chunk_count += 1
            logger.debug(f"🔧 Processing chunk #{chunk_count}, size: {len(chunk) if isinstance(chunk, bytes) else 'N/A'} bytes")
            
            if chunk.startswith(b"data: "):
                try:
                    line_data = chunk[6:].decode('utf-8').strip()
                    logger.debug(f"🔧 Decoded chunk data: {line_data[:100]}{'...' if len(line_data) > 100 else ''}")
                    
                    if line_data == "[DONE]":
                        logger.debug("🔧 Received [DONE] marker, finalizing stream")
                        # Send content_block_stop and message_stop events
                        if current_block_type:
                            stop_event = {'type': 'content_block_stop', 'index': current_block_index}
                            yield f"event: content_block_stop\ndata: {json.dumps(stop_event)}\n\n"
                            logger.debug(f"🔧 Sent content_block_stop: {stop_event}")
                        
                        # Determine stop_reason based on last block type
                        stop_reason = "tool_use" if current_block_type == "tool_use" else "end_turn"
                        delta_event = {'type': 'message_delta', 'delta': {'stop_reason': stop_reason}, 'usage': {'output_tokens': 0}}
                        yield f"event: message_delta\ndata: {json.dumps(delta_event)}\n\n"
                        logger.debug(f"🔧 Sent message_delta with stop_reason: {stop_reason}")
                        
                        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
                        logger.debug("🔧 Sent message_stop event")
                        break
                elif line_data:
                    # Handle multiple JSON objects in one line (split by newline if present)
                    json_parts = line_data.split('\n')
                    chunk_json = None
                    
                    for json_part in json_parts:
                        json_part = json_part.strip()
                        if not json_part:
                            continue
                        
                        try:
                            chunk_json = json.loads(json_part)
                            # Use the last valid JSON (most recent data)
                        except json.JSONDecodeError as e:
                            # Try to extract the first complete JSON object
                            try:
                                # Find the end of first JSON object
                                decoder = json.JSONDecoder()
                                obj, idx = decoder.raw_decode(json_part)
                                chunk_json = obj
                                # Ignore the extra data after first JSON
                                if idx < len(json_part):
                                    logger.debug(f"🔧 Extracted first JSON from multi-object chunk (ignored {len(json_part) - idx} chars)")
                            except:
                                logger.warning(f"⚠️ Failed to parse JSON: {e}, data: {json_part[:200]}")
                                continue
                    
                    if not chunk_json:
                        continue
                        
                        if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                            choice = chunk_json["choices"][0]
                            delta = choice.get("delta", {})
                            logger.debug(f"🔧 Delta content: role={delta.get('role')}, content={bool(delta.get('content'))}, tool_calls={bool(delta.get('tool_calls'))}")
                            
                            # Handle text content
                            content = delta.get("content", "")
                            if content:
                                if current_block_type != "text":
                                    # Start new text block
                                    if current_block_type:
                                        yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': current_block_index})}\n\n"
                                        current_block_index += 1
                                    current_block_type = "text"
                                    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': current_block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                                
                                # Send content_block_delta event
                                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': current_block_index, 'delta': {'type': 'text_delta', 'text': content}})}\n\n"
                            
                            # Handle tool_calls
                            tool_calls = delta.get("tool_calls")
                            if tool_calls:
                                for tool_call_delta in tool_calls:
                                    tc_index = tool_call_delta.get("index", 0)
                                    
                                    # Start new tool_use block if needed
                                    if not tool_call_started or current_block_type != "tool_use":
                                        if current_block_type and current_block_type != "tool_use":
                                            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': current_block_index})}\n\n"
                                            current_block_index += 1
                                        
                                        current_block_type = "tool_use"
                                        tool_call_started = True
                                        
                                        # Initialize tool call tracking
                                        tool_id = tool_call_delta.get("id", f"toolu_{uuid.uuid4().hex}")
                                        current_tool_call = {"id": tool_id, "name": "", "input": ""}
                                        
                                        # Get function name and id
                                        if "function" in tool_call_delta:
                                            func = tool_call_delta["function"]
                                            if "name" in func:
                                                current_tool_call["name"] = func["name"]
                                        
                                    # Send tool_use start event
                                    start_event = {
                                        'type': 'content_block_start',
                                        'index': current_block_index,
                                        'content_block': {
                                            'type': 'tool_use',
                                            'id': current_tool_call['id'],
                                            'name': current_tool_call['name'],
                                            'input': {}
                                        }
                                    }
                                    yield f"event: content_block_start\ndata: {json.dumps(start_event)}\n\n"
                                    
                                    # Accumulate function arguments
                                    if "function" in tool_call_delta:
                                        func = tool_call_delta["function"]
                                        if "arguments" in func:
                                            args_chunk = func["arguments"]
                                            current_tool_call["input"] += args_chunk
                                            # Send input delta
                                            yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': current_block_index, 'delta': {'type': 'input_json_delta', 'partial_json': args_chunk}})}\n\n"
                            
                            # Handle finish_reason
                            finish_reason = choice.get("finish_reason")
                            if finish_reason:
                                # This will be handled in [DONE]
                                pass
                                
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                    logger.warning(f"⚠️ Error parsing streaming chunk: {e}, chunk: {chunk[:200] if isinstance(chunk, bytes) else chunk}")
                    pass
    
    except Exception as e:
        logger.error(f"❌ Stream conversion error: {type(e).__name__}: {e}")
        logger.error(f"❌ Processed {chunk_count} chunks before error")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        # Send error event to client
        error_event = {
            'type': 'error',
            'error': {
                'type': 'api_error',
                'message': f'Stream conversion error: {str(e)}'
            }
        }
        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
    finally:
        logger.debug(f"🔧 Stream conversion completed, total chunks: {chunk_count}")

