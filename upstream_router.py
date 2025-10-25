# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Upstream service routing logic.
"""

import random
import logging
from typing import List, Dict, Any, Tuple, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def find_upstream(
    model_name: str,
    model_to_service_mapping: Dict[str, List[Dict[str, Any]]],
    alias_mapping: Dict[str, List[str]],
    default_service: Dict[str, Any],
    model_passthrough: bool = False,
    all_services: List[Any] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Find upstream configurations by model name, handling aliases and passthrough mode.
    Returns list of services sorted by priority and the actual model name to use.
    """
    
    # Handle model passthrough mode
    if model_passthrough:
        logger.info("🔄 Model passthrough mode is active. Using all configured services.")
        service_list = []
        for service in all_services:
            service_dict = service.model_dump() if hasattr(service, 'model_dump') else service
            # Skip services with empty API keys
            if not service_dict.get("api_key") or service_dict.get("api_key").strip() == "":
                logger.warning(f"⚠️  Skipping service '{service_dict.get('name')}' with empty API key")
                continue
            service_list.append(service_dict)

        if service_list:
            # Sort by priority (higher number = higher priority)
            service_list = sorted(service_list, key=lambda x: x.get('priority', 0), reverse=True)
            priority_list = [f"{s['name']}({s.get('priority', 0)})" for s in service_list]
            logger.info(f"📋 Found {len(service_list)} valid services, priority order: {priority_list}")
            return service_list, model_name
        else:
            raise HTTPException(status_code=500, detail="配置错误：model_passthrough 模式下没有找到有效的上游服务")

    # Default routing logic
    chosen_model_entry = model_name
    
    if model_name in alias_mapping:
        chosen_model_entry = random.choice(alias_mapping[model_name])
        logger.info(
            f"🔄 Model alias '{model_name}' detected. Randomly selected '{chosen_model_entry}' for this request.")

    services = model_to_service_mapping.get(chosen_model_entry)

    if services:
        # Filter out services with empty API keys and log warning
        valid_services = []
        for service in services:
            if not service.get("api_key") or service.get("api_key").strip() == "":
                logger.warning(f"⚠️  Skipping service '{service.get('name')}' - API key is empty")
            else:
                valid_services.append(service)

        if not valid_services:
            raise HTTPException(status_code=500,
                                detail=f"Model configuration error: No valid API keys found for model '{chosen_model_entry}'")

        services = valid_services
    else:
        logger.warning(f"⚠️  Model '{model_name}' not found in configuration, using default service")
        services = [default_service]
        if not services[0].get("api_key"):
            raise HTTPException(status_code=500, detail="Service configuration error: Default API key not found.")

    actual_model_name = chosen_model_entry
    if ':' in chosen_model_entry:
         parts = chosen_model_entry.split(':', 1)
         if len(parts) == 2:
             _, actual_model_name = parts
            
    return services, actual_model_name

