# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Main FastAPI application for Toolify middleware.
Refactored for better modularity and maintainability.
"""

import os
import json
import uuid
import httpx
import traceback
import time
import logging
import yaml
from typing import List, Dict, Any

from fastapi import FastAPI, Request, Header, HTTPException, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Toolify modules
from toolify_core.models import ChatCompletionRequest, AnthropicMessage, Tool, ToolFunction
from toolify_core.token_counter import TokenCounter
from config_loader import config_loader, AppConfig
from admin_auth import (
    LoginRequest, LoginResponse, verify_admin_token,
    verify_password, create_access_token, get_admin_credentials
)
from toolify_core.function_calling import (
    generate_function_prompt,
    generate_random_trigger_signal,
    parse_function_calls_xml
)
from toolify_core.tool_mapping import store_tool_call_mapping
from toolify_core.anthropic_adapter import (
    anthropic_to_openai_request,
    openai_to_anthropic_response,
    stream_openai_to_anthropic
)
from toolify_core.message_processor import (
    preprocess_messages,
    validate_message_structure,
    safe_process_tool_choice
)
from toolify_core.upstream_router import find_upstream
from toolify_core.streaming_proxy import stream_proxy_with_fc_transform

logger = logging.getLogger(__name__)

# Global variables
app_config: AppConfig = None
MODEL_TO_SERVICE_MAPPING: Dict[str, List[Dict[str, Any]]] = {}
ALIAS_MAPPING: Dict[str, List[str]] = {}
DEFAULT_SERVICE: Dict[str, Any] = {}
ALLOWED_CLIENT_KEYS: List[str] = []
GLOBAL_TRIGGER_SIGNAL: str = ""
token_counter = TokenCounter()


def load_runtime_config(reload: bool = False):
    """Load or reload runtime configuration and derived globals."""
    global app_config, MODEL_TO_SERVICE_MAPPING, ALIAS_MAPPING, DEFAULT_SERVICE
    global ALLOWED_CLIENT_KEYS, GLOBAL_TRIGGER_SIGNAL

    if reload:
        app_config = config_loader.reload_config()
        logger.info("🔄 Reloaded configuration from disk")
    else:
        app_config = config_loader.load_config()
    
    log_level_str = app_config.features.log_level
    if log_level_str == "DISABLED":
        log_level = logging.CRITICAL + 1
    else:
        log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Configure logging (avoid adding duplicate handlers on reload)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        root_logger.setLevel(log_level)
    
    logger.info(f"✅ Configuration loaded successfully: {config_loader.config_path}")
    logger.info(f"📊 Configured {len(app_config.upstream_services)} upstream services")
    logger.info(f"🔑 Configured {len(app_config.client_authentication.allowed_keys)} client keys")
    
    MODEL_TO_SERVICE_MAPPING, ALIAS_MAPPING = config_loader.get_model_to_service_mapping()
    DEFAULT_SERVICE = config_loader.get_default_service()
    ALLOWED_CLIENT_KEYS = config_loader.get_allowed_client_keys()
    GLOBAL_TRIGGER_SIGNAL = generate_random_trigger_signal()
    
    logger.info(f"🎯 Configured {len(MODEL_TO_SERVICE_MAPPING)} model mappings")
    if ALIAS_MAPPING:
        logger.info(f"🔄 Configured {len(ALIAS_MAPPING)} model aliases: {list(ALIAS_MAPPING.keys())}")
    logger.info(f"🔄 Default service: {DEFAULT_SERVICE['name']}")


# Load configuration at startup
try:
    load_runtime_config()
except Exception as e:
    logger.error(f"❌ Configuration loading failed: {type(e).__name__}")
    logger.error(f"❌ Error details: {str(e)}")
    logger.error("💡 Please ensure config.yaml file exists and is properly formatted")
    exit(1)


# Initialize FastAPI app
app = FastAPI()
http_client = httpx.AsyncClient()

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    """Middleware for debugging validation errors, does not log conversation content."""
    response = await call_next(request)
    
    if response.status_code == 422:
        logger.debug(f"🔍 Validation error detected for {request.method} {request.url.path}")
        logger.debug(f"🔍 Response status code: 422 (Pydantic validation failure)")
    
    return response


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors with detailed error information."""
    logger.error("=" * 80)
    logger.error("❌ Pydantic Validation Error")
    logger.error("=" * 80)
    logger.error(f"📍 Request URL: {request.url}")
    logger.error(f"📍 Request Method: {request.method}")
    
    # Log request headers
    logger.error(f"📋 Request Headers:")
    for header_name, header_value in request.headers.items():
        if header_name.lower() == "authorization":
            logger.error(f"   {header_name}: Bearer ***{header_value[-8:] if len(header_value) > 8 else '***'}")
        else:
            logger.error(f"   {header_name}: {header_value}")
    
    # Try to read and log the raw request body
    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8')
        logger.error(f"📦 Raw Request Body (first 1000 chars):")
        logger.error(body_text[:1000])
        if len(body_text) > 1000:
            logger.error(f"   ... (total {len(body_text)} chars)")
    except Exception as e:
        logger.error(f"⚠️  Could not read request body: {e}")
    
    logger.error(f"🔴 Validation Errors ({len(exc.errors())} error(s)):")
    for i, error in enumerate(exc.errors(), 1):
        logger.error(f"   Error {i}:")
        logger.error(f"      Location: {' -> '.join(str(loc) for loc in error.get('loc', []))}")
        logger.error(f"      Message: {error.get('msg')}")
        logger.error(f"      Type: {error.get('type')}")
        if 'input' in error:
            input_repr = repr(error['input'])
            logger.error(f"      Input: {input_repr[:200]}{'...' if len(input_repr) > 200 else ''}")
    logger.error("=" * 80)
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Invalid request format",
                "type": "invalid_request_error",
                "code": "invalid_request",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"❌ Unhandled exception: {exc}")
    logger.error(f"❌ Request URL: {request.url}")
    logger.error(f"❌ Exception type: {type(exc).__name__}")
    logger.error(f"❌ Error stack: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "server_error",
                "code": "internal_error"
            }
        }
    )


