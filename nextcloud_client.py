import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, unquote
import os
import time
from datetime import datetime, timezone


class NextCloudClient:
    """
    NextCloud WebDAV client for listing and downloading files.
    """
    
    def __init__(self, server_url, username, password):
        """
        Initialize NextCloud client.
        
        Args:
            server_url (str): Base URL of the NextCloud server
            username (str): NextCloud username
            password (str): NextCloud password
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)
        
    def _get_webdav_url(self, path=""):
        """
        Construct WebDAV URL for the given path.
        
        Args:
            path (str): Path relative to user's files
            
        Returns:
            str: Complete WebDAV URL
        """
        path = path.strip('/')
        return f"{self.server_url}/remote.php/dav/files/{self.username}/{path}"
    
    def list_files(self, directory_path="", extensions=None):
        """
        List files in a NextCloud directory using WebDAV PROPFIND.
        
        Args:
            directory_path (str): Path to the directory to list
            extensions (list): List of file extensions to filter by (e.g., ['.jpg', '.png'])
            
        Returns:
            list: List of dictionaries containing file information
        """
        url = self._get_webdav_url(directory_path)
        
        # WebDAV PROPFIND request to list directory contents
        headers = {
            'Depth': '1',
            'Content-Type': 'application/xml'
        }
        
        # Basic PROPFIND body to get file properties including upload time
        propfind_body = '''<?xml version="1.0"?>
        <d:propfind xmlns:d="DAV:" xmlns:nc="http://nextcloud.org/ns">
            <d:prop>
                <d:getlastmodified/>
                <d:getcontentlength/>
                <d:resourcetype/>
                <d:getetag/>
                <d:getcontenttype/>
                <d:creationdate/>
                <nc:creation_time/>
                <nc:upload_time/>
            </d:prop>
        </d:propfind>'''
        
        try:
            response = requests.request(
                'PROPFIND',
                url,
                auth=self.auth,
                headers=headers,
                data=propfind_body
            )
            response.raise_for_status()
            
            return self._parse_propfind_response(response.text, extensions)
            
        except requests.exceptions.RequestException as e:
            print(f"Error listing files: {e}")
            return []
    
    def _parse_propfind_response(self, xml_content, extensions=None):
        """
        Parse WebDAV PROPFIND XML response to extract file information.
        
        Args:
            xml_content (str): XML response content
            extensions (list): List of file extensions to filter by
            
        Returns:
            list: List of dictionaries containing file information
        """
        files = []
        
        try:
            # Parse XML with namespace handling
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            namespaces = {
                'd': 'DAV:',
                's': 'http://sabredav.org/ns',
                'oc': 'http://owncloud.org/ns',
                'nc': 'http://nextcloud.org/ns'
            }
            
            # Find all response elements
            for response in root.findall('.//d:response', namespaces):
                href_elem = response.find('d:href', namespaces)
                if href_elem is None:
                    continue
                    
                href = href_elem.text
                
                # Extract filename from href
                filename = unquote(href.split('/')[-1])
                
                # Skip if it's a directory (ends with /) or the parent directory
                if href.endswith('/') or not filename:
                    continue
                
                # Check if file has required extension
                if extensions:
                    if not any(filename.lower().endswith(ext.lower()) for ext in extensions):
                        continue
                
                # Extract file properties
                propstat = response.find('d:propstat', namespaces)
                if propstat is None:
                    continue
                    
                prop = propstat.find('d:prop', namespaces)
                if prop is None:
                    continue
                
                # Get file properties
                file_info = {
                    'name': filename,
                    'href': href,
                    'path': href.replace(f'/remote.php/dav/files/{self.username}/', ''),
                }
                
                # Get last modified date
                lastmod_elem = prop.find('d:getlastmodified', namespaces)
                if lastmod_elem is not None:
                    try:
                        # Parse and convert to UTC timezone-naive
                        dt = datetime.strptime(lastmod_elem.text, '%a, %d %b %Y %H:%M:%S %Z')
                        file_info['last_modified'] = dt.replace(tzinfo=timezone.utc).replace(tzinfo=None)
                    except ValueError:
                        # Fallback if the date format is different
                        file_info['last_modified_raw'] = lastmod_elem.text
                
                # Get creation date (convert to UTC timezone-naive)
                creation_elem = prop.find('d:creationdate', namespaces)
                if creation_elem is not None:
                    try:
                        # Parse ISO 8601 format with timezone
                        creation_date_str = creation_elem.text
                        # Handle different ISO 8601 formats
                        if '+' in creation_date_str or creation_date_str.endswith('Z'):
                            dt = datetime.fromisoformat(creation_date_str.replace('Z', '+00:00'))
                        else:
                            dt = datetime.fromisoformat(creation_date_str)
                        # Convert to UTC and make timezone-naive
                        if dt.tzinfo is not None:
                            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                        file_info['creation_date'] = dt
                    except (ValueError, AttributeError):
                        file_info['creation_date_raw'] = creation_elem.text
                
                # Get creation time as timestamp
                creation_time_elem = prop.find('nc:creation_time', namespaces)
                if creation_time_elem is not None:
                    try:
                        timestamp = int(creation_time_elem.text)
                        # Create UTC timezone-naive datetime
                        file_info['creation_time'] = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
                    except (ValueError, TypeError):
                        file_info['creation_time_raw'] = creation_time_elem.text
                
                # Get upload time as timestamp (this is what we need!)
                upload_time_elem = prop.find('nc:upload_time', namespaces)
                if upload_time_elem is not None:
                    try:
                        timestamp = int(upload_time_elem.text)
                        # Create UTC timezone-naive datetime
                        file_info['upload_date'] = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
                    except (ValueError, TypeError):
                        file_info['upload_date_raw'] = upload_time_elem.text
                
                # Get content length (file size)
                size_elem = prop.find('d:getcontentlength', namespaces)
                if size_elem is not None:
                    file_info['size'] = int(size_elem.text)
                
                # Get content type
                type_elem = prop.find('d:getcontenttype', namespaces)
                if type_elem is not None:
                    file_info['content_type'] = type_elem.text
                
                # Get etag
                etag_elem = prop.find('d:getetag', namespaces)
                if etag_elem is not None:
                    file_info['etag'] = etag_elem.text.strip('"')
                
                files.append(file_info)
                
        except ET.ParseError as e:
            print(f"Error parsing XML response: {e}")
            return []
        
        return files
    
    def download_file(self, file_path, local_path=None):
        """
        Download a file from NextCloud.
        
        Args:
            file_path (str): Path to the file on NextCloud (relative to user's files)
            local_path (str): Local path to save the file (optional, defaults to filename)
            
        Returns:
            str: Path to the downloaded file, or None if failed
        """
        url = self._get_webdav_url(file_path)
        
        if local_path is None:
            local_path = os.path.basename(file_path)
        
        try:
            response = requests.get(url, auth=self.auth, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path) if os.path.dirname(local_path) else '.', exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {file_path} -> {local_path}")
            return local_path
            
        except requests.exceptions.HTTPError as e:
            # Re-raise HTTP errors (auth failures, not found, etc.)
            if e.response.status_code in [401, 403]:
                raise Exception(f"Authentication failed for {file_path}: {e}")
            elif e.response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_path}")
            else:
                raise Exception(f"HTTP error downloading {file_path}: {e}")
        except (OSError, IOError, PermissionError) as e:
            # Re-raise local file system errors (permissions, disk space, etc.)
            raise Exception(f"Local file system error saving {local_path}: {e}")
        except requests.exceptions.RequestException as e:
            # For connection errors, retry a few times before giving up
            if hasattr(self, '_download_retry_count'):
                self._download_retry_count += 1
            else:
                self._download_retry_count = 1
            
            max_retries = 3
            if self._download_retry_count <= max_retries:
                print(f"Network error downloading file {file_path} (attempt {self._download_retry_count}/{max_retries}): {e}")
                time.sleep(2 ** self._download_retry_count)  # Exponential backoff
                return self.download_file(file_path, local_path)
            else:
                # Reset retry counter and re-raise after max attempts
                self._download_retry_count = 0
                raise Exception(f"Network error downloading {file_path} after {max_retries} attempts: {e}")
    
    def get_files(self, directory_path="", extensions=None):
        """
        Get detailed file information in a directory.
        
        Args:
            directory_path (str): Path to the directory to list
            extensions (list): List of file extensions to filter by
            
        Returns:
            list: List of dictionaries containing file information (name, size, date, etc.)
        """
        return self.list_files(directory_path, extensions)
    
    def get_file_names(self, directory_path="", extensions=None):
        """
        Get a simple list of file names in a directory.
        
        Args:
            directory_path (str): Path to the directory to list
            extensions (list): List of file extensions to filter by
            
        Returns:
            list: List of file names
        """
        files = self.list_files(directory_path, extensions)
        return [file_info['name'] for file_info in files]


if __name__ == "__main__":
    # Simple test when running the module directly
    import yaml
    
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
                if 'upload_date' in file_info:
                    print(f"    Uploaded: {file_info['upload_date']}")
                if 'creation_date' in file_info:
                    print(f"    Created: {file_info['creation_date']}")
                if 'content_type' in file_info:
                    print(f"    Type: {file_info['content_type']}")
                print()
        else:
            print("No files found or connection failed.")
            
    except Exception as e:
        print(f"Error: {e}")
