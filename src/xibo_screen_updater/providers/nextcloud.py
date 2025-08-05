"""
NextCloud provider implementation for source file access.

This module implements the SourceProvider interface for NextCloud,
using WebDAV protocol for file operations.
"""

import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, unquote
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from .base import SourceProvider, FileInfo, registry


class NextCloudProvider(SourceProvider):
    """
    NextCloud WebDAV client implementing SourceProvider interface.
    """
    
    def __init__(self, server_url: str, username: str, password: str):
        """
        Initialize NextCloud provider.
        
        Args:
            server_url: Base URL of the NextCloud server
            username: NextCloud username
            password: NextCloud password
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)
        self.logger = logging.getLogger(__name__)
        self._connected = False
        
    def connect(self) -> bool:
        """
        Test connection to NextCloud server.
        
        Returns:
            True if connection successful
        """
        try:
            # Test connection with a simple request
            url = self._get_webdav_url("")
            response = requests.request('PROPFIND', url, auth=self.auth, timeout=10)
            self._connected = response.status_code in [200, 207]  # 207 is Multi-Status for WebDAV
            
            if self._connected:
                self.logger.info(f"Successfully connected to NextCloud server: {self.server_url}")
            else:
                self.logger.error(f"Failed to connect to NextCloud server: HTTP {response.status_code}")
                
            return self._connected
            
        except Exception as e:
            self.logger.error(f"Error connecting to NextCloud server: {e}")
            self._connected = False
            return False
        
    def _get_webdav_url(self, path: str = "") -> str:
        """
        Construct WebDAV URL for the given path.
        
        Args:
            path: Path relative to user's files
            
        Returns:
            Complete WebDAV URL
        """
        path = path.strip('/')
        return f"{self.server_url}/remote.php/dav/files/{self.username}/{path}"
    
    def get_files(self, directory_path: str = "", extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Get list of files from NextCloud directory.
        
        Args:
            directory_path: Path to the directory to list
            extensions: List of file extensions to filter by
            
        Returns:
            List of FileInfo objects
        """
        if not self._connected and not self.connect():
            return []
            
        url = self._get_webdav_url(directory_path)
        
        # WebDAV PROPFIND request to list directory contents
        headers = {
            'Depth': '1',
            'Content-Type': 'application/xml'
        }
        
        # PROPFIND body to get file properties including upload time
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
                data=propfind_body,
                timeout=30
            )
            response.raise_for_status()
            
            return self._parse_propfind_response(response.text, extensions)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error listing files: {e}")
            return []
    
    def _parse_propfind_response(self, xml_content: str, extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Parse WebDAV PROPFIND XML response to extract file information.
        
        Args:
            xml_content: XML response content
            extensions: List of file extensions to filter by
            
        Returns:
            List of FileInfo objects
        """
        files = []
        
        try:
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
                filename = unquote(href.split('/')[-1])
                
                # Skip directories and parent directory
                if href.endswith('/') or not filename:
                    continue
                
                # Check file extension
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
                
                # Create FileInfo object
                file_info = self._extract_file_info(prop, namespaces, filename, href)
                if file_info:
                    files.append(file_info)
                    
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML response: {e}")
            return []
        
        return files
    
    def _extract_file_info(self, prop, namespaces: Dict[str, str], filename: str, href: str) -> Optional[FileInfo]:
        """Extract file information from XML properties."""
        try:
            # Get file size
            size = 0
            size_elem = prop.find('d:getcontentlength', namespaces)
            if size_elem is not None:
                size = int(size_elem.text)
            
            # Get upload date (prefer upload_time, fallback to last_modified)
            upload_date = datetime.utcnow()
            
            # Try NextCloud's upload_time first
            upload_time_elem = prop.find('nc:upload_time', namespaces)
            if upload_time_elem is not None:
                try:
                    timestamp = int(upload_time_elem.text)
                    upload_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
                except (ValueError, TypeError):
                    pass
            else:
                # Fallback to last modified
                lastmod_elem = prop.find('d:getlastmodified', namespaces)
                if lastmod_elem is not None:
                    try:
                        dt = datetime.strptime(lastmod_elem.text, '%a, %d %b %Y %H:%M:%S %Z')
                        upload_date = dt.replace(tzinfo=timezone.utc).replace(tzinfo=None)
                    except ValueError:
                        pass
            
            # Get content type
            content_type = None
            type_elem = prop.find('d:getcontenttype', namespaces)
            if type_elem is not None:
                content_type = type_elem.text
            
            # Get etag
            etag = None
            etag_elem = prop.find('d:getetag', namespaces)
            if etag_elem is not None:
                etag = etag_elem.text.strip('"')
            
            return FileInfo(
                name=filename,
                path=href.replace(f'/remote.php/dav/files/{self.username}/', ''),
                size=size,
                upload_date=upload_date,
                content_type=content_type,
                etag=etag
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting file info for {filename}: {e}")
            return None
    
    def download_file(self, file_path: str, local_path: str) -> Optional[str]:
        """
        Download a file from NextCloud.
        
        Args:
            file_path: Path to the file on NextCloud
            local_path: Local path to save the file
            
        Returns:
            Local path if successful, None otherwise
        """
        if not self._connected and not self.connect():
            return None
            
        url = self._get_webdav_url(file_path)
        
        try:
            response = requests.get(url, auth=self.auth, stream=True, timeout=60)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path) if os.path.dirname(local_path) else '.', exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded: {file_path} -> {local_path}")
            return local_path
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                self.logger.error(f"Authentication failed for {file_path}: {e}")
            elif e.response.status_code == 404:
                self.logger.error(f"File not found: {file_path}")
            else:
                self.logger.error(f"HTTP error downloading {file_path}: {e}")
            return None
            
        except (OSError, IOError) as e:
            self.logger.error(f"Local file system error saving {local_path}: {e}")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error downloading {file_path}: {e}")
            return None
    
    def get_new_files_since(self, timestamp: datetime, directory_path: str = "", 
                          extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Get files uploaded since the given timestamp.
        
        Args:
            timestamp: Only return files newer than this timestamp
            directory_path: Path to search for files
            extensions: List of file extensions to filter by
            
        Returns:
            List of FileInfo objects for new files
        """
        all_files = self.get_files(directory_path, extensions)
        new_files = [f for f in all_files if f.upload_date > timestamp]
        
        if new_files:
            self.logger.info(f"Found {len(new_files)} new files since {timestamp}")
        
        return new_files


# Factory function for creating NextCloud providers from config
def create_nextcloud_provider(config: Dict[str, Any]) -> NextCloudProvider:
    """
    Create a NextCloud provider from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured NextCloudProvider instance
    """
    server_config = config.get('copy_from', {})
    
    if server_config.get('provider') != 'nextcloud':
        raise ValueError("Configuration must have copy_from.provider set to 'nextcloud'")
    
    server = server_config.get('server')
    auth = server_config.get('auth', {})
    username = auth.get('user')
    password = auth.get('password')
    
    if not all([server, username, password]):
        raise ValueError("Missing required NextCloud configuration: server, user, password")
    
    return NextCloudProvider(server, username, password)


# Register the provider
registry.register_source_provider('nextcloud', NextCloudProvider)


# Maintain backward compatibility
NextCloudClient = NextCloudProvider