async def verify_api_key(authorization: str = Header(...)):
    """Dependency: verify client API key."""
    client_key = authorization.replace("Bearer ", "")
    if app_config.features.key_passthrough:
        # In passthrough mode, skip allowed_keys check
        return client_key
    if client_key not in ALLOWED_CLIENT_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return client_key


@app.get("/")
def read_root():
    """Root endpoint showing service status."""
    return {
        "status": "OpenAI Function Call Middleware is running",
        "config": {
            "upstream_services_count": len(app_config.upstream_services),
            "client_keys_count": len(app_config.client_authentication.allowed_keys),
            "models_count": len(MODEL_TO_SERVICE_MAPPING),
            "features": {
                "function_calling": app_config.features.enable_function_calling,
                "log_level": app_config.features.log_level,
                "convert_developer_to_system": app_config.features.convert_developer_to_system,
                "random_trigger": True
            }
        }
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    _api_key: str = Depends(verify_api_key)
):
    """Main chat completion endpoint, proxy and inject function calling capabilities."""
    start_time = time.time()
    
    # Count input tokens
    prompt_tokens = token_counter.count_tokens(body.messages, body.model)
    logger.info(f"📊 Request to {body.model} - Input tokens: {prompt_tokens}")
    
    try:
        logger.debug(f"🔧 Received request, model: {body.model}")
        logger.debug(f"🔧 Number of messages: {len(body.messages)}")
        logger.debug(f"🔧 Number of tools: {len(body.tools) if body.tools else 0}")
        logger.debug(f"🔧 Streaming: {body.stream}")
        
        upstreams, actual_model = find_upstream(
            body.model,
            MODEL_TO_SERVICE_MAPPING,
            ALIAS_MAPPING,
            DEFAULT_SERVICE,
            app_config.features.model_passthrough,
            app_config.upstream_services
        )

        logger.debug(f"🔧 Found {len(upstreams)} upstream service(s) for model {body.model}")
        for i, srv in enumerate(upstreams):
            logger.debug(f"🔧 Service {i + 1}: {srv['name']} (priority: {srv.get('priority', 0)})")
        
        logger.debug(f"🔧 Starting message preprocessing, original message count: {len(body.messages)}")
        processed_messages = preprocess_messages(
            body.messages,
            GLOBAL_TRIGGER_SIGNAL,
            app_config.features.convert_developer_to_system
        )
        logger.debug(f"🔧 Preprocessing completed, processed message count: {len(processed_messages)}")
        
        if not validate_message_structure(processed_messages, app_config.features.convert_developer_to_system):
            logger.error(f"❌ Message structure validation failed, but continuing processing")
        
        request_body_dict = body.model_dump(exclude_unset=True)
        request_body_dict["model"] = actual_model
        request_body_dict["messages"] = processed_messages
        is_fc_enabled = app_config.features.enable_function_calling
        has_tools_in_request = bool(body.tools)
        has_function_call = is_fc_enabled and has_tools_in_request
        
        logger.debug(f"🔧 Request body constructed, message count: {len(processed_messages)}")
        
    except Exception as e:
        logger.error(f"❌ Request preprocessing failed: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        if hasattr(app_config, 'debug') and app_config.debug:
            logger.error(f"❌ Error stack: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "message": "Invalid request format",
                    "type": "invalid_request_error",
                    "code": "invalid_request"
                }
            }
        )

    if has_function_call:
        logger.debug(f"🔧 Using global trigger signal for this request: {GLOBAL_TRIGGER_SIGNAL}")
        
        function_prompt, _ = generate_function_prompt(
            body.tools,
            GLOBAL_TRIGGER_SIGNAL,
            app_config.features.prompt_template
        )
        
        tool_choice_prompt = safe_process_tool_choice(body.tool_choice)
        if tool_choice_prompt:
            function_prompt += tool_choice_prompt

        system_message = {"role": "system", "content": function_prompt}
        request_body_dict["messages"].insert(0, system_message)
        
        if "tools" in request_body_dict:
            del request_body_dict["tools"]
        if "tool_choice" in request_body_dict:
            del request_body_dict["tool_choice"]

    elif has_tools_in_request and not is_fc_enabled:
        logger.info(f"🔧 Function calling is disabled by configuration, ignoring 'tools' and 'tool_choice' in request.")
        if "tools" in request_body_dict:
            del request_body_dict["tools"]
        if "tool_choice" in request_body_dict:
            del request_body_dict["tool_choice"]

    # Try each upstream service by priority until one succeeds
    last_error = None

    if not body.stream:
        # Non-streaming: try each upstream with failover
        for upstream_idx, upstream in enumerate(upstreams):
            upstream_url = f"{upstream['base_url']}/chat/completions"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_api_key}" if app_config.features.key_passthrough else f"Bearer {upstream['api_key']}",
                "Accept": "application/json"
            }

            logger.info(
                f"📝 Attempting upstream {upstream_idx + 1}/{len(upstreams)}: {upstream['name']} (priority: {upstream.get('priority', 0)})")
            logger.info(
                f"📝 Model: {request_body_dict.get('model', 'unknown')}, Messages: {len(request_body_dict.get('messages', []))}")

            try:
                logger.debug(f"🔧 Sending upstream request to: {upstream_url}")
                logger.debug(f"🔧 has_function_call: {has_function_call}")
                logger.debug(f"🔧 Request body contains tools: {bool(body.tools)}")
                
                upstream_response = await http_client.post(
                    upstream_url, json=request_body_dict, headers=headers, timeout=app_config.server.timeout
                )
                upstream_response.raise_for_status()
                
                # 添加响应内容检查，防止空响应或非JSON响应
                response_text = upstream_response.text
                logger.debug(f"🔧 Upstream response status code: {upstream_response.status_code}")
                logger.debug(f"🔧 Upstream response length: {len(response_text)} bytes")

                if not response_text or response_text.strip() == "":
                    logger.error(f"❌ Upstream {upstream['name']} returned empty response body with 200 status")
                    raise ValueError("Empty response from upstream service")

                try:
                    response_json = upstream_response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"❌ Failed to parse JSON from {upstream['name']}")
                    logger.error(f"❌ Response content (first 500 chars): {response_text[:500]}")
                    logger.error(f"❌ Content-Type: {upstream_response.headers.get('content-type', 'unknown')}")
                    raise ValueError(f"Invalid JSON response: {json_err}")
                
                # Count output tokens and handle usage
                completion_text = ""
                if response_json.get("choices") and len(response_json["choices"]) > 0:
                    content = response_json["choices"][0].get("message", {}).get("content")
                    if content:
                        completion_text = content
                
                # Calculate our estimated tokens
                estimated_completion_tokens = token_counter.count_text_tokens(completion_text,
                                                                              body.model) if completion_text else 0
                estimated_prompt_tokens = prompt_tokens
                estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens
                elapsed_time = time.time() - start_time
                
                # Check if upstream provided usage and respect it
                upstream_usage = response_json.get("usage", {})
                if upstream_usage:
                    # Preserve upstream's usage structure and only replace zero values
                    final_usage = upstream_usage.copy()
                    
                    # Replace zero or missing values with our estimates
                    if not final_usage.get("prompt_tokens") or final_usage.get("prompt_tokens") == 0:
                        final_usage["prompt_tokens"] = estimated_prompt_tokens
                        logger.debug(f"🔧 Replaced zero/missing prompt_tokens with estimate: {estimated_prompt_tokens}")
                    
                    if not final_usage.get("completion_tokens") or final_usage.get("completion_tokens") == 0:
                        final_usage["completion_tokens"] = estimated_completion_tokens
                        logger.debug(
                            f"🔧 Replaced zero/missing completion_tokens with estimate: {estimated_completion_tokens}")
                    
                    if not final_usage.get("total_tokens") or final_usage.get("total_tokens") == 0:
                        final_usage["total_tokens"] = final_usage.get("prompt_tokens",
                                                                      estimated_prompt_tokens) + final_usage.get(
                            "completion_tokens", estimated_completion_tokens)
                        logger.debug(
                            f"🔧 Replaced zero/missing total_tokens with calculated value: {final_usage['total_tokens']}")
                    
                    response_json["usage"] = final_usage
                    logger.debug(f"🔧 Preserved upstream usage with replacements: {final_usage}")
                else:
                    # No upstream usage, provide our estimates
                    response_json["usage"] = {
                        "prompt_tokens": estimated_prompt_tokens,
                        "completion_tokens": estimated_completion_tokens,
                        "total_tokens": estimated_total_tokens
                    }
                    logger.debug(f"🔧 No upstream usage found, using estimates")
                
                # Log token statistics
                actual_usage = response_json["usage"]
                logger.info("=" * 60)
                logger.info(f"📊 Token Usage Statistics - Model: {body.model}")
                logger.info(f"   Input Tokens: {actual_usage.get('prompt_tokens', 0)}")
                logger.info(f"   Output Tokens: {actual_usage.get('completion_tokens', 0)}")
                logger.info(f"   Total Tokens: {actual_usage.get('total_tokens', 0)}")
                logger.info(f"   Duration: {elapsed_time:.2f}s")
                logger.info("=" * 60)
                
                if has_function_call:
                    content = response_json["choices"][0]["message"]["content"]
                    logger.debug(f"🔧 Complete response content: {repr(content)}")
                    
                    parsed_tools = parse_function_calls_xml(content, GLOBAL_TRIGGER_SIGNAL)
                    logger.debug(f"🔧 XML parsing result: {parsed_tools}")
                    
                    if parsed_tools:
                        logger.debug(f"🔧 Successfully parsed {len(parsed_tools)} tool calls")
                        tool_calls = []
                        for tool in parsed_tools:
                            tool_call_id = f"call_{uuid.uuid4().hex}"
                            store_tool_call_mapping(
                                tool_call_id,
                                tool["name"],
                                tool["args"],
                                f"Calling tool {tool['name']}"
                            )
                            tool_calls.append({
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool["name"],
                                    "arguments": json.dumps(tool["args"])
                                }
                            })
                        logger.debug(f"🔧 Converted tool_calls: {tool_calls}")
                        
                        response_json["choices"][0]["message"] = {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": tool_calls,
                        }
                        response_json["choices"][0]["finish_reason"] = "tool_calls"
                        logger.debug(f"🔧 Function call conversion completed")
                    else:
                        logger.debug(f"🔧 No tool calls detected, returning original content (including think blocks)")
                else:
                    logger.debug(f"🔧 No function calls detected or conversion conditions not met")
                
                return JSONResponse(content=response_json)

            except httpx.HTTPStatusError as e:
                logger.warning(f"⚠️  Upstream {upstream['name']} failed: status_code={e.response.status_code}")
                logger.debug(f"🔧 Error details: {e.response.text}")

                last_error = e

                # Check if we should retry with next upstream
                # Don't retry for client errors (400, 401, 403) - these won't succeed with different upstream
                if e.response.status_code in [400, 401, 403]:
                    logger.error(f"❌ Client error from {upstream['name']}, not retrying other upstreams")
                    if e.response.status_code == 400:
                        error_response = {
                            "error": {"message": "Invalid request parameters", "type": "invalid_request_error",
                                      "code": "bad_request"}}
                    elif e.response.status_code == 401:
                        error_response = {"error": {"message": "Authentication failed", "type": "authentication_error",
                                                    "code": "unauthorized"}}
                    elif e.response.status_code == 403:
                        error_response = {
                            "error": {"message": "Access forbidden", "type": "permission_error", "code": "forbidden"}}
                    return JSONResponse(content=error_response, status_code=e.response.status_code)

                # For 429 and 5xx errors, try next upstream if available
                if upstream_idx < len(upstreams) - 1:
                    logger.info(f"🔄 Trying next upstream service (failover)...")
                    continue
                else:
                    # All upstreams failed
                    logger.error(f"❌ All {len(upstreams)} upstream services failed")
                    if e.response.status_code == 429:
                        error_response = {
                            "error": {"message": "Rate limit exceeded on all upstreams", "type": "rate_limit_error",
                                      "code": "rate_limit_exceeded"}}
                    elif e.response.status_code >= 500:
                        error_response = {"error": {"message": "All upstream services temporarily unavailable",
                                                    "type": "service_error", "code": "upstream_error"}}
                    else:
                        error_response = {
                            "error": {"message": "Request processing failed on all upstreams", "type": "api_error",
                                      "code": "unknown_error"}}
                    return JSONResponse(content=error_response, status_code=e.response.status_code)
            
            except ValueError as e:
                # 捕获空响应或JSON解析错误
                logger.error(f"❌ Invalid response from {upstream['name']}: {e}")
                last_error = e
                if upstream_idx < len(upstreams) - 1:
                    logger.info(f"🔄 Trying next upstream service...")
                    continue
                else:
                    logger.error(f"❌ All upstreams failed - invalid responses")
                    return JSONResponse(
                        status_code=502,
                        content={"error": {"message": "All upstream services returned invalid responses",
                                           "type": "bad_gateway", "code": "invalid_upstream_response"}}
                    )

            except Exception as e:
                logger.error(f"❌ Unexpected error with {upstream['name']}: {type(e).__name__}: {e}")
                logger.error(f"❌ Error traceback: {traceback.format_exc()}")
                last_error = e
                if upstream_idx < len(upstreams) - 1:
                    logger.info(f"🔄 Trying next upstream service...")
                    continue
                else:
                    logger.error(f"❌ All upstreams failed with errors")
                    return JSONResponse(
                        status_code=500,
                        content={"error": {"message": "All upstream services failed", "type": "service_error",
                                           "code": "all_upstreams_failed"}}
                    )

    else:
        # Streaming: use the highest priority upstream (first in list)
        upstream = upstreams[0]
        upstream_url = f"{upstream['base_url']}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key}" if app_config.features.key_passthrough else f"Bearer {upstream['api_key']}",
            "Accept": "text/event-stream"
        }

        logger.info(f"📝 Streaming to upstream: {upstream['name']} (priority: {upstream.get('priority', 0)})")

        async def stream_with_token_count():
            completion_tokens = 0
            completion_text = ""
            done_received = False
            upstream_usage_chunk = None
            
            async for chunk in stream_proxy_with_fc_transform(
                upstream_url,
                request_body_dict,
                headers,
                body.model,
                has_function_call,
                GLOBAL_TRIGGER_SIGNAL,
                http_client,
                app_config.server.timeout
            ):
                # Check if this is the [DONE] marker
                if chunk.startswith(b"data: "):
                    try:
                        line_data = chunk[6:].decode('utf-8').strip()
                        if line_data == "[DONE]":
                            done_received = True
                            # Don't yield the [DONE] marker yet, we'll send it after usage info
                            break
                        elif line_data:
                            chunk_json = json.loads(line_data)
                            
                            # Check if this chunk contains usage information
                            if "usage" in chunk_json:
                                upstream_usage_chunk = chunk_json
                                logger.debug(f"🔧 Detected upstream usage chunk: {chunk_json['usage']}")
                                # Don't yield upstream usage chunk yet, we'll process it
                                continue
                            
                            # Process regular content chunks
                            if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                                delta = chunk_json["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    completion_text += content
                    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                        logger.debug(f"Failed to parse chunk for token counting: {e}")
                        pass
                
                yield chunk
            
            # Calculate our estimated tokens
            estimated_completion_tokens = token_counter.count_text_tokens(completion_text,
                                                                          body.model) if completion_text else 0
            estimated_prompt_tokens = prompt_tokens
            estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens
            elapsed_time = time.time() - start_time
            
            # Determine final usage
            final_usage = None
            if upstream_usage_chunk and "usage" in upstream_usage_chunk:
                # Respect upstream usage, but replace zero values
                upstream_usage = upstream_usage_chunk["usage"]
                final_usage = upstream_usage.copy()
                
                if not final_usage.get("prompt_tokens") or final_usage.get("prompt_tokens") == 0:
                    final_usage["prompt_tokens"] = estimated_prompt_tokens
                    logger.debug(f"🔧 Replaced zero/missing prompt_tokens with estimate: {estimated_prompt_tokens}")
                
                if not final_usage.get("completion_tokens") or final_usage.get("completion_tokens") == 0:
                    final_usage["completion_tokens"] = estimated_completion_tokens
                    logger.debug(
                        f"🔧 Replaced zero/missing completion_tokens with estimate: {estimated_completion_tokens}")
                
                if not final_usage.get("total_tokens") or final_usage.get("total_tokens") == 0:
                    final_usage["total_tokens"] = final_usage.get("prompt_tokens",
                                                                  estimated_prompt_tokens) + final_usage.get(
                        "completion_tokens", estimated_completion_tokens)
                    logger.debug(
                        f"🔧 Replaced zero/missing total_tokens with calculated value: {final_usage['total_tokens']}")
                
                logger.debug(f"🔧 Using upstream usage with replacements: {final_usage}")
            else:
                # No upstream usage, use our estimates
                final_usage = {
                    "prompt_tokens": estimated_prompt_tokens,
                    "completion_tokens": estimated_completion_tokens,
                    "total_tokens": estimated_total_tokens
                }
                logger.debug(f"🔧 No upstream usage found, using estimates")
            
            # Log token statistics
            logger.info("=" * 60)
            logger.info(f"📊 Token Usage Statistics - Model: {body.model}")
            logger.info(f"   Input Tokens: {final_usage['prompt_tokens']}")
            logger.info(f"   Output Tokens: {final_usage['completion_tokens']}")
            logger.info(f"   Total Tokens: {final_usage['total_tokens']}")
            logger.info(f"   Duration: {elapsed_time:.2f}s")
            logger.info("=" * 60)
            
            # Send usage information if requested via stream_options OR if upstream provided usage
            if (body.stream_options and body.stream_options.get("include_usage", False)) or upstream_usage_chunk:
                usage_chunk_to_send = {
                    "id": f"chatcmpl-{uuid.uuid4().hex}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": body.model,
                    "choices": [],
                    "usage": final_usage
                }
                
                # If upstream provided additional fields in the usage chunk, preserve them
                if upstream_usage_chunk:
                    for key in upstream_usage_chunk:
                        if key not in ["usage", "choices"] and key not in usage_chunk_to_send:
                            usage_chunk_to_send[key] = upstream_usage_chunk[key]
                
                yield f"data: {json.dumps(usage_chunk_to_send)}\n\n".encode('utf-8')
                logger.debug(f"🔧 Sent usage chunk in stream: {usage_chunk_to_send['usage']}")
            
            # Send [DONE] marker if it was received
            if done_received:
                yield b"data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_with_token_count(),
            media_type="text/event-stream"
        )


