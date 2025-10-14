# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

import os
import yaml
from typing import List, Dict, Any, Set, Optional
from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Server configuration"""
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host address")
    timeout: int = Field(default=180, ge=1, description="Request timeout (seconds)")


class UpstreamService(BaseModel):
    """Upstream service configuration"""
    name: str = Field(description="Service name")
    base_url: str = Field(description="Service base URL")
    api_key: str = Field(description="API key")
    models: List[str] = Field(default_factory=list, description="List of supported models")
    description: str = Field(default="", description="Service description")
    is_default: bool = Field(default=False, description="Is default service")
    priority: int = Field(default=0, description="Priority level (lower number = higher priority, 0 is highest)")
    
    @field_validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')
    
    @field_validator('api_key')
    def validate_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError('api_key cannot be empty')
        return v
    
    @field_validator('models')
    def validate_models(cls, v):
        # Allow empty models list when model_passthrough is enabled
        # This will be validated at AppConfig level
        if v:
            for model in v:
                if not model or model.strip() == "":
                    raise ValueError('model name cannot be empty')
        return v if v else []


class ClientAuthConfig(BaseModel):
    """Client authentication configuration"""
    allowed_keys: List[str] = Field(description="List of allowed client API keys")
    
    @field_validator('allowed_keys')
    def validate_allowed_keys(cls, v):
        if not v or len(v) == 0:
            raise ValueError('allowed_keys cannot be empty')
        for key in v:
            if not key or key.strip() == "":
                raise ValueError('API key cannot be empty')
        return v


class AdminAuthConfig(BaseModel):
    """Admin authentication configuration"""
    username: str = Field(description="Admin username")
    password: str = Field(description="Admin password (bcrypt hashed)")
    jwt_secret: str = Field(description="JWT secret key for token signing")
    
    @field_validator('username')
    def validate_username(cls, v):
        if not v or v.strip() == "":
            raise ValueError('username cannot be empty')
        return v.strip()
    
    @field_validator('password')
    def validate_password(cls, v):
        if not v or v.strip() == "":
            raise ValueError('password cannot be empty')
        return v
    
    @field_validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if not v or v.strip() == "":
            raise ValueError('jwt_secret cannot be empty')
        if len(v) < 32:
            raise ValueError('jwt_secret must be at least 32 characters long')
        return v


class FeaturesConfig(BaseModel):
    """Feature configuration"""
    enable_function_calling: bool = Field(default=True, description="Enable function calling")
    log_level: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL, or DISABLED")
    convert_developer_to_system: bool = Field(default=True, description="Convert developer role to system role")
    prompt_template: Optional[str] = Field(default=None, description="Custom prompt template for function calling")
    key_passthrough: bool = Field(default=False, description="If true, directly forward client-provided API key to upstream instead of using configured upstream key")
    model_passthrough: bool = Field(default=False, description="If true, forward all requests directly to the 'openai' upstream service, ignoring model-based routing")

    @field_validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator('prompt_template')
    def validate_prompt_template(cls, v):
        if v:
            if "{tools_list}" not in v or "{trigger_signal}" not in v:
                raise ValueError("prompt_template must contain {tools_list} and {trigger_signal} placeholders")
        return v


class AppConfig(BaseModel):
    """Application full configuration"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    upstream_services: List[UpstreamService] = Field(description="List of upstream services")
    client_authentication: ClientAuthConfig = Field(description="Client authentication configuration")
    admin_authentication: Optional[AdminAuthConfig] = Field(default=None, description="Admin authentication configuration")
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    
    @field_validator('upstream_services')
    def validate_upstream_services(cls, v, info):
        if not v or len(v) == 0:
            raise ValueError('upstream_services cannot be empty')
        
        # Get features config to check model_passthrough mode
        features = info.data.get('features', FeaturesConfig())
        model_passthrough = features.model_passthrough if hasattr(features, 'model_passthrough') else False
        
        # In model_passthrough mode, check for 'openai' service existence
        if model_passthrough:
            openai_service = next((s for s in v if s.name == 'openai'), None)
            if not openai_service:
                raise ValueError("When model_passthrough is enabled, an upstream service named 'openai' must be configured")
        else:
            # In normal mode, validate that services have models
            for service in v:
                if not service.models or len(service.models) == 0:
                    raise ValueError(f"Service '{service.name}' must have at least one model when model_passthrough is disabled")
        
        default_services = [service for service in v if service.is_default]
        if len(default_services) == 0:
            raise ValueError('Must have at least one default upstream service (is_default: true)')
        if len(default_services) > 1:
            raise ValueError('Only one upstream service can be marked as default')
        
        all_models = set()
        all_aliases = set()
        
        for service in v:
            for model in service.models:
                if model in all_models:
                    raise ValueError(f'Duplicate model entry found: {model}')
                all_models.add(model)
                
                if ':' in model:
                    parts = model.split(':', 1)
                    if len(parts) == 2:
                        alias, real_model = parts
                        if not alias.strip() or not real_model.strip():
                            raise ValueError(f"Invalid alias format in '{model}'. Both parts must not be empty.")
                        all_aliases.add(alias)
                    else:
                        raise ValueError(f"Invalid model format with colon: {model}")

        regular_models = {m for m in all_models if ':' not in m}
        conflicts = all_aliases.intersection(regular_models)
        if conflicts:
            raise ValueError(f"Alias names {conflicts} conflict with model names.")
                
        return v


