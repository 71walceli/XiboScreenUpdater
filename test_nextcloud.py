#!/usr/bin/env python3
"""
Test script for NextCloud client functionality.
"""

# Simple test when running the module directly
import yaml
from nextcloud_client import NextCloudClient

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

try:
    config = load_config("config/example.yaml")
    server_config = config['copy_from']
    
    client = NextCloudClient(
        server_config['server'],
        server_config['auth']['user'],
        server_config['auth']['password']
    )
    
    print(f"Testing NextCloud connection to: {server_config['server']}")
    print(f"Directory: {server_config['path']}")
    print("-" * 50)
    
    files = client.get_files(
        directory_path=server_config['path'],
        extensions=server_config['extensions']
    )
    
    if files:
        print(f"Found {len(files)} files:")
        for file_info in files:
            print(f"  - {file_info['name']}")
            if 'size' in file_info:
                print(f"    Size: {file_info['size']} bytes")
            if 'last_modified' in file_info:
                print(f"    Modified: {file_info['last_modified']}")
            if 'content_type' in file_info:
                print(f"    Type: {file_info['content_type']}")
            print()
    else:
        print("No files found or connection failed.")
        
    latest_file = max(files, key=lambda f: f.get('last_modified', '')) if files else None
    if latest_file:
        print(f"Latest file: {latest_file['name']} (Modified: {latest_file.get('last_modified', 'Unknown')})")
        downloaded = client.download_file(latest_file['path'], f"data/{latest_file['name']}")
        if downloaded:
            print(f"Downloaded latest file to: {downloaded}")

except Exception as e:
    print(f"Error: {e}")