@app.post("/v1/messages")
async def anthropic_messages(
        request: Request,
        body: AnthropicMessage,
        _api_key: str = Depends(verify_api_key)
):
    """Anthropic Messages API endpoint - converts to OpenAI format and back."""
    start_time = time.time()
    
    logger.info(f"📨 Anthropic API request to model: {body.model}")
    logger.info(f"📊 Max tokens: {body.max_tokens}, Stream: {body.stream}")
    
    try:
        # Convert Anthropic request to OpenAI format
        anthropic_dict = body.model_dump()
        openai_request = anthropic_to_openai_request(anthropic_dict)
        
        logger.debug(f"🔄 Converted Anthropic request to OpenAI format")
        logger.debug(f"🔧 OpenAI messages: {len(openai_request['messages'])}")
        
        # Apply Toolify's function calling logic if tools are present
        has_tools = "tools" in openai_request and openai_request["tools"]
        is_fc_enabled = app_config.features.enable_function_calling
        has_function_call = is_fc_enabled and has_tools
        
        if has_function_call:
            logger.info(f"🔧 Applying Toolify function calling injection for {len(openai_request['tools'])} tools")
            
            # Convert OpenAI tools format to Toolify Tool objects
            from pydantic import ValidationError
            tool_objects = []
            for tool_dict in openai_request["tools"]:
                try:
                    # Create Tool object from the converted format
                    tool_obj = Tool(
                        type="function",
                        function=ToolFunction(
                            name=tool_dict["function"]["name"],
                            description=tool_dict["function"].get("description", ""),
                            parameters=tool_dict["function"].get("parameters", {})
                        )
                    )
                    tool_objects.append(tool_obj)
                except (ValidationError, KeyError) as e:
                    logger.warning(f"⚠️  Failed to parse tool: {e}")
            
            if tool_objects:
                # Generate function calling prompt
                function_prompt, _ = generate_function_prompt(
                    tool_objects,
                    GLOBAL_TRIGGER_SIGNAL,
                    app_config.features.prompt_template
                )
                
                # Inject into system message
                system_message = {"role": "system", "content": function_prompt}
                openai_request["messages"].insert(0, system_message)
                
                logger.debug(f"🔧 Injected function calling prompt with trigger signal")
            
            # Remove tools parameter (we're using prompt injection instead)
            del openai_request["tools"]
        
        elif has_tools and not is_fc_enabled:
            logger.info(f"🔧 Function calling is disabled, removing tools from request")
            del openai_request["tools"]
        
        # Find upstream service
        upstreams, actual_model = find_upstream(
            body.model,
            MODEL_TO_SERVICE_MAPPING,
            ALIAS_MAPPING,
            DEFAULT_SERVICE,
            app_config.features.model_passthrough,
            app_config.upstream_services
        )
        upstream = upstreams[0]  # Use highest priority upstream
        
        logger.info(f"🎯 Using upstream: {upstream['name']} (priority: {upstream.get('priority', 0)})")
        
        # Update model to actual upstream model
        openai_request["model"] = actual_model
        
        # Prepare request headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key}" if app_config.features.key_passthrough else f"Bearer {upstream['api_key']}",
        }
        
        upstream_url = f"{upstream['base_url']}/chat/completions"
        
        if body.stream:
            # Streaming response
            logger.info(f"📡 Starting Anthropic streaming response")
            headers["Accept"] = "text/event-stream"
            
            async def anthropic_stream_generator():
                try:
                    # If function calling is enabled, use the special streaming handler
                    if has_function_call:
                        logger.debug(f"🔧 Using function calling streaming handler")
                        # Stream through Toolify's FC processor, then convert to Anthropic format
                        openai_stream = stream_proxy_with_fc_transform(
                            upstream_url, 
                            openai_request, 
                            headers, 
                            openai_request["model"], 
                            True,  # has_fc=True
                            GLOBAL_TRIGGER_SIGNAL,
                            http_client,
                            app_config.server.timeout
                        )
                        # Convert to Anthropic format
                        async for anthropic_chunk in stream_openai_to_anthropic(openai_stream):
                            yield anthropic_chunk.encode('utf-8') if isinstance(anthropic_chunk, str) else anthropic_chunk
                    else:
                        # No function calling, direct streaming
                        async with http_client.stream("POST", upstream_url, json=openai_request, headers=headers, timeout=app_config.server.timeout) as response:
                            if response.status_code != 200:
                                error_content = await response.aread()
                                logger.error(f"❌ Upstream error: {response.status_code} - {error_content.decode('utf-8', errors='ignore')}")
                                yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': 'Upstream service error'}})}\n\n"
                                return
                            
                            async for converted_chunk in stream_openai_to_anthropic(response.aiter_bytes()):
                                yield converted_chunk.encode('utf-8') if isinstance(converted_chunk, str) else converted_chunk
                            
                except Exception as e:
                    logger.error(f"❌ Streaming error: {e}")
                    logger.error(traceback.format_exc())
                    yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': str(e)}})}\n\n"
            
            return StreamingResponse(
                anthropic_stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming response
            logger.debug(f"🔧 Sending non-streaming request to upstream")
            headers["Accept"] = "application/json"
            
            upstream_response = await http_client.post(
                upstream_url,
                json=openai_request,
                headers=headers,
                timeout=app_config.server.timeout
            )
            upstream_response.raise_for_status()
            
            openai_resp = upstream_response.json()
            logger.debug(f"✅ Received response from upstream")
            
            # If function calling was enabled, check for tool calls in response
            if has_function_call:
                choice = openai_resp.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                # Check if response contains function call XML
                if content and GLOBAL_TRIGGER_SIGNAL in content:
                    logger.debug(f"🔧 Detected function call trigger signal in response")
                    parsed_tools = parse_function_calls_xml(content, GLOBAL_TRIGGER_SIGNAL)
                    
                    if parsed_tools:
                        logger.info(f"🔧 Successfully parsed {len(parsed_tools)} function call(s)")
                        
                        # Convert to OpenAI tool_calls format
                        tool_calls = []
                        for tool in parsed_tools:
                            tool_call_id = f"call_{uuid.uuid4().hex}"
                            # Store mapping for potential future lookups
                            store_tool_call_mapping(
                                tool_call_id,
                                tool["name"],
                                tool["args"],
                                f"Calling tool {tool['name']}"
                            )
                            tool_calls.append({
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool["name"],
                                    "arguments": json.dumps(tool["args"])
                                }
                            })
                        
                        # Update OpenAI response with tool_calls
                        openai_resp["choices"][0]["message"] = {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": tool_calls
                        }
                        openai_resp["choices"][0]["finish_reason"] = "tool_calls"
                        logger.debug(f"🔧 Converted XML function calls to OpenAI tool_calls format")
            
            # Convert OpenAI response to Anthropic format
            anthropic_resp = openai_to_anthropic_response(openai_resp)
            
            elapsed_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"📊 Anthropic API Response - Model: {body.model}")
            logger.info(f"   Input Tokens: {anthropic_resp['usage']['input_tokens']}")
            logger.info(f"   Output Tokens: {anthropic_resp['usage']['output_tokens']}")
            logger.info(f"   Duration: {elapsed_time:.2f}s")
            logger.info("=" * 60)
            
            return JSONResponse(content=anthropic_resp)
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Upstream HTTP error: {e.response.status_code}")
        error_detail = e.response.text
        return JSONResponse(
            status_code=e.response.status_code,
            content={
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": f"Upstream service error: {error_detail}"
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Error processing Anthropic request: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": str(e)
                }
            }
        )


