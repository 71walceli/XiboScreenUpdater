"""
Integration test for the complete workflow.

This test validates that the refactored system can load configuration,
initialize providers, and handle the basic workflow.
"""

import unittest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from xibo_screen_updater.core.application import XiboScreenUpdater
from xibo_screen_updater.core.config_manager import ConfigurationError


class TestXiboScreenUpdaterIntegration(unittest.TestCase):
    """Integration tests for the complete application."""
    
    def setUp(self):
        """Set up test fixtures."""
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
    
    def test_application_initialization(self):
        """Test that the application can initialize with valid config."""
        config_file = self.create_temp_config(self.valid_config)
        
        try:
            app = XiboScreenUpdater(config_file)
            
            # Should not raise an exception during creation
            self.assertIsNotNone(app)
            self.assertEqual(app.config_path, config_file)
            self.assertIsNotNone(app.config_manager)
            self.assertIsNotNone(app.logger)
            
        finally:
            os.unlink(config_file)
    
    def test_application_initialization_with_invalid_config(self):
        """Test application behavior with invalid config."""
        invalid_config = {'invalid': 'config'}
        config_file = self.create_temp_config(invalid_config)
        
        try:
            app = XiboScreenUpdater(config_file)
            
            # Should raise ConfigurationError during initialization
            with self.assertRaises((ConfigurationError, RuntimeError)):
                app.initialize()
                
        finally:
            os.unlink(config_file)
    
    @patch('xibo_screen_updater.providers.nextcloud.NextCloudProvider.connect')
    @patch('xibo_screen_updater.providers.xibo.XiboProvider.authenticate')
    def test_provider_initialization(self, mock_xibo_auth, mock_nc_connect):
        """Test that providers are initialized correctly."""
        config_file = self.create_temp_config(self.valid_config)
        
        # Mock successful connections
        mock_nc_connect.return_value = True
        mock_xibo_auth.return_value = True
        
        try:
            app = XiboScreenUpdater(config_file)
            app.initialize()
            
            # Check that providers were created
            self.assertIsNotNone(app.nextcloud_provider)
            self.assertIsNotNone(app.xibo_provider)
            
            # Check that connection methods were called
            mock_nc_connect.assert_called_once()
            mock_xibo_auth.assert_called_once()
            
        finally:
            os.unlink(config_file)
    
    @patch('xibo_screen_updater.providers.nextcloud.NextCloudProvider.connect')
    def test_nextcloud_connection_failure(self, mock_nc_connect):
        """Test handling of NextCloud connection failure."""
        config_file = self.create_temp_config(self.valid_config)
        
        # Mock failed connection
        mock_nc_connect.return_value = False
        
        try:
            app = XiboScreenUpdater(config_file)
            
            with self.assertRaises(RuntimeError) as cm:
                app.initialize()
            
            self.assertIn('Failed to connect to NextCloud', str(cm.exception))
            
        finally:
            os.unlink(config_file)
    
    @patch('xibo_screen_updater.providers.nextcloud.NextCloudProvider.connect')
    @patch('xibo_screen_updater.providers.xibo.XiboProvider.authenticate')
    def test_xibo_authentication_failure(self, mock_xibo_auth, mock_nc_connect):
        """Test handling of Xibo authentication failure."""
        config_file = self.create_temp_config(self.valid_config)
        
        # Mock successful NextCloud but failed Xibo
        mock_nc_connect.return_value = True
        mock_xibo_auth.return_value = False
        
        try:
            app = XiboScreenUpdater(config_file)
            
            with self.assertRaises(RuntimeError) as cm:
                app.initialize()
            
            self.assertIn('Failed to authenticate with Xibo', str(cm.exception))
            
        finally:
            os.unlink(config_file)


if __name__ == '__main__':
    unittest.main()
