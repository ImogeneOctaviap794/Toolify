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

**📋 MANDATORY TOOL CALL FORMAT - THIS IS CRITICAL:**

When you decide to use tools, you MUST follow this EXACT format. Any deviation will cause complete failure:

**STEP 1 - Output the trigger signal on a new line (EXACTLY as shown, no modifications):**
{trigger_signal}

**STEP 2 - Immediately output the XML (starting from the next line, no extra text):**
<function_calls>
    <function_call>
        <tool>EXACT_TOOL_NAME</tool>
        <args>
            <param_name>value</param_name>
        </args>
    </function_call>
</function_calls>

**CRITICAL RULES:**
1. The trigger signal `{trigger_signal}` MUST be on its own line
2. NO text before the trigger signal on that line
3. NO text between trigger signal and <function_calls>
4. NO extra <function_calls> nesting (only ONE opening, ONE closing)
5. You CAN have text BEFORE the trigger signal (like "Let me check...")
6. You MUST NOT have text AFTER </function_calls> - stop immediately after closing tag

STRICT ARGUMENT KEY RULES:
- You MUST use parameter keys EXACTLY as defined (case- and punctuation-sensitive). Do NOT rename, add, or remove characters.
- If a key starts with a hyphen (e.g., -i, -C), you MUST keep the hyphen in the tag name. Example: <-i>true</-i>, <-C>2</-C>.
- Never convert "-i" to "i" or "-C" to "C". Do not pluralize, translate, or alias parameter keys.
- The <tool> tag must contain the exact name of a tool from the list. Any other tool name is invalid.
- The <args> must contain all required arguments for that tool.

**✅ CORRECT EXAMPLE:**
```
User: "北京今天天气怎么样？"

Your response:
我来帮你查询北京的天气。
{trigger_signal}
<function_calls>
    <function_call>
        <tool>get_weather</tool>
        <args>
            <location>北京</location>
            <unit>celsius</unit>
        </args>
    </function_call>
</function_calls>
```

**❌ WRONG EXAMPLE 1 - Double nesting (DON'T DO THIS):**
```
{trigger_signal}
<function_calls>
<function_calls>    ← ❌ WRONG! Only ONE <function_calls> tag
    <function_call>
        ...
    </function_call>
</function_calls>
</function_calls>
```

**❌ WRONG EXAMPLE 2 - Text after closing tag (DON'T DO THIS):**
```
{trigger_signal}
<function_calls>
    <function_call>
        <tool>get_weather</tool>
        <args><location>北京</location></args>
    </function_call>
</function_calls>

根据查询结果...  ← ❌ WRONG! Stop immediately after </function_calls>
```

**❌ WRONG EXAMPLE 3 - Missing trigger signal (DON'T DO THIS):**
```
<function_calls>    ← ❌ WRONG! Must have trigger signal first
    <function_call>
        ...
    </function_call>
</function_calls>
```

**🎯 REMEMBER:**
- Trigger signal {trigger_signal} MUST appear BEFORE <function_calls>
- Only ONE <function_calls> wrapper (no nesting)
- STOP immediately after </function_calls> (no more text)
- Tool will be executed and results returned to you

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

