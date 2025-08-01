import os
import requests
from datetime import datetime
from time import sleep
from requests.auth import HTTPBasicAuth
from nextcloud_client import NextCloudClient
from xibo_client import create_xibo_client_from_config
import yaml

seen_files = set()

def get_nextcloud_files(config):
    """
    Get file list from NextCloud using proper WebDAV client.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        list: List of file names that match the configured extensions
    """
    server_config = config['copy_from']
    
    # Create NextCloud client
    client = NextCloudClient(
        server_config['server'],
        server_config['auth']['user'],
        server_config['auth']['password']
    )
    
    # Get file names with extension filtering
    return client.get_files(
        directory_path=server_config['path'],
        extensions=server_config['extensions']
    )

def get_nextcloud_files_detailed(config):
    """
    Get detailed file information from NextCloud using proper WebDAV client.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        list: List of dictionaries containing file information (name, size, date, etc.)
    """
    server_config = config['copy_from']
    
    # Create NextCloud client
    client = NextCloudClient(
        server_config['server'],
        server_config['auth']['user'],
        server_config['auth']['password']
    )
    
    # Get detailed file information with extension filtering
    return client.get_files(
        directory_path=server_config['path'],
        extensions=server_config['extensions']
    )

def get_new_files(config):
    """
    Get new files from NextCloud that haven't been seen before.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        list: List of new file info dictionaries
    """
    files = get_nextcloud_files_detailed(config)
    new_files = []
    
    for file_info in files:
        file_name = file_info['name']
        if file_name not in seen_files:
            seen_files.add(file_name)
            new_files.append(file_info)
    
    return new_files

def download_file(filename, config):
    """
    Download a file from NextCloud using the NextCloud client.
    
    Args:
        filename (str): Name of the file to download
        config (dict): Configuration dictionary
        
    Returns:
        str: Path to the downloaded file
    """
    server_config = config['copy_from']
    
    # Create NextCloud client
    client = NextCloudClient(
        server_config['server'],
        server_config['auth']['user'],
        server_config['auth']['password']
    )
    
    # Construct the file path on NextCloud
    file_path = f"{server_config['path']}/{filename}"
    
    # Download the file
    local_path = client.download_file(file_path, filename)
    return local_path

def upload_and_set_xibo_screen(filepath: str, config: dict, screen_name: str = None) -> bool:
    """
    Upload a file to Xibo and optionally set it as default for a specific screen.
    
    Args:
        filepath (str): Path to the file to upload
        config (dict): Configuration dictionary
        screen_name (str, optional): Name of the screen to set as default
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create Xibo client from config
        xibo_client = create_xibo_client_from_config(config, debug=True)
        
        # Authenticate
        if not xibo_client.authenticate():
            print(f"Failed to authenticate with Xibo")
            return False
        
        if screen_name:
            # Complete workflow: upload + create layout + set as default
            print(f"Uploading {filepath} and setting as default for screen '{screen_name}'")
            return xibo_client.upload_and_set_screen(filepath, screen_name)
        else:
            # Just upload the media
            print(f"Uploading {filepath} to Xibo library")
            result = xibo_client.upload_media(filepath)
            return result.get('mediaId') is not None
            
    except Exception as e:
        print(f"Error uploading to Xibo: {e}")
        return False

def load_config(file_path):
    import yaml
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    """
    Main function that monitors NextCloud for new files and uploads them to Xibo.
    """
    config = load_config("config/example.yaml")
    display_name = config['project_to']['display'].get('name')  # Use the name from config
    poll_interval = config['copy_from'].get('poll_interval', 10)  # Default to 10 seconds

    start_time = datetime.utcnow()

    if not display_name:
        print("❌ Screen name not found in config. Please check your configuration.")
        exit(1)

    print(f"Starting file monitor for screen: {display_name}")
    print(f"Monitoring NextCloud path: {config['copy_from']['path']}")
    print(f"Extensions: {config['copy_from']['extensions']}")
    print(f"Poll interval: {poll_interval} seconds")
    print("-" * 50)

    while True:
        try:
            new_files = get_new_files(config)
            if new_files:
                print(f"New files found: {[f['name'] for f in new_files]}")
                
                for file_info in new_files:
                    # Skip files modified before the script started
                    if file_info['last_modified'] <= start_time:
                        continue
                    
                    file_name = file_info['name']
                    print(f"Processing: {file_name}")
                    
                    # Download file from NextCloud
                    try:
                        downloaded_path = download_file(file_name, config)
                        if downloaded_path:
                            print(f"Downloaded: {downloaded_path}")
                            
                            # Upload to Xibo and set as default for screen
                            success = upload_and_set_xibo_screen(
                                downloaded_path, 
                                config, 
                                display_name
                            )
                            
                            if success:
                                print(f"✅ Successfully processed {file_name}")
                            else:
                                print(f"❌ Failed to upload {file_name} to Xibo")
                        else:
                            print(f"❌ Failed to download {file_name}")
                            
                    except Exception as e:
                        print(f"❌ Error processing {file_name}: {e}")
                
                print("-" * 50)
            else:
                print("No new files found")
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            
        sleep(poll_interval)

if __name__ == "__main__":
    main()
