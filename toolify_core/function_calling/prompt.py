# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Prompt generation for function calling.
"""

import json
import secrets
import string
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def generate_random_trigger_signal() -> str:
    """Generate a random, self-closing trigger signal like <Function_AB1c_Start/>."""
    chars = string.ascii_letters + string.digits
    random_str = ''.join(secrets.choice(chars) for _ in range(4))
    return f"<Function_{random_str}_Start/>"


def get_function_call_prompt_template(trigger_signal: str, custom_template: str = None) -> str:
    """
    Generate prompt template based on dynamic trigger signal.
    """
    if custom_template:
        logger.info("🔧 Using custom prompt template from configuration")
        return custom_template.format(
            trigger_signal=trigger_signal,
            tools_list="{tools_list}"
        )
    
    return f"""
You have access to the following powerful tools to help solve problems efficiently:

{{tools_list}}

**🎯 CRITICAL TOOL USAGE RULES:**

⚡ **MANDATORY TOOL USAGE** - You MUST use tools when the task requires action. DO NOT output code, file contents, or results directly to the user when you can use a tool instead.

⚡ **PROHIBITED BEHAVIORS:**
❌ NEVER output full code blocks when you should use Write/Edit tools
❌ NEVER describe file contents when you should use Read tool
❌ NEVER list what you "would do" - DO IT with tools immediately
❌ NEVER say "here's the code" and paste it - USE THE WRITE TOOL

⚡ **REQUIRED BEHAVIORS:**
✅ ALWAYS use Write tool to create files (never output code for user to copy)
✅ ALWAYS use Edit tool to modify files (never show diffs)
✅ ALWAYS use Read tool to check files (never guess)
✅ ALWAYS use Bash tool to execute commands (never just suggest)
✅ ALWAYS use search tools to find information (never speculate)

**💡 TOOL USAGE IS MANDATORY FOR:**
✅ Creating any file (HTML, CSS, JS, Python, etc.) - USE WRITE TOOL
✅ Modifying existing files - USE EDIT TOOL
✅ Searching for code or text - USE GREP/SEARCH TOOLS
✅ Finding files - USE GLOB/FILE SEARCH TOOLS
✅ Executing commands - USE BASH TOOL
✅ Fetching web content - USE FETCH TOOL
✅ Reading files - USE READ TOOL

**❌ EXAMPLES OF WHAT NOT TO DO:**
❌ User: "Create a weather.html file"
   BAD Response: "Here's the HTML code: <!DOCTYPE html>..."
   
✅ User: "Create a weather.html file"  
   GOOD Response: [Immediately uses Write tool to create the file]

❌ User: "Find TODO comments"
   BAD Response: "You can find them with: grep TODO..."
   
✅ User: "Find TODO comments"
   GOOD Response: [Immediately uses Grep tool to search]

**🚀 REMEMBER - THIS IS NOT OPTIONAL:**
- You have real tools that can DO things
- Users expect you to USE these tools, not describe them
- Outputting code/results directly is LAZY and WRONG
- Using tools shows competence and gets real work done
- When a task needs action → USE TOOLS IMMEDIATELY

**IMPORTANT CONTEXT NOTES:**
1. You can call MULTIPLE tools in a single response if needed - don't hold back!
2. The conversation context may already contain tool execution results from previous function calls. Review the conversation history carefully to avoid unnecessary duplicate tool calls.
3. When tool execution results are present in the context, they will be formatted with XML tags like <tool_result>...</tool_result> for easy identification.
4. This is the ONLY format you can use for tool calls, and any deviation will result in failure.

**📋 TOOL CALL FORMAT:**
When you need to use tools, you **MUST** strictly follow this format. Do NOT include any extra text, explanations, or dialogue on the first and second lines of the tool call syntax:

1. When starting tool calls, begin on a new line with exactly:
{trigger_signal}
No leading or trailing spaces, output exactly as shown above. The trigger signal MUST be on its own line and appear only once.

2. Starting from the second line, **immediately** follow with the complete <function_calls> XML block.

3. For multiple tool calls, include multiple <function_call> blocks within the same <function_calls> wrapper.

4. Do not add any text or explanation after the closing </function_calls> tag.

STRICT ARGUMENT KEY RULES:
- You MUST use parameter keys EXACTLY as defined (case- and punctuation-sensitive). Do NOT rename, add, or remove characters.
- If a key starts with a hyphen (e.g., -i, -C), you MUST keep the hyphen in the tag name. Example: <-i>true</-i>, <-C>2</-C>.
- Never convert "-i" to "i" or "-C" to "C". Do not pluralize, translate, or alias parameter keys.
- The <tool> tag must contain the exact name of a tool from the list. Any other tool name is invalid.
- The <args> must contain all required arguments for that tool.

**🌟 TOOL USAGE EXAMPLES:**

Example 1 - User asks: "What files are in the src directory?"
❌ BAD: "The src directory likely contains source code files..."
✅ GOOD: Use the file listing tool immediately to get real results!

Example 2 - User asks: "Find all TODO comments in the code"
❌ BAD: "You can search for TODO comments using grep..."
✅ GOOD: Use the search tool NOW to find them!

