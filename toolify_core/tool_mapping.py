# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Tool call mapping manager with TTL and size limit.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


class ToolCallMappingManager:
    """
    Tool call mapping manager with TTL (Time To Live) and size limit.
    
    Features:
    1. Automatic expiration cleanup - entries are automatically deleted after specified time
    2. Size limit - prevents unlimited memory growth
    3. LRU eviction - removes least recently used entries when size limit is reached
    4. Thread safe - supports concurrent access
    5. Periodic cleanup - background thread regularly cleans up expired entries
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600, cleanup_interval: int = 300):
        """
        Initialize mapping manager.
        
        Args:
            max_size: Maximum number of stored entries
            ttl_seconds: Entry time to live (seconds)
            cleanup_interval: Cleanup interval (seconds)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        
        self._data: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
        
        logger.debug(
            f"🔧 [INIT] Tool call mapping manager started - Max entries: {max_size}, TTL: {ttl_seconds}s, Cleanup interval: {cleanup_interval}s")
    
    def store(self, tool_call_id: str, name: str, args: dict, description: str = "") -> None:
        """Store tool call mapping."""
        with self._lock:
            current_time = time.time()
            
            if tool_call_id in self._data:
                del self._data[tool_call_id]
                del self._timestamps[tool_call_id]
            
            while len(self._data) >= self.max_size:
                oldest_key = next(iter(self._data))
                del self._data[oldest_key]
                del self._timestamps[oldest_key]
                logger.debug(f"🔧 [CLEANUP] Removed oldest entry due to size limit: {oldest_key}")
            
            self._data[tool_call_id] = {
                "name": name,
                "args": args,
                "description": description,
                "created_at": current_time
            }
            self._timestamps[tool_call_id] = current_time
            
            logger.debug(f"🔧 Stored tool call mapping: {tool_call_id} -> {name}")
            logger.debug(f"🔧 Current mapping table size: {len(self._data)}")
    
    def get(self, tool_call_id: str) -> Optional[Dict[str, Any]]:
        """Get tool call mapping (updates LRU order)."""
        with self._lock:
            current_time = time.time()
            
            if tool_call_id not in self._data:
                logger.debug(f"🔧 Tool call mapping not found: {tool_call_id}")
                logger.debug(f"🔧 All IDs in current mapping table: {list(self._data.keys())}")
                return None
            
            if current_time - self._timestamps[tool_call_id] > self.ttl_seconds:
                logger.debug(f"🔧 Tool call mapping expired: {tool_call_id}")
                del self._data[tool_call_id]
                del self._timestamps[tool_call_id]
                return None
            
            result = self._data[tool_call_id]
            self._data.move_to_end(tool_call_id)
            
            logger.debug(f"🔧 Found tool call mapping: {tool_call_id} -> {result['name']}")
            return result
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries, return the number of cleaned entries."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, timestamp in self._timestamps.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._data[key]
                del self._timestamps[key]
            
            if expired_keys:
                logger.debug(f"🔧 [CLEANUP] Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        with self._lock:
            current_time = time.time()
            expired_count = sum(1 for ts in self._timestamps.values()
                              if current_time - ts > self.ttl_seconds)
            
            return {
                "total_entries": len(self._data),
                "expired_entries": expired_count,
                "active_entries": len(self._data) - expired_count,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "memory_usage_ratio": len(self._data) / self.max_size
            }
    
    def _periodic_cleanup(self) -> None:
        """Background periodic cleanup thread."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                cleaned = self.cleanup_expired()
                
                stats = self.get_stats()
                if stats["total_entries"] > 0:
                    logger.debug(f"🔧 [STATS] Mapping table status: Total={stats['total_entries']}, "
                               f"Active={stats['active_entries']}, Memory usage={stats['memory_usage_ratio']:.1%}")
                
            except Exception as e:
                logger.error(f"❌ Background cleanup thread exception: {e}")


# Global instance
TOOL_CALL_MAPPING_MANAGER = ToolCallMappingManager(
    max_size=1000,
    ttl_seconds=3600,
    cleanup_interval=300
)


def store_tool_call_mapping(tool_call_id: str, name: str, args: dict, description: str = ""):
    """Store mapping between tool call ID and call content."""
    TOOL_CALL_MAPPING_MANAGER.store(tool_call_id, name, args, description)


def get_tool_call_mapping(tool_call_id: str) -> Optional[Dict[str, Any]]:
    """Get call content corresponding to tool call ID."""
    return TOOL_CALL_MAPPING_MANAGER.get(tool_call_id)

