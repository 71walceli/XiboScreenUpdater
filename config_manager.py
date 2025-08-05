"""
Configuration management module for Xibo Screen Updater.

Provides centralized configuration loading, validation, and management.
"""

import os
import sys
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConfigPaths:
    """Configuration file path resolution."""
    cli_arg: Optional[str] = None
    env_var: Optional[str] = None
    default: str = "./config.yaml"
    
    def resolve(self) -> str:
        """Resolve configuration file path using priority order."""
        if self.cli_arg:
            return self.cli_arg
        if self.env_var:
            return self.env_var
        return self.default


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._config_path: Optional[str] = None
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded configuration dictionary
            
        Raises:
            ConfigurationError: If config file cannot be loaded or is invalid
        """
        try:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r') as file:
                self._config = yaml.safe_load(file)
            
            self._config_path = config_path
            self._validate_config()
            return self._config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading config file {config_path}: {e}")
    
    def _validate_config(self):
        """Validate loaded configuration."""
        if not self._config:
            raise ConfigurationError("Configuration is empty")
        
        # Validate copy_from section
        copy_from = self._config.get('copy_from', {})
        required_copy_from = ['provider', 'server', 'path', 'auth', 'extensions']
        for field in required_copy_from:
            if field not in copy_from:
                raise ConfigurationError(f"Missing required field in copy_from: {field}")
        
        # Validate copy_from.auth
        auth = copy_from.get('auth', {})
        if 'user' not in auth or 'password' not in auth:
            raise ConfigurationError("Missing user or password in copy_from.auth")
        
        # Validate project_to section
        project_to = self._config.get('project_to', {})
        required_project_to = ['provider', 'host', 'auth', 'display']
        for field in required_project_to:
            if field not in project_to:
                raise ConfigurationError(f"Missing required field in project_to: {field}")
        
        # Validate project_to.auth
        xibo_auth = project_to.get('auth', {})
        if 'client_id' not in xibo_auth or 'client_secret' not in xibo_auth:
            raise ConfigurationError("Missing client_id or client_secret in project_to.auth")
        
        # Validate display
        display = project_to.get('display', {})
        if 'name' not in display:
            raise ConfigurationError("Missing name in project_to.display")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get current configuration."""
        if not self._config:
            raise ConfigurationError("Configuration not loaded")
        return self._config
    
    @property
    def config_path(self) -> str:
        """Get current configuration file path."""
        if not self._config_path:
            raise ConfigurationError("Configuration not loaded")
        return self._config_path
    
    def get_nextcloud_config(self) -> Dict[str, Any]:
        """Get NextCloud configuration section."""
        return self.config.get('copy_from', {})
    
    def get_xibo_config(self) -> Dict[str, Any]:
        """Get Xibo configuration section."""
        return self.config.get('project_to', {})
    
    def get_display_name(self) -> str:
        """Get target display name."""
        return self.config['project_to']['display']['name']
    
    def get_poll_interval(self) -> int:
        """Get polling interval in seconds."""
        return self.config['copy_from'].get('poll_interval', 10)
    
    def get_extensions(self) -> list:
        """Get file extensions to monitor."""
        return self.config['copy_from'].get('extensions', [])


def resolve_config_path(cli_arg: Optional[str] = None) -> str:
    """
    Resolve configuration file path using priority order.
    
    Args:
        cli_arg: Configuration path from command line argument
        
    Returns:
        Resolved configuration file path
    """
    paths = ConfigPaths(
        cli_arg=cli_arg,
        env_var=os.environ.get('CONFIG_PATH'),
        default='./config.yaml'
    )
    return paths.resolve()
