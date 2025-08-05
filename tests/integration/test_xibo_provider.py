"""
Integration tests for Xibo provider functionality.
"""

import unittest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from xibo_screen_updater.providers.xibo import XiboProvider, create_xibo_provider


class TestXiboProviderIntegration(unittest.TestCase):
    """Integration tests for Xibo provider."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample valid config
        self.valid_config = {
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
    
    def test_create_xibo_provider_from_config(self):
        """Test creating Xibo provider from configuration."""
        provider = create_xibo_provider(self.valid_config)
        
        self.assertIsInstance(provider, XiboProvider)
        self.assertEqual(provider.server_url, 'http://localhost:8082/api')
        self.assertEqual(provider.client_id, 'test_client')
        self.assertEqual(provider.client_secret, 'test_secret')
    
    def test_create_xibo_provider_invalid_config(self):
        """Test creating Xibo provider with invalid configuration."""
        invalid_config = {'project_to': {'provider': 'invalid'}}
        
        with self.assertRaises(ValueError) as cm:
            create_xibo_provider(invalid_config)
        
        self.assertIn('must have project_to.provider set to \'xibo\'', str(cm.exception))
    
    def test_create_xibo_provider_missing_credentials(self):
        """Test creating Xibo provider with missing credentials."""
        incomplete_config = {
            'project_to': {
                'provider': 'xibo',
                'host': 'http://localhost:8082/api/',
                'auth': {
                    'client_id': 'test_client'
                    # missing client_secret
                }
            }
        }
        
        with self.assertRaises(ValueError) as cm:
            create_xibo_provider(incomplete_config)
        
        self.assertIn('Missing required Xibo configuration', str(cm.exception))
    
    @patch('xibo_screen_updater.providers.xibo.requests.post')
    def test_authentication_success(self, mock_post):
        """Test successful authentication with Xibo."""
        # Mock successful OAuth2 response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        provider = create_xibo_provider(self.valid_config)
        result = provider.authenticate()
        
        self.assertTrue(result)
        self.assertEqual(provider.access_token, 'test_token')
        mock_post.assert_called_once()
    
    @patch('xibo_screen_updater.providers.xibo.requests.post')
    def test_authentication_failure(self, mock_post):
        """Test failed authentication with Xibo."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response
        
        provider = create_xibo_provider(self.valid_config)
        result = provider.authenticate()
        
        self.assertFalse(result)
    
    @patch('xibo_screen_updater.providers.xibo.requests.post')
    def test_authentication_network_error(self, mock_post):
        """Test network error during authentication."""
        # Mock network error
        mock_post.side_effect = Exception("Network error")
        
        provider = create_xibo_provider(self.valid_config)
        result = provider.authenticate()
        
        self.assertFalse(result)
    
    @patch('xibo_screen_updater.providers.xibo.requests.request')
    @patch('xibo_screen_updater.providers.xibo.requests.post')
    def test_get_displays(self, mock_post, mock_request):
        """Test getting displays from Xibo."""
        # Mock authentication
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_auth_response
        
        # Mock displays response
        mock_displays_response = Mock()
        mock_displays_response.status_code = 200
        mock_displays_response.json.return_value = [
            {'displayId': 1, 'display': 'Test Display 1'},
            {'displayId': 2, 'display': 'Test Display 2'}
        ]
        mock_request.return_value = mock_displays_response
        
        provider = create_xibo_provider(self.valid_config)
        provider.authenticate()
        displays = provider.get_displays()
        
        self.assertEqual(len(displays), 2)
        self.assertEqual(displays[0]['display'], 'Test Display 1')


class TestXiboProviderLiveIntegration(unittest.TestCase):
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
        
        host = config.get('project_to', {}).get('host', '')
        if 'your-xibo-server' in host or 'localhost' in host:
            self.skipTest("Config file contains dummy values")
    
    def test_live_authentication(self):
        """Test actual authentication with Xibo server (requires valid config)."""
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        try:
            provider = create_xibo_provider(config, debug=True)
            result = provider.authenticate()
            
            if result:
                print("✅ Successfully authenticated with Xibo")
                
                # Test getting displays
                displays = provider.get_displays()
                print(f"✅ Found {len(displays)} displays")
                
                for display in displays[:3]:  # Show first 3
                    print(f"   - {display.get('display')} (ID: {display.get('displayId')})")
                
                # Test getting media library
                media_list = provider.get_media_list()
                print(f"✅ Found {len(media_list)} media items")
                
                # Test getting layouts
                layouts = provider.get_layouts()
                print(f"✅ Found {len(layouts)} layouts")
                
            else:
                print("❌ Failed to authenticate with Xibo")
                
        except Exception as e:
            self.fail(f"Live test failed: {e}")
    
    def test_workflow_simulation(self):
        """Test complete workflow simulation (no actual file upload)."""
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        try:
            provider = create_xibo_provider(config, debug=True)
            
            if not provider.authenticate():
                self.skipTest("Could not authenticate with Xibo")
            
            print("Testing complete workflow simulation...")
            
            # Test that we can find the configured display
            display_name = config['project_to']['display']['name']
            display = provider._find_display_by_name(display_name)
            
            if display:
                print(f"✅ Found configured display: {display_name}")
                
                # Test display group lookup
                display_group_id = provider._find_display_group_by_display_name(display_name)
                if display_group_id:
                    print(f"✅ Found display group ID: {display_group_id}")
                else:
                    print("⚠️  Could not find display group for display")
            else:
                print(f"⚠️  Configured display '{display_name}' not found in Xibo")
                
        except Exception as e:
            self.fail(f"Workflow simulation failed: {e}")


if __name__ == '__main__':
    # Run both mocked and live tests
    print("Xibo Provider Integration Tests")
    print("=" * 50)
    
    unittest.main(verbosity=2)
