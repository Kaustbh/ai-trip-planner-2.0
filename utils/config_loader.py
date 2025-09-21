"""
Configuration loader utilities for AI Trip Planner
"""

import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file and environment variables.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Load environment variables
    load_dotenv()
    
    config = {}
    
    # Load from file if provided
    if config_path and Path(config_path).exists():
        config_path = Path(config_path)
        
        if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        elif config_path.suffix.lower() == '.json':
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    # Load default configurations
    default_config = load_default_config()
    
    # Merge configurations (file config overrides default)
    config = merge_configs(default_config, config)
    
    # Substitute environment variables
    config = substitute_env_vars(config)
    
    return config


def load_default_config() -> Dict[str, Any]:
    """Load default configuration."""
    return {
        "app": {
            "name": "AI Trip Planner",
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO"
        },
        "agents": {
            "max_concurrent": 5,
            "timeout": 30,
            "retry_attempts": 3
        },
        "protocols": {
            "default": "hybrid",
            "timeout": 30,
            "retry_attempts": 3
        },
        "memory": {
            "type": "vector",
            "max_items": 1000,
            "ttl": 3600
        },
        "tools": {
            "timeout": 30,
            "retry_attempts": 3,
            "rate_limit": 60
        },
        "workflows": {
            "max_concurrent_tasks": 5,
            "timeout": 300,
            "retry_failed_tasks": True
        },
        "orchestrators": {
            "max_concurrent_agents": 10,
            "task_timeout": 300,
            "monitoring_enabled": True
        }
    }


def merge_configs(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        default: Default configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = default.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Substitute environment variables in configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with environment variables substituted
    """
    def substitute_value(value: Any) -> Any:
        if isinstance(value, str):
            # Handle ${VAR} and ${VAR:default} patterns
            import re
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                return os.getenv(var_name, default_value)
            
            return re.sub(pattern, replace_var, value)
        elif isinstance(value, dict):
            return {k: substitute_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [substitute_value(item) for item in value]
        else:
            return value
    
    return substitute_value(config)


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., "database.host")
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> None:
    """
    Set a configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., "database.host")
        value: Value to set
    """
    keys = key_path.split('.')
    current = config
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def validate_config(config: Dict[str, Any], required_keys: list) -> bool:
    """
    Validate that required configuration keys are present.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required key paths
        
    Returns:
        True if all required keys are present
    """
    for key_path in required_keys:
        if get_config_value(config, key_path) is None:
            return False
    return True


def save_config(config: Dict[str, Any], file_path: str) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary
        file_path: Path to save configuration
    """
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.yaml' or file_path.suffix.lower() == '.yml':
        with open(file_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    elif file_path.suffix.lower() == '.json':
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    else:
        raise ValueError(f"Unsupported config file format: {file_path.suffix}")
