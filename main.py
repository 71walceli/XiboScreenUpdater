import os
import requests
from datetime import datetime
from time import sleep
from requests.auth import HTTPBasicAuth
from nextcloud_client import NextCloudClient

NEXTCLOUD_URL = "https://your.nextcloud.server/remote.php/dav/files/your_user/"
NEXTCLOUD_USER = "admin"
NEXTCLOUD_PASS = "admin_password"

XIBO_API_BASE = "https://your.xibo.server/api"
XIBO_CLIENT_ID = "your_client_id"
XIBO_CLIENT_SECRET = "your_client_secret"
XIBO_USER = "api_user"
XIBO_PASS = "api_password"

WATCH_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']
POLL_INTERVAL = 300  # 5 minutes

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
    files = get_nextcloud_files(config)
    new_files = [f for f in files if f not in seen_files]
    for f in new_files:
        seen_files.add(f)
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

def xibo_authenticate():
    response = requests.post(f"{XIBO_API_BASE}/authorize/access_token", data={
        "grant_type": "password",
        "client_id": XIBO_CLIENT_ID,
        "client_secret": XIBO_CLIENT_SECRET,
        "username": XIBO_USER,
        "password": XIBO_PASS
    })
    return response.json()["access_token"]

def upload_to_xibo(filepath, token):
    files = {'files[]': open(filepath, 'rb')}
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{XIBO_API_BASE}/library", files=files, headers=headers)
    return response.json()

def load_config(file_path):
    import yaml
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    config = load_config("config/example.yaml")

    while True:
        new_files = get_new_files(config)
        if new_files:
            print(f"New files found: {new_files}")
            """ 
            token = xibo_authenticate()
            for f in new_files:
                downloaded = download_file(f, config)
                if downloaded:
                    upload_to_xibo(downloaded, token)
                    # Optional: update layout/display
            """
        sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