class ConfigLoader:
    """Configuration loader"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: AppConfig = None
    
    def load_config(self) -> AppConfig:
        """Load configuration file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file '{self.config_path}' not found. "
                f"Please copy 'config.example.yaml' to '{self.config_path}' and modify the configuration as needed."
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Configuration file format error: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read configuration file: {e}")
        
        if not config_data:
            raise ValueError("Configuration file is empty")
        
        try:
            self._config = AppConfig(**config_data)
            return self._config
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    @property
    def config(self) -> AppConfig:
        """Get configuration object"""
        if self._config is None:
            self.load_config()
        return self._config

    def reload_config(self) -> AppConfig:
        """Force reload configuration from disk"""
        self._config = None
        return self.load_config()

    def reload_config(self) -> AppConfig:
        """Force reload configuration from disk"""
        self._config = None
        return self.load_config()
    
    def get_model_to_service_mapping(self) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[str]]]:
        """Get model to service mapping (now returns list of services per model, sorted by priority) and model aliases"""
        config = self.config
        model_mapping: Dict[str, List[Dict[str, Any]]] = {}
        alias_mapping = {}
        
        for service in config.upstream_services:
            service_info = {
                "name": service.name,
                "base_url": service.base_url,
                "api_key": service.api_key,
                "description": service.description,
                "is_default": service.is_default,
                "priority": service.priority
            }
            
            for model_entry in service.models:
                # Support multiple services for the same model
                if model_entry not in model_mapping:
                    model_mapping[model_entry] = []
                model_mapping[model_entry].append(service_info)
                
                if ':' in model_entry:
                    parts = model_entry.split(':', 1)
                    if len(parts) == 2:
                        alias, _ = parts
                        if alias not in alias_mapping:
                            alias_mapping[alias] = []
                        alias_mapping[alias].append(model_entry)
        
        # Sort services by priority (lower number = higher priority)
        for model_entry in model_mapping:
            model_mapping[model_entry] = sorted(model_mapping[model_entry], key=lambda x: x['priority'])
        
        return model_mapping, alias_mapping
    
    def get_default_service(self) -> Dict[str, Any]:
        """Get default service configuration"""
        config = self.config
        for service in config.upstream_services:
            if service.is_default:
                return {
                    "name": service.name,
                    "base_url": service.base_url,
                    "api_key": service.api_key,
                    "description": service.description,
                    "is_default": service.is_default
                }
        raise ValueError("No default service configured")
    
    def get_allowed_client_keys(self) -> Set[str]:
        """Get set of allowed client keys"""
        return set(self.config.client_authentication.allowed_keys)
    
    def get_log_level(self) -> str:
        """Get configured log level"""
        return self.config.features.log_level
    
    def get_features_config(self) -> Dict[str, Any]:
        """Get feature configuration"""
        return {
            "function_calling": self.config.features.enable_function_calling,
            "log_level": self.config.features.log_level,
            "convert_developer_to_system": self.config.features.convert_developer_to_system
        }


config_loader = ConfigLoader()