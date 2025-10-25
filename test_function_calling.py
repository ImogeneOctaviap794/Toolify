#!/usr/bin/env python3
"""
Toolify 函数调用测试脚本
测试 claude-sonnet-4-20250514 模型的工具调用能力
"""

import json
from openai import OpenAI

# 连接到 Toolify 中间件
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="65187777"  # 配置文件中的 allowed_keys
)

# 定义测试工具：获取天气信息
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、深圳"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如：2+2、10*5"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

def test_single_tool_call():
    """测试单个工具调用"""
    print("\n" + "="*60)
    print("测试 1: 单个工具调用 - 查询天气")
    print("="*60)
    
    response = client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "北京今天天气怎么样？"}
        ],
        tools=tools,
        temperature=0.7
    )
    
    print(f"\n📝 模型: {response.model}")
    print(f"🎯 完成原因: {response.choices[0].finish_reason}")
    
    if response.choices[0].message.tool_calls:
        print(f"🔧 工具调用数量: {len(response.choices[0].message.tool_calls)}")
        for i, tool_call in enumerate(response.choices[0].message.tool_calls, 1):
            print(f"\n  工具 #{i}:")
            print(f"    - ID: {tool_call.id}")
            print(f"    - 名称: {tool_call.function.name}")
            print(f"    - 参数: {tool_call.function.arguments}")
    else:
        print(f"💬 回复: {response.choices[0].message.content}")
    
    print(f"\n📊 Token 使用:")
    print(f"    - 输入: {response.usage.prompt_tokens}")
    print(f"    - 输出: {response.usage.completion_tokens}")
    print(f"    - 总计: {response.usage.total_tokens}")

def test_multiple_tool_calls():
    """测试多个工具调用"""
    print("\n" + "="*60)
    print("测试 2: 多个工具调用 - 天气查询 + 计算")
    print("="*60)
    
    response = client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "帮我查一下北京和上海的天气，然后计算 25 + 37 等于多少"}
        ],
        tools=tools,
        temperature=0.7
    )
    
    print(f"\n📝 模型: {response.model}")
    print(f"🎯 完成原因: {response.choices[0].finish_reason}")
    
    if response.choices[0].message.tool_calls:
        print(f"🔧 工具调用数量: {len(response.choices[0].message.tool_calls)}")
        for i, tool_call in enumerate(response.choices[0].message.tool_calls, 1):
            print(f"\n  工具 #{i}:")
            print(f"    - ID: {tool_call.id}")
            print(f"    - 名称: {tool_call.function.name}")
            print(f"    - 参数: {tool_call.function.arguments}")
    else:
        print(f"💬 回复: {response.choices[0].message.content}")
    
    print(f"\n📊 Token 使用:")
    print(f"    - 输入: {response.usage.prompt_tokens}")
    print(f"    - 输出: {response.usage.completion_tokens}")
    print(f"    - 总计: {response.usage.total_tokens}")

def test_no_tool_needed():
    """测试不需要工具的普通对话"""
    print("\n" + "="*60)
    print("测试 3: 普通对话 - 不需要工具")
    print("="*60)
    
    response = client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        tools=tools,
        temperature=0.7
    )
    
    print(f"\n📝 模型: {response.model}")
    print(f"🎯 完成原因: {response.choices[0].finish_reason}")
    
    if response.choices[0].message.tool_calls:
        print(f"🔧 工具调用数量: {len(response.choices[0].message.tool_calls)}")
    else:
        print(f"💬 回复: {response.choices[0].message.content}")
    
    print(f"\n📊 Token 使用:")
    print(f"    - 输入: {response.usage.prompt_tokens}")
    print(f"    - 输出: {response.usage.completion_tokens}")
    print(f"    - 总计: {response.usage.total_tokens}")

def test_streaming():
    """测试流式响应"""
    print("\n" + "="*60)
    print("测试 4: 流式响应 - 工具调用")
    print("="*60)
    
    stream = client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "深圳现在天气如何？"}
        ],
        tools=tools,
        stream=True,
        temperature=0.7
    )
    
    print("\n📡 流式输出:")
    tool_calls_detected = False
    
    for chunk in stream:
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                if not tool_calls_detected:
                    print("\n🔧 检测到工具调用!")
                    tool_calls_detected = True
                
                for tool_call in delta.tool_calls:
                    if hasattr(tool_call, 'function') and tool_call.function:
                        if hasattr(tool_call.function, 'name') and tool_call.function.name:
                            print(f"  - 工具: {tool_call.function.name}")
                        if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                            print(f"  - 参数片段: {tool_call.function.arguments}", end='')
            
            elif hasattr(delta, 'content') and delta.content:
                print(delta.content, end='', flush=True)
            
            if chunk.choices[0].finish_reason:
                print(f"\n\n🎯 完成原因: {chunk.choices[0].finish_reason}")

if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("Toolify 函数调用功能测试")
    print("测试模型: claude-sonnet-4-20250514")
    print("🚀"*30)
    
    try:
        # 执行所有测试
        test_single_tool_call()
        test_multiple_tool_calls()
        test_no_tool_needed()
        test_streaming()
        
        print("\n" + "✅"*30)
        print("所有测试完成！")
        print("✅"*30 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

