import requests
import os
import time
from urllib.parse import urljoin
from typing import Optional, Dict, Any, List
import json


class XiboClient:
    """
    Xibo CMS client for managing screens, layouts, and media using OAuth2 authentication.
    
    This client supports the workflow:
    1. Upload media files to the library
    2. Create layouts with the uploaded media
    3. Set layouts as default for displays/screens
    """
    
    def __init__(self, server_url: str, client_id: str, client_secret: str, debug: bool = False):
        """
        Initialize Xibo client with OAuth2 credentials.
        
        Args:
            server_url (str): Base URL of the Xibo CMS server
            client_id (str): OAuth2 client ID
            client_secret (str): OAuth2 client secret
            debug (bool): Enable debug logging
        """
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.debug = debug
        self.access_token = None
        self.token_expires_at = 0
        
    def _log(self, message: str):
        """Log debug messages if debug is enabled."""
        if self.debug:
            print(f"[XiboClient] {message}")
            
    def _get_api_url(self, endpoint: str) -> str:
        """
        Construct API URL for the given endpoint.
        
        Args:
            endpoint (str): API endpoint path
            
        Returns:
            str: Complete API URL
        """
        endpoint = endpoint.lstrip('/')
        return f"{self.server_url}/{endpoint}"
    
    def authenticate(self) -> bool:
        """
        Authenticate with Xibo CMS using OAuth2 client credentials grant.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        url = self._get_api_url("authorize/access_token")
        
        # Try form-encoded data for OAuth2
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            self._log(f"Authenticating with Xibo server at {url}")
            self._log(f"Using client_id: {self.client_id[:8]}...")
            response = requests.post(url, data=data, headers=headers)
            
            self._log(f"Response status: {response.status_code}")
            self._log(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
            self.token_expires_at = time.time() + expires_in - 60  # Refresh 1 minute early
            
            self._log(f"Authentication successful. Token expires in {expires_in} seconds")
            return True
            
        except requests.exceptions.RequestException as e:
            self._log(f"Authentication failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self._log(f"Response: {e.response.text}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            bool: True if we have a valid token, False otherwise
        """
        if not self.access_token or time.time() >= self.token_expires_at:
            self._log("Token expired or missing, re-authenticating...")
            return self.authenticate()
        return True
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request to the Xibo API.
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            requests.Response: The response object
            
        Raises:
            Exception: If authentication fails or request fails
        """
        if not self._ensure_authenticated():
            raise Exception("Failed to authenticate with Xibo CMS")
        
        url = self._get_api_url(endpoint)
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        self._log(f"{method} {url}")
        if self.debug and 'data' in kwargs:
            self._log(f"Data: {kwargs['data']}")
        
        response = requests.request(method, url, **kwargs)
        
        if self.debug:
            self._log(f"Response status: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    self._log(f"Response JSON: {response.json()}")
                except:
                    pass
        
        response.raise_for_status()
        return response
    
    def upload_media(self, file_path: str, name: Optional[str] = None, tags: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a media file to the Xibo library.
        
        Args:
            file_path (str): Path to the file to upload
            name (str, optional): Custom name for the media. Defaults to filename
            tags (str, optional): Comma-separated tags for the media
            
        Returns:
            dict: Response data containing media information
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            Exception: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        media_name = name or os.path.splitext(filename)[0]
        
        self._log(f"Uploading media file: {file_path} as '{media_name}'")
        
        with open(file_path, 'rb') as f:
            files = {'files': (filename, f, 'application/octet-stream')}
            data = {'name': media_name}
            
            if tags:
                data['tags'] = tags
            
            response = self._make_request('POST', 'library', files=files, data=data)
            
        result = response.json()
        self._log(f"Media uploaded successfully. Media ID: {result.get('mediaId')}")
        return result
    
    def get_media_list(self, media_name: Optional[str] = None, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of media from the library.
        
        Args:
            media_name (str, optional): Filter by media name
            media_type (str, optional): Filter by media type
            
        Returns:
            list: List of media objects
        """
        params = {}
        if media_name:
            params['media'] = media_name
        if media_type:
            params['type'] = media_type
        
        response = self._make_request('GET', 'library', params=params)
        return response.json()
    
    def create_layout(self, name: str, description: Optional[str] = None, resolution_id: int = 9) -> Dict[str, Any]:
        """
        Create a new layout.
        
        Args:
            name (str): Layout name
            description (str, optional): Layout description
            resolution_id (int): Resolution ID (default: 9 for 1920x1080)
            
        Returns:
            dict: Layout information
        """
        self._log(f"Creating layout: {name}")
        
        data = {
            'name': name,
            'resolutionId': resolution_id
        }
        
        if description:
            data['description'] = description
        
        response = self._make_request('POST', 'layout', data=data)
        result = response.json()
        
        self._log(f"Layout created successfully. Layout ID: {result.get('layoutId')}")
        return result
    
    def create_fullscreen_layout(self, media_id: int, name: Optional[str] = None, 
            resolution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a fullscreen layout with a single media item.
        
        Args:
            media_id (int): ID of the media to display
            name (str, optional): Layout name. If not provided, will use media name
            resolution_id (int, optional): Resolution ID
            
        Returns:
            dict: Layout information
        """
        self._log(f"Creating fullscreen layout for media ID: {media_id}")
        
        data = {
            'id': media_id,
            'type': 'media'
        }
        
        if name:
            data['name'] = name
        if resolution_id:
            data['resolutionId'] = resolution_id
        
        response = self._make_request('POST', 'layout/fullscreen', data=data)
        result = response.json()
        
        self._log(f"Fullscreen layout created successfully. Layout ID: {result.get('layoutId')}")
        return result
    
    def get_layouts(self, layout_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of layouts.
        
        Args:
            layout_name (str, optional): Filter by layout name
            
        Returns:
            list: List of layout objects
        """
        params = {}
        if layout_name:
            params['layout'] = layout_name
        
        response = self._make_request('GET', 'layout', params=params)
        return response.json()
    
    def get_displays(self, display_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of displays/screens.
        
        Args:
            display_name (str, optional): Filter by display name
            
        Returns:
            list: List of display objects
        """
        params = {}
        if display_name:
            params['display'] = display_name
        
        response = self._make_request('GET', 'display', params=params)
        return response.json()
    
    def set_display_default_layout(self, display_id: int, layout_id: int) -> bool:
        """
        Set the default layout for a display.
        
        Args:
            display_id (int): ID of the display
            layout_id (int): ID of the layout to set as default
            
        Returns:
            bool: True if successful, False otherwise
        """
        self._log(f"Setting layout {layout_id} as default for display {display_id}")
        
        try:
            data = {'layoutId': layout_id}
            self._make_request('PUT', f'display/defaultlayout/{display_id}', data=data)
            self._log("Default layout set successfully")
            return True
        except Exception as e:
            self._log(f"Failed to set default layout: {e}")
            return False
    
    def find_display_by_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a display by name.
        
        Args:
            display_name (str): Name of the display to find
            
        Returns:
            dict or None: Display object if found, None otherwise
        """
        displays = self.get_displays(display_name)
        for display in displays:
            if display.get('display', '').lower() == display_name.lower():
                return display
        return None
    
    def find_layout_by_name(self, layout_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a layout by name.
        
        Args:
            layout_name (str): Name of the layout to find
            
        Returns:
            dict or None: Layout object if found, None otherwise
        """
        layouts = self.get_layouts(layout_name)
        for layout in layouts:
            if layout.get('layout', '').lower() == layout_name.lower():
                return layout
        return None
    
    def upload_and_set_screen(self, file_path: str, screen_name: str, 
                             layout_name: Optional[str] = None) -> bool:
        """
        Complete workflow: upload media, create layout, and set as default for screen.
        
        Args:
            file_path (str): Path to the media file to upload
            screen_name (str): Name of the screen/display to update
            layout_name (str, optional): Name for the layout. Defaults to filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Step 1: Upload media
            self._log(f"Starting workflow for file: {file_path}, screen: {screen_name}")
            media_result = self.upload_media(file_path)
            media_id = media_result.get('mediaId')
            
            if not media_id:
                self._log("Failed to get media ID from upload response")
                return False
            
            # Step 2: Create fullscreen layout
            filename = os.path.splitext(os.path.basename(file_path))[0]
            layout_title = layout_name or f"Layout for {filename}"
            
            layout_result = self.create_fullscreen_layout(media_id, layout_title)
            layout_id = layout_result.get('layoutId')
            
            if not layout_id:
                self._log("Failed to get layout ID from create response")
                return False
            
            # Step 3: Find display by name
            display = self.find_display_by_name(screen_name)
            if not display:
                self._log(f"Display '{screen_name}' not found")
                return False
            
            display_id = display.get('displayId')
            if not display_id:
                self._log("Failed to get display ID")
                return False
            
            # Step 4: Set as default layout
            success = self.set_display_default_layout(display_id, layout_id)
            
            if success:
                self._log(f"Workflow completed successfully!")
                self._log(f"  - Media ID: {media_id}")
                self._log(f"  - Layout ID: {layout_id}")
                self._log(f"  - Display ID: {display_id}")
            
            return success
            
        except Exception as e:
            self._log(f"Workflow failed: {e}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information and test connectivity.
        
        Returns:
            dict: Server information
        """
        try:
            response = self._make_request('GET', 'about')
            return response.json()
        except Exception as e:
            self._log(f"Failed to get server info: {e}")
            return {}
    
    def list_resolutions(self) -> List[Dict[str, Any]]:
        """
        Get list of available resolutions.
        
        Returns:
            list: List of resolution objects
        """
        try:
            response = self._make_request('GET', 'resolution')
            return response.json()
        except Exception as e:
            self._log(f"Failed to get resolutions: {e}")
            return []


def create_xibo_client_from_config(config: Dict[str, Any], debug: bool = False) -> XiboClient:
    """
    Create a XiboClient instance from configuration.
    
    Args:
        config (dict): Configuration dictionary with project_to section
        debug (bool): Enable debug logging
        
    Returns:
        XiboClient: Configured client instance
    """
    xibo_config = config.get('project_to', {})
    
    if xibo_config.get('provider') != 'xibo':
        raise ValueError("Configuration must have project_to.provider set to 'xibo'")
    
    host = xibo_config.get('host')
    auth = xibo_config.get('auth', {})
    client_id = auth.get('client_id')
    client_secret = auth.get('client_secret')
    
    if not all([host, client_id, client_secret]):
        raise ValueError("Missing required Xibo configuration: host, client_id, client_secret")
    
    return XiboClient(host, client_id, client_secret, debug=debug)
