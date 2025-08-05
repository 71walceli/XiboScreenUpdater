"""
Unit tests for configuration management.
"""

import unittest
import tempfile
import os
import yaml
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from xibo_screen_updater.core.config_manager import ConfigManager, ConfigurationError, resolve_config_path


class TestConfigManager(unittest.TestCase):
    """Test configuration management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        
        # Sample valid config
        self.valid_config = {
            'copy_from': {
                'provider': 'nextcloud',
                'server': 'http://localhost:8080',
                'path': 'test-path',
                'auth': {
                    'user': 'testuser',
                    'password': 'testpass'
                },
                'extensions': ['.jpg', '.png'],
                'poll_interval': 10
            },
            'project_to': {
                'provider': 'xibo',
                'host': 'http://localhost:8082/api/',
                'auth': {
                    'client_id': 'test_client',
                    'client_secret': 'test_secret'
                },
                'display': {
                    'name': 'Test Display',
                    'width': 1920,
                    'height': 1080
                }
            }
        }
    
    def create_temp_config(self, config_data):
        """Create a temporary config file with given data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    def test_load_valid_config(self):
        """Test loading a valid configuration."""
        config_file = self.create_temp_config(self.valid_config)
        
        try:
            config = self.config_manager.load_config(config_file)
            self.assertEqual(config, self.valid_config)
            self.assertEqual(self.config_manager.config_path, config_file)
        finally:
            os.unlink(config_file)
    
    def test_load_nonexistent_config(self):
        """Test loading a non-existent configuration file."""
        with self.assertRaises(ConfigurationError) as cm:
            self.config_manager.load_config('/path/that/does/not/exist.yaml')
        
        self.assertIn('Configuration file not found', str(cm.exception))
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [unclosed')
            config_file = f.name
        
        try:
            with self.assertRaises(ConfigurationError) as cm:
                self.config_manager.load_config(config_file)
            self.assertIn('Invalid YAML', str(cm.exception))
        finally:
            os.unlink(config_file)
    
    def test_missing_copy_from_section(self):
        """Test config missing copy_from section."""
        invalid_config = {'project_to': self.valid_config['project_to']}
        config_file = self.create_temp_config(invalid_config)
        
        try:
            with self.assertRaises(ConfigurationError) as cm:
                self.config_manager.load_config(config_file)
            self.assertIn('Missing required field in copy_from', str(cm.exception))
        finally:
            os.unlink(config_file)
    
    def test_missing_project_to_section(self):
        """Test config missing project_to section."""
        invalid_config = {'copy_from': self.valid_config['copy_from']}
        config_file = self.create_temp_config(invalid_config)
        
        try:
            with self.assertRaises(ConfigurationError) as cm:
                self.config_manager.load_config(config_file)
            self.assertIn('Missing required field in project_to', str(cm.exception))
        finally:
            os.unlink(config_file)
    
    def test_get_display_name(self):
        """Test getting display name."""
        config_file = self.create_temp_config(self.valid_config)
        
        try:
            self.config_manager.load_config(config_file)
            display_name = self.config_manager.get_display_name()
            self.assertEqual(display_name, 'Test Display')
        finally:
            os.unlink(config_file)
    
    def test_get_poll_interval(self):
        """Test getting poll interval."""
        config_file = self.create_temp_config(self.valid_config)
        
        try:
            self.config_manager.load_config(config_file)
            poll_interval = self.config_manager.get_poll_interval()
            self.assertEqual(poll_interval, 10)
        finally:
            os.unlink(config_file)
    
    def test_get_poll_interval_default(self):
        """Test getting default poll interval."""
        config_without_poll = self.valid_config.copy()
        del config_without_poll['copy_from']['poll_interval']
        config_file = self.create_temp_config(config_without_poll)
        
        try:
            self.config_manager.load_config(config_file)
            poll_interval = self.config_manager.get_poll_interval()
            self.assertEqual(poll_interval, 10)  # Default value
        finally:
            os.unlink(config_file)


class TestConfigPathResolution(unittest.TestCase):
    """Test configuration path resolution logic."""
    
    def test_cli_arg_priority(self):
        """Test that CLI argument has highest priority."""
        with patch.dict(os.environ, {'CONFIG_PATH': '/env/path.yaml'}):
            result = resolve_config_path('/cli/path.yaml')
            self.assertEqual(result, '/cli/path.yaml')
    
    def test_env_var_priority(self):
        """Test that environment variable has second priority."""
        with patch.dict(os.environ, {'CONFIG_PATH': '/env/path.yaml'}):
            result = resolve_config_path(None)
            self.assertEqual(result, '/env/path.yaml')
    
    def test_default_priority(self):
        """Test that default path is used when no other options."""
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_config_path(None)
            self.assertEqual(result, './config.yaml')


if __name__ == '__main__':
    unittest.main()