Example 3 - User asks: "Is there a config.yaml file?"
❌ BAD: "There might be a config.yaml file..."
✅ GOOD: Use the file search tool to check!

**📐 CORRECT FORMAT Example (multiple tool calls, including hyphenated keys):**
...response content (optional)...
{trigger_signal}
<function_calls>
    <function_call>
        <tool>Grep</tool>
        <args>
            <-i>true</-i>
            <-C>2</-C>
            <path>.</path>
        </args>
    </function_call>
    <function_call>
        <tool>search</tool>
        <args>
            <keywords>["Python Document", "how to use python"]</keywords>
        </args>
    </function_call>
  </function_calls>

**❌ INCORRECT Example (extra text + wrong key names — DO NOT DO THIS):**
...response content (optional)...
{trigger_signal}
I will call the tools for you.
<function_calls>
    <function_call>
        <tool>Grep</tool>
        <args>
            <i>true</i>
            <C>2</C>
            <path>.</path>
        </args>
    </function_call>
</function_calls>

**🚀 REMEMBER:**
- Tools are fast, accurate, and reliable
- Using tools shows competence and initiative
- Users WANT you to use tools to get real results
- When in doubt, use tools!

Now please be ready to strictly follow the above specifications and USE TOOLS PROACTIVELY!
"""


def generate_function_prompt(tools: List[Any], trigger_signal: str, custom_template: str = None) -> Tuple[str, str]:
    """
    Generate injected system prompt based on tools definition in client request.
    
    Args:
        tools: List of tool definitions
        trigger_signal: Unique trigger signal for function calling
        custom_template: Custom prompt template (optional)
    
    Returns: (prompt_content, trigger_signal)
    """
    tools_list_str = []
    for i, tool in enumerate(tools):
        func = tool.function
        name = func.name
        description = func.description or ""

        # Robustly read JSON Schema fields
        schema: Dict[str, Any] = func.parameters or {}
        props: Dict[str, Any] = schema.get("properties", {}) or {}
        required_list: List[str] = schema.get("required", []) or []

        # Brief summary line: name (type)
        params_summary = ", ".join([
            f"{p_name} ({(p_info or {}).get('type', 'any')})" for p_name, p_info in props.items()
        ]) or "None"

        # Build detailed parameter spec for prompt injection
        detail_lines: List[str] = []
        for p_name, p_info in props.items():
            p_info = p_info or {}
            p_type = p_info.get("type", "any")
            is_required = "Yes" if p_name in required_list else "No"
            p_desc = p_info.get("description")
            enum_vals = p_info.get("enum")
            default_val = p_info.get("default")
            examples_val = p_info.get("examples") or p_info.get("example")

            # Common constraints and hints
            constraints: Dict[str, Any] = {}
            for key in [
                "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                "minLength", "maxLength", "pattern", "format",
                "minItems", "maxItems", "uniqueItems"
            ]:
                if key in p_info:
                    constraints[key] = p_info.get(key)

            # Array item type hint
            if p_type == "array":
                items = p_info.get("items") or {}
                if isinstance(items, dict):
                    itype = items.get("type")
                    if itype:
                        constraints["items.type"] = itype

            # Compose pretty lines
            detail_lines.append(f"- {p_name}:")
            detail_lines.append(f"  - type: {p_type}")
            detail_lines.append(f"  - required: {is_required}")
            if p_desc:
                detail_lines.append(f"  - description: {p_desc}")
            if enum_vals is not None:
                try:
                    detail_lines.append(f"  - enum: {json.dumps(enum_vals, ensure_ascii=False)}")
                except Exception:
                    detail_lines.append(f"  - enum: {enum_vals}")
            if default_val is not None:
                try:
                    detail_lines.append(f"  - default: {json.dumps(default_val, ensure_ascii=False)}")
                except Exception:
                    detail_lines.append(f"  - default: {default_val}")
            if examples_val is not None:
                try:
                    detail_lines.append(f"  - examples: {json.dumps(examples_val, ensure_ascii=False)}")
                except Exception:
                    detail_lines.append(f"  - examples: {examples_val}")
            if constraints:
                try:
                    detail_lines.append(f"  - constraints: {json.dumps(constraints, ensure_ascii=False)}")
                except Exception:
                    detail_lines.append(f"  - constraints: {constraints}")

        detail_block = "\n".join(detail_lines) if detail_lines else "(no parameter details)"
        desc_block = f"```\n{description}\n```" if description else "None"

        tools_list_str.append(
            f"{i + 1}. <tool name=\"{name}\">\n"
            f"   Description:\n{desc_block}\n"
            f"   Parameters summary: {params_summary}\n"
            f"   Required parameters: {', '.join(required_list) if required_list else 'None'}\n"
            f"   Parameter details:\n{detail_block}"
        )
    
    prompt_template = get_function_call_prompt_template(trigger_signal, custom_template)
    prompt_content = prompt_template.replace("{tools_list}", "\n\n".join(tools_list_str))
    
    return prompt_content, trigger_signal

