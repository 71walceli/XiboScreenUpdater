#!/usr/bin/env python3
"""
Test script for Xibo client functionality.
"""

import yaml
import os
from xibo_client import XiboClient, create_xibo_client_from_config

def load_config(file_path):
    """Load configuration from YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def test_xibo_connection():
    """Test basic Xibo connection and authentication."""
    try:
        print("Testing Xibo client...")
        print("-" * 50)
        
        # Load configuration
        config = load_config("config/example.yaml")
        
        # Create Xibo client
        client = create_xibo_client_from_config(config, debug=True)
        
        # Test authentication
        print("1. Testing authentication...")
        if not client.authenticate():
            print("❌ Authentication failed!")
            return False
        print("✅ Authentication successful!")
        
        # Test server info
        print("\n2. Getting server information...")
        server_info = client.get_server_info()
        if server_info:
            print(f"✅ Server info retrieved:")
            print(f"   Version: {server_info.get('version', 'Unknown')}")
            print(f"   Build: {server_info.get('build', 'Unknown')}")
        else:
            print("❌ Failed to get server info")
        
        # Test getting displays
        print("\n3. Getting displays...")
        displays = client.get_displays()
        print(f"✅ Found {len(displays)} displays:")
        for display in displays[:5]:  # Show first 5
            print(f"   - {display.get('display')} (ID: {display.get('displayId')})")
        if len(displays) > 5:
            print(f"   ... and {len(displays) - 5} more")
        
        # Test getting layouts
        print("\n4. Getting layouts...")
        layouts = client.get_layouts()
        print(f"✅ Found {len(layouts)} layouts:")
        for layout in layouts[:5]:  # Show first 5
            print(f"   - {layout.get('layout')} (ID: {layout.get('layoutId')})")
        if len(layouts) > 5:
            print(f"   ... and {len(layouts) - 5} more")
        
        # Test getting media
        print("\n5. Getting media library...")
        media_list = client.get_media_list()
        print(f"✅ Found {len(media_list)} media items:")
        for media in media_list[:5]:  # Show first 5
            print(f"   - {media.get('name')} (ID: {media.get('mediaId')}, Type: {media.get('mediaType')})")
        if len(media_list) > 5:
            print(f"   ... and {len(media_list) - 5} more")
        
        # Test getting resolutions
        print("\n6. Getting resolutions...")
        resolutions = client.list_resolutions()
        print(f"✅ Found {len(resolutions)} resolutions:")
        for resolution in resolutions:
            width = resolution.get('width', 0)
            height = resolution.get('height', 0)
            print(f"   - {width}x{height} (ID: {resolution.get('resolutionId')})")
        
        # Test getting display groups
        print("\n7. Getting display groups...")
        display_groups = client.get_display_groups()
        print(f"✅ Found {len(display_groups)} display groups:")
        for group in display_groups[:5]:  # Show first 5
            print(f"   - {group.get('displayGroup')} (ID: {group.get('displayGroupId')})")
        if len(display_groups) > 5:
            print(f"   ... and {len(display_groups) - 5} more")
        
        print("\n✅ All tests passed! Xibo client is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_workflow():
    """Test the complete workflow using the main function."""
    try:
        print("\n" + "="*60)
        print("Testing complete workflow (upload_and_set_screen)...")
        print("="*60)
        
        # Check if test image exists
        test_file = "data/Screenshot_20250326_145344.png"
        if not os.path.exists(test_file):
            print(f"❌ Test image not found: {test_file}")
            return False
        
        # Load configuration
        config = load_config("config/example.yaml")
        client = create_xibo_client_from_config(config, debug=True)
        
        # Authenticate
        if not client.authenticate():
            print("❌ Authentication failed!")
            return False
        
        # Get displays to test with
        displays = client.get_displays()
        if not displays:
            print("❌ No displays found! Please add a display to Xibo first.")
            return False
        
        # Use the first display for testing
        test_display = displays[0]
        display_name = test_display.get('display')
        print(f"Using display for test: {display_name}")
        
        # Test complete workflow (schedule for short duration for testing)
        print(f"\nTesting complete workflow...")
        success = client.upload_and_set_screen(
            file_path=test_file,
            screen_name=display_name,
            duration_hours=10000  # Short duration for testing
        )
        
        if success:
            print(f"✅ Complete workflow test successful!")
            print(f"   Media uploaded and scheduled to '{display_name}' for 1 hour")
            return True
        else:
            print("❌ Complete workflow test failed")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Xibo Client Test Suite")
    print("=" * 50)
    
    # Test basic connection
    if test_xibo_connection():
        # Test scheduling workflow if basic tests pass
        print("\n" + "="*60)
        print("Running additional workflow tests...")
        print("="*60)
        
        #test_scheduling_workflow()
        test_complete_workflow()
    else:
        print("\n❌ Basic tests failed. Please check your Xibo configuration.")
