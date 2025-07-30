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
        
        print("\n✅ All tests passed! Xibo client is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_upload_workflow():
    """Test the complete upload and screen setting workflow."""
    try:
        print("\n" + "="*60)
        print("Testing complete workflow (upload + set screen)...")
        print("="*60)
        
        # Check if test image exists
        test_file = "data/Screenshot_20250205_225547.png"
        if not os.path.exists(test_file):
            print(f"❌ Test image not found: {test_file}")
            print("   Download a test image first using the NextCloud client")
            return False
        
        # Load configuration
        config = load_config("config/example.yaml")
        client = create_xibo_client_from_config(config, debug=True)
        
        # Authenticate
        if not client.authenticate():
            print("❌ Authentication failed!")
            return False
        
        # Get available displays to test with
        displays = client.get_displays()
        if not displays:
            print("❌ No displays found! Please add a display to Xibo first.")
            return False
        
        # Use the first display for testing
        test_display = displays[0]
        display_name = test_display.get('display')
        print(f"Using display for test: {display_name}")
        
        # Test upload only (without setting screen) to avoid affecting real displays
        print(f"\nTesting media upload...")
        media_result = client.upload_media(test_file, name=f"Upload {test_file.split('/')[-1]}")
        media_id = media_result.get('files')[0].get('mediaId') if media_result.get('files') else None
        
        if media_id:
            print(f"✅ Media uploaded successfully! Media ID: {media_id}")
            
            # Test layout creation
            print(f"\nTesting layout creation...")
            layout_result = client.create_fullscreen_layout(media_id, name="Test Layout from Python Client")
            layout_id = layout_result.get('layoutId')
            
            if layout_id:
                print(f"✅ Layout created successfully! Layout ID: {layout_id}")
                print(f"\n✅ Upload workflow test completed successfully!")
                print(f"   Note: Layout was created but not set as default to avoid affecting displays.")
                print(f"   You can manually test setting it as default by calling:")
                print(f"   client.set_display_default_layout({test_display.get('displayId')}, {layout_id})")
                return True
            else:
                print("❌ Failed to create layout")
                return False
        else:
            print("❌ Failed to upload media")
            return False
            
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Xibo Client Test Suite")
    print("=" * 50)
    
    # Test basic connection
    if test_xibo_connection():
        # Test upload workflow if basic tests pass
        test_upload_workflow()
    else:
        print("\n❌ Basic tests failed. Please check your Xibo configuration.")
