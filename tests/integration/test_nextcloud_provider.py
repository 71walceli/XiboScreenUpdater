"""
Integration tests for NextCloud provider functionality.
"""

import unittest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from xibo_screen_updater.providers.nextcloud import NextCloudProvider, create_nextcloud_provider


class TestNextCloudProviderIntegration(unittest.TestCase):
    """Integration tests for NextCloud provider."""
    
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
            }
        }
    
    def create_temp_config(self, config_data):
        """Create a temporary config file with given data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    def test_create_nextcloud_provider_from_config(self):
        """Test creating NextCloud provider from configuration."""
        provider = create_nextcloud_provider(self.valid_config)
        
        self.assertIsInstance(provider, NextCloudProvider)
        self.assertEqual(provider.server_url, 'http://localhost:8080')
        self.assertEqual(provider.username, 'testuser')
        self.assertEqual(provider.password, 'testpass')
    
    def test_create_nextcloud_provider_invalid_config(self):
        """Test creating NextCloud provider with invalid configuration."""
        invalid_config = {'copy_from': {'provider': 'invalid'}}
        
        with self.assertRaises(ValueError) as cm:
            create_nextcloud_provider(invalid_config)
        
        self.assertIn('must have copy_from.provider set to \'nextcloud\'', str(cm.exception))
    
    def test_create_nextcloud_provider_missing_credentials(self):
        """Test creating NextCloud provider with missing credentials."""
        incomplete_config = {
            'copy_from': {
                'provider': 'nextcloud',
                'server': 'http://localhost:8080',
                'auth': {
                    'user': 'testuser'
                    # missing password
                }
            }
        }
        
        with self.assertRaises(ValueError) as cm:
            create_nextcloud_provider(incomplete_config)
        
        self.assertIn('Missing required NextCloud configuration', str(cm.exception))
    
    @patch('xibo_screen_updater.providers.nextcloud.requests.request')
    def test_connection_success(self, mock_request):
        """Test successful connection to NextCloud."""
        # Mock successful WebDAV response
        mock_response = Mock()
        mock_response.status_code = 207  # Multi-Status for WebDAV
        mock_request.return_value = mock_response
        
        provider = create_nextcloud_provider(self.valid_config)
        result = provider.connect()
        
        self.assertTrue(result)
        mock_request.assert_called_once()
    
    @patch('xibo_screen_updater.providers.nextcloud.requests.request')
    def test_connection_failure(self, mock_request):
        """Test failed connection to NextCloud."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        provider = create_nextcloud_provider(self.valid_config)
        result = provider.connect()
        
        self.assertFalse(result)
    
    @patch('xibo_screen_updater.providers.nextcloud.requests.request')
    def test_connection_network_error(self, mock_request):
        """Test network error during connection."""
        # Mock network error
        mock_request.side_effect = Exception("Network error")
        
        provider = create_nextcloud_provider(self.valid_config)
        result = provider.connect()
        
        self.assertFalse(result)


class TestNextCloudProviderLiveIntegration(unittest.TestCase):
    """Live integration tests (require actual config file)."""
    
    def setUp(self):
        """Set up for live tests."""
        self.config_file = "config/example.yaml"
        self.skip_if_no_config()
    
    def skip_if_no_config(self):
        """Skip tests if config file doesn't exist or has dummy values."""
        if not os.path.exists(self.config_file):
            self.skipTest("No example config file found")
        
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        server = config.get('copy_from', {}).get('server', '')
        if 'your-nextcloud-server' in server or 'localhost' in server:
            self.skipTest("Config file contains dummy values")
    
    def test_live_connection(self):
        """Test actual connection to NextCloud server (requires valid config)."""
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        try:
            provider = create_nextcloud_provider(config)
            result = provider.connect()
            
            if result:
                print("✅ Successfully connected to NextCloud")
                
                # Test file listing
                files = provider.get_files(
                    config['copy_from']['path'],
                    config['copy_from']['extensions']
                )
                print(f"✅ Found {len(files)} files")
                
                if files:
                    for file_info in files[:3]:  # Show first 3
                        print(f"   - {file_info.name} ({file_info.size} bytes)")
            else:
                print("❌ Failed to connect to NextCloud")
                
        except Exception as e:
            self.fail(f"Live test failed: {e}")


if __name__ == '__main__':
    # Run both mocked and live tests
    print("NextCloud Provider Integration Tests")
    print("=" * 50)
    
    unittest.main(verbosity=2)
