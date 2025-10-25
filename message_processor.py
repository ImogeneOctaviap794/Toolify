# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Message processing utilities.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from tool_mapping import get_tool_call_mapping

logger = logging.getLogger(__name__)


def format_tool_result_for_ai(tool_call_id: str, result_content: str) -> str:
    """Format tool call results for AI understanding with English prompts and XML structure."""
    logger.debug(f"🔧 Formatting tool call result: tool_call_id={tool_call_id}")
    tool_info = get_tool_call_mapping(tool_call_id)
    if not tool_info:
        logger.debug(f"🔧 Tool call mapping not found, using default format")
        return f"Tool execution result:\n<tool_result>\n{result_content}\n</tool_result>"
    
    formatted_text = f"""Tool execution result:
- Tool name: {tool_info['name']}
- Execution result:
<tool_result>
{result_content}
</tool_result>"""
    
    logger.debug(f"🔧 Formatting completed, tool name: {tool_info['name']}")
    return formatted_text


def format_assistant_tool_calls_for_ai(tool_calls: List[Dict[str, Any]], trigger_signal: str) -> str:
    """Format assistant tool calls into AI-readable string format."""
    logger.debug(f"🔧 Formatting assistant tool calls. Count: {len(tool_calls)}")
    
    xml_calls_parts = []
    for tool_call in tool_calls:
        function_info = tool_call.get("function", {})
        name = function_info.get("name", "")
        arguments_json = function_info.get("arguments", "{}")
        
        try:
            # First, try to load as JSON. If it's a string that's a valid JSON, we parse it.
            args_dict = json.loads(arguments_json)
        except (json.JSONDecodeError, TypeError):
            # If it's not a valid JSON string, treat it as a simple string.
            args_dict = {"raw_arguments": arguments_json}

        args_parts = []
        for key, value in args_dict.items():
            # Dump the value back to a JSON string for consistent representation inside XML.
            json_value = json.dumps(value, ensure_ascii=False)
            args_parts.append(f"<{key}>{json_value}</{key}>")
        
        args_content = "\n".join(args_parts)
        
        xml_call = f"<function_call>\n<tool>{name}</tool>\n<args>\n{args_content}\n</args>\n</function_call>"
        xml_calls_parts.append(xml_call)

    all_calls = "\n".join(xml_calls_parts)
    final_str = f"{trigger_signal}\n<function_calls>\n{all_calls}\n</function_calls>"
    
    logger.debug("🔧 Assistant tool calls formatted successfully.")
    return final_str


def preprocess_messages(messages: List[Dict[str, Any]], trigger_signal: str, convert_developer: bool = True) -> List[Dict[str, Any]]:
    """Preprocess messages, convert tool-type messages to AI-understandable format, return dictionary list to avoid Pydantic validation issues."""
    processed_messages = []
    
    for message in messages:
        if isinstance(message, dict):
            if message.get("role") == "tool":
                tool_call_id = message.get("tool_call_id")
                content = message.get("content")
                
                if tool_call_id and content:
                    formatted_content = format_tool_result_for_ai(tool_call_id, content)
                    processed_message = {
                        "role": "user",
                        "content": formatted_content
                    }
                    processed_messages.append(processed_message)
                    logger.debug(f"🔧 Converted tool message to user message: tool_call_id={tool_call_id}")
                else:
                    logger.debug(
                        f"🔧 Skipped invalid tool message: tool_call_id={tool_call_id}, content={bool(content)}")
            elif message.get("role") == "assistant" and "tool_calls" in message and message["tool_calls"]:
                tool_calls = message.get("tool_calls", [])
                formatted_tool_calls_str = format_assistant_tool_calls_for_ai(tool_calls, trigger_signal)
                
                # Combine with original content if it exists
                original_content = message.get("content") or ""
                final_content = f"{original_content}\n{formatted_tool_calls_str}".strip()

                processed_message = {
                    "role": "assistant",
                    "content": final_content
                }
                # Copy other potential keys from the original message, except tool_calls
                for key, value in message.items():
                    if key not in ["role", "content", "tool_calls"]:
                        processed_message[key] = value

                processed_messages.append(processed_message)
                logger.debug(f"🔧 Converted assistant tool_calls to content.")

            elif message.get("role") == "developer":
                if convert_developer:
                    processed_message = message.copy()
                    processed_message["role"] = "system"
                    processed_messages.append(processed_message)
                    logger.debug(f"🔧 Converted developer message to system message for better upstream compatibility")
                else:
                    processed_messages.append(message)
                    logger.debug(f"🔧 Keeping developer role unchanged (based on configuration)")
            else:
                processed_messages.append(message)
        else:
            processed_messages.append(message)
    
    return processed_messages


def validate_message_structure(messages: List[Dict[str, Any]], convert_developer: bool = True) -> bool:
    """Validate if message structure meets requirements."""
    try:
        valid_roles = ["system", "user", "assistant", "tool"]
        if not convert_developer:
            valid_roles.append("developer")
        
        for i, msg in enumerate(messages):
            if "role" not in msg:
                logger.error(f"❌ Message {i} missing role field")
                return False
            
            if msg["role"] not in valid_roles:
                logger.error(f"❌ Invalid role value for message {i}: {msg['role']}")
                return False
            
            if msg["role"] == "tool":
                if "tool_call_id" not in msg:
                    logger.error(f"❌ Tool message {i} missing tool_call_id field")
                    return False
            
            content = msg.get("content")
            content_info = ""
            if content:
                if isinstance(content, str):
                    content_info = f", content=text({len(content)} chars)"
                elif isinstance(content, list):
                    text_parts = [item for item in content if isinstance(item, dict) and item.get('type') == 'text']
                    image_parts = [item for item in content if
                                   isinstance(item, dict) and item.get('type') == 'image_url']
                    content_info = f", content=multimodal(text={len(text_parts)}, images={len(image_parts)})"
                else:
                    content_info = f", content={type(content).__name__}"
            else:
                content_info = ", content=empty"
            
            logger.debug(f"✅ Message {i} validation passed: role={msg['role']}{content_info}")
        
        logger.debug(f"✅ All messages validated successfully, total {len(messages)} messages")
        return True
    except Exception as e:
        logger.error(f"❌ Message validation exception: {e}")
        return False


def safe_process_tool_choice(tool_choice) -> str:
    """Safely process tool_choice field to avoid type errors."""
    try:
        if tool_choice is None:
            return ""
        
        if isinstance(tool_choice, str):
            if tool_choice == "none":
                return "\n\n**IMPORTANT:** You are prohibited from using any tools in this round. Please respond like a normal chat assistant and answer the user's question directly."
            else:
                logger.debug(f"🔧 Unknown tool_choice string value: {tool_choice}")
                return ""
        
        elif hasattr(tool_choice, 'function') and hasattr(tool_choice.function, 'name'):
            required_tool_name = tool_choice.function.name
            return f"\n\n**IMPORTANT:** In this round, you must use ONLY the tool named `{required_tool_name}`. Generate the necessary parameters and output in the specified XML format."
        
        else:
            logger.debug(f"🔧 Unsupported tool_choice type: {type(tool_choice)}")
            return ""
    
    except Exception as e:
        logger.error(f"❌ Error processing tool_choice: {e}")
        return ""

