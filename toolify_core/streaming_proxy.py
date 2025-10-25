# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Streaming proxy for handling streaming responses with function calling.
"""

import os
import json
import uuid
import logging
import httpx
from typing import List, Dict, Any

from .function_calling import StreamingFunctionCallDetector, parse_function_calls_xml
from .tool_mapping import store_tool_call_mapping

logger = logging.getLogger(__name__)


async def stream_proxy_with_fc_transform(
    url: str,
    body: dict,
    headers: dict,
    model: str,
    has_fc: bool,
    trigger_signal: str,
    http_client: httpx.AsyncClient,
    timeout: int
):
    """
    Enhanced streaming proxy, supports dynamic trigger signals, avoids misjudgment within think tags.
    """
    logger.info(f"📝 Starting streaming response from: {url}")
    logger.info(f"📝 Function calling enabled: {has_fc}")

    if not has_fc or not trigger_signal:
        try:
            async with http_client.stream("POST", url, json=body, headers=headers, timeout=timeout) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
        except httpx.RemoteProtocolError:
            logger.debug("🔧 Upstream closed connection prematurely, ending stream response")
            return
        return

    detector = StreamingFunctionCallDetector(trigger_signal)

    def _prepare_tool_calls(parsed_tools: List[Dict[str, Any]]):
        tool_calls = []
        for i, tool in enumerate(parsed_tools):
            tool_call_id = f"call_{uuid.uuid4().hex}"
            store_tool_call_mapping(
                tool_call_id,
                tool["name"],
                tool["args"],
                f"Calling tool {tool['name']}"
            )
            tool_calls.append({
                "index": i, "id": tool_call_id, "type": "function",
                "function": {"name": tool["name"], "arguments": json.dumps(tool["args"])}
            })
        return tool_calls

    def _build_tool_call_sse_chunks(parsed_tools: List[Dict[str, Any]], model_id: str) -> List[str]:
        tool_calls = _prepare_tool_calls(parsed_tools)
        chunks: List[str] = []

        initial_chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex}", "object": "chat.completion.chunk",
            "created": int(os.path.getmtime(__file__)), "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": None, "tool_calls": tool_calls},
                         "finish_reason": None}],
        }
        chunks.append(f"data: {json.dumps(initial_chunk)}\n\n")

        final_chunk = {
             "id": f"chatcmpl-{uuid.uuid4().hex}", "object": "chat.completion.chunk",
            "created": int(os.path.getmtime(__file__)), "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
        }
        chunks.append(f"data: {json.dumps(final_chunk)}\n\n")
        chunks.append("data: [DONE]\n\n")
        return chunks

    try:
        async with http_client.stream("POST", url, json=body, headers=headers, timeout=timeout) as response:
            print(f"\n{'='*80}")
            print(f"🔍 UPSTREAM STREAMING RESPONSE")
            print(f"{'='*80}")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"{'='*80}\n")
            
            if response.status_code != 200:
                error_content = await response.aread()
                print(f"❌ Error content: {error_content.decode('utf-8', errors='ignore')}")
                logger.error(f"❌ Upstream service stream response error: status_code={response.status_code}")
                logger.error(f"❌ Upstream error details: {error_content.decode('utf-8', errors='ignore')}")
                
                if response.status_code == 401:
                    error_message = "Authentication failed"
                elif response.status_code == 403:
                    error_message = "Access forbidden"
                elif response.status_code == 429:
                    error_message = "Rate limit exceeded"
                elif response.status_code >= 500:
                    error_message = "Upstream service temporarily unavailable"
                else:
                    error_message = "Request processing failed"
                
                error_chunk = {"error": {"message": error_message, "type": "upstream_error"}}
                yield f"data: {json.dumps(error_chunk)}\n\n".encode('utf-8')
                yield b"data: [DONE]\n\n"
                return

            line_count = 0
            async for line in response.aiter_lines():
                line_count += 1
                if line_count <= 10:  # 打印前10行
                    print(f"📥 Upstream line #{line_count}: {line[:200] if len(line) > 200 else line}")
                
                if detector.state == "tool_parsing":
                    if line.startswith("data:"):
                        line_data = line[len("data: "):].strip()
                        if line_data and line_data != "[DONE]":
                            try:
                                chunk_json = json.loads(line_data)
                                delta_content = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content",
                                                                                                        "") or ""
                                detector.content_buffer += delta_content
                                # Early termination: once </function_calls> appears, parse and finish immediately
                                if "</function_calls>" in detector.content_buffer:
                                    logger.debug("🔧 Detected </function_calls> in stream, finalizing early...")
                                    parsed_tools = detector.finalize()
                                    if parsed_tools:
                                        logger.debug(f"🔧 Early finalize: parsed {len(parsed_tools)} tool calls")
                                        for sse in _build_tool_call_sse_chunks(parsed_tools, model):
                                            yield sse.encode('utf-8')
                                        return
                                    else:
                                        logger.error("❌ Early finalize failed to parse tool calls")
                                        error_content = "Error: Detected tool use signal but failed to parse function call format"
                                        error_chunk = {"id": "error-chunk",
                                                       "choices": [{"delta": {"content": error_content}}]}
                                        yield f"data: {json.dumps(error_chunk)}\n\n".encode('utf-8')
                                        yield b"data: [DONE]\n\n"
                                        return
                            except (json.JSONDecodeError, IndexError):
                                pass
                    continue
                
                if line.startswith("data:"):
                    line_data = line[len("data: "):].strip()
                    if not line_data or line_data == "[DONE]":
                        continue
                    
                    try:
                        chunk_json = json.loads(line_data)
                        delta_content = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "") or ""
                        
                        if delta_content:
                            is_detected, content_to_yield = detector.process_chunk(delta_content)
                            
                            if content_to_yield:
                                yield_chunk = {
                                    "id": f"chatcmpl-passthrough-{uuid.uuid4().hex}",
                                    "object": "chat.completion.chunk",
                                    "created": int(os.path.getmtime(__file__)),
                                    "model": model,
                                    "choices": [{"index": 0, "delta": {"content": content_to_yield}}]
                                }
                                yield f"data: {json.dumps(yield_chunk)}\n\n".encode('utf-8')
                            
                            if is_detected:
                                # Tool call signal detected, switch to parsing mode
                                continue
                    
                    except (json.JSONDecodeError, IndexError):
                        yield line + "\n\n"

    except httpx.RemoteProtocolError as e:
        logger.error(f"❌ Remote protocol error (connection closed): {e}")
        logger.error(f"❌ This usually means the upstream server closed the connection prematurely")
        logger.debug("🔧 Upstream closed connection prematurely, ending stream response")
        # Don't send error to client, just end the stream gracefully
        return
    
    except httpx.RequestError as e:
        logger.error(f"❌ Failed to connect to upstream service: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        
        error_message = "Failed to connect to upstream service"
        error_chunk = {"error": {"message": error_message, "type": "connection_error"}}
        yield f"data: {json.dumps(error_chunk)}\n\n".encode('utf-8')
        yield b"data: [DONE]\n\n"
        return

    if detector.state == "tool_parsing":
        logger.debug(f"🔧 Stream ended, starting to parse tool call XML...")
        parsed_tools = detector.finalize()
        if parsed_tools:
            logger.debug(f"🔧 Streaming processing: Successfully parsed {len(parsed_tools)} tool calls")
            for sse in _build_tool_call_sse_chunks(parsed_tools, model):
                yield sse
            return
        else:
            logger.error(
                f"❌ Detected tool call signal but XML parsing failed, buffer content: {detector.content_buffer}")
            error_content = "Error: Detected tool use signal but failed to parse function call format"
            error_chunk = {"id": "error-chunk", "choices": [{"delta": {"content": error_content}}]}
            yield f"data: {json.dumps(error_chunk)}\n\n".encode('utf-8')

    elif detector.state == "detecting" and detector.content_buffer:
        # If stream has ended but buffer still has remaining characters insufficient to form signal, output them
        final_yield_chunk = {
            "id": f"chatcmpl-finalflush-{uuid.uuid4().hex}", "object": "chat.completion.chunk",
            "created": int(os.path.getmtime(__file__)), "model": model,
            "choices": [{"index": 0, "delta": {"content": detector.content_buffer}}]
        }
        yield f"data: {json.dumps(final_yield_chunk)}\n\n".encode('utf-8')

    yield b"data: [DONE]\n\n"