@app.get("/v1/models")
async def list_models(_api_key: str = Depends(verify_api_key)):
    """List all available models."""
    visible_models = set()
    for model_name in MODEL_TO_SERVICE_MAPPING.keys():
        if ':' in model_name:
            parts = model_name.split(':', 1)
            if len(parts) == 2:
                alias, _ = parts
                visible_models.add(alias)
            else:
                visible_models.add(model_name)
        else:
            visible_models.add(model_name)

    models = []
    for model_id in sorted(visible_models):
        models.append({
            "id": model_id,
            "object": "model",
            "created": 1677610602,
            "owned_by": "openai",
            "permission": [],
            "root": model_id,
            "parent": None
        })
    
    return {
        "object": "list",
        "data": models
    }


# Admin API endpoints
@app.post("/api/admin/login", response_model=LoginResponse)
async def admin_login(login_data: LoginRequest, admin_config=Depends(get_admin_credentials)):
    """Admin login endpoint."""
    if login_data.username != admin_config.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not verify_password(login_data.password, admin_config.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = create_access_token(admin_config.username, admin_config.jwt_secret)
    return LoginResponse(access_token=access_token)


@app.get("/api/admin/config")
async def get_config(_username: str = Depends(verify_admin_token)):
    """Get current configuration."""
    try:
        with open(config_loader.config_path, 'r', encoding='utf-8') as f:
            config_content = yaml.safe_load(f)

        # Remove sensitive information from response
        if 'admin_authentication' in config_content:
            config_content['admin_authentication'] = {
                'username': config_content['admin_authentication'].get('username', ''),
                'password': '********',
                'jwt_secret': '********'
            }

        return {"success": True, "config": config_content}
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read configuration: {str(e)}")


@app.put("/api/admin/config")
async def update_config(config_data: dict, _username: str = Depends(verify_admin_token)):
    """Update configuration."""
    try:
        # Read current config to preserve admin_authentication
        current_config = None
        try:
            with open(config_loader.config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f)
        except Exception:
            pass

        # If admin_authentication exists in current config and not provided in update, preserve it
        if current_config and 'admin_authentication' in current_config:
            if 'admin_authentication' not in config_data or config_data['admin_authentication'].get(
                    'password') == '********':
                config_data['admin_authentication'] = current_config['admin_authentication']

        # Validate the configuration using Pydantic
        from config_loader import AppConfig
        validated_config = AppConfig(**config_data)

        # Write the validated configuration back to file
        with open(config_loader.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Reload runtime configuration so changes take effect immediately
        load_runtime_config(reload=True)
        logger.info(f"Configuration updated and reloaded successfully by admin: {_username}")
        return {
            "success": True,
            "message": "Configuration updated successfully and applied immediately."
        }

    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Configuration validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


# Mount static files for admin interface (if exists)
try:
    if os.path.exists("frontend/dist"):
        app.mount("/admin", StaticFiles(directory="frontend/dist", html=True), name="admin")
        logger.info("📁 Admin interface mounted at /admin")
except Exception as e:
    logger.warning(f"⚠️  Failed to mount admin interface: {e}")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting server on {app_config.server.host}:{app_config.server.port}")
    logger.info(f"⏱️  Request timeout: {app_config.server.timeout} seconds")
    
    uvicorn.run(
        app,
        host=app_config.server.host,
        port=app_config.server.port,
        log_level=app_config.features.log_level.lower() if app_config.features.log_level != "DISABLED" else "critical"
    )

