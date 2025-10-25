# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Function calling module for Toolify.
"""

from .parser import parse_function_calls_xml, remove_think_blocks
from .prompt import generate_function_prompt, generate_random_trigger_signal
from .streaming import StreamingFunctionCallDetector

__all__ = [
    'parse_function_calls_xml',
    'remove_think_blocks',
    'generate_function_prompt',
    'generate_random_trigger_signal',
    'StreamingFunctionCallDetector',
]

