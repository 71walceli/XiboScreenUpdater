"""
Xibo provider implementation for destination display management.

This module implements the DestinationProvider interface for Xibo CMS,
using OAuth2 authentication and REST API for media management.
"""

import requests
import os
import time
from urllib.parse import urljoin
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta
import logging

from .base import DestinationProvider, registry

# TODO Handle these through configuration
auto_scheduled_prefix = "Auto-scheduled"
auto_layout_prefix = "Auto-layout"

class XiboProvider(DestinationProvider):
    """
    Xibo CMS client implementing DestinationProvider interface.
    
    This client supports the workflow:
    1. Upload media files to the library
    2. Create layouts with the uploaded media
    3. Schedule layouts to displays/display groups
    """
    
    def __init__(self, server_url: str, client_id: str, client_secret: str, debug: bool = False):
        """
        Initialize Xibo provider with OAuth2 credentials.
        
        Args:
            server_url: Base URL of the Xibo CMS server
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            debug: Enable debug logging
        """
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.debug = debug
        self.access_token = None
        self.token_expires_at = 0
        self.logger = logging.getLogger(__name__)
        
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
    def _log(self, message: str, level: str = 'info'):
        """Log messages with appropriate level."""
        if level == 'debug' and not self.debug:
            return
            
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[XiboProvider] {message}")
            
    def _get_api_url(self, endpoint: str) -> str:
        """
        Construct API URL for the given endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Complete API URL
        """
        endpoint = endpoint.lstrip('/')
        return f"{self.server_url}/{endpoint}"
    
    def authenticate(self) -> bool:
        """
        Authenticate with Xibo CMS using OAuth2 client credentials grant.
        
        Returns:
            True if authentication successful, False otherwise
        """
        url = self._get_api_url("authorize/access_token")
        
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
            self._log(f"Using client_id: {self.client_id[:8]}...", 'debug')
            
            response = requests.post(url, data=data, headers=headers, timeout=30)
            
            self._log(f"Response status: {response.status_code}", 'debug')
            
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
                self._log(f"Response: {e.response.text}", 'debug')
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            True if we have a valid token, False otherwise
        """
        if not self.access_token or time.time() >= self.token_expires_at:
            self._log("Token expired or missing, re-authenticating...")
            return self.authenticate()
        return True
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request to the Xibo API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
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
        
        self._log(f"{method} {url}", 'debug')
        if self.debug and 'data' in kwargs:
            self._log(f"Data: {kwargs['data']}", 'debug')
        
        response = requests.request(method, url, timeout=60, **kwargs)
        
        if self.debug:
            self._log(f"Response status: {response.status_code}", 'debug')
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    self._log(f"Response JSON: {response.json()}", 'debug')
                except:
                    pass
        
        response.raise_for_status()
        return response
    
    def upload_media(self, file_path: str, name: Optional[str] = None, 
                    tags: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Upload a media file to the Xibo library.
        
        Args:
            file_path: Path to the file to upload
            name: Custom name for the media. Defaults to filename
            tags: Comma-separated tags for the media
            
        Returns:
            Media information dict if successful, None otherwise
        """
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return None
        
        filename = os.path.basename(file_path)
        media_name = name or os.path.splitext(filename)[0]
        
        self._log(f"Uploading media file: {file_path} as '{media_name}'")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'files': (filename, f, 'application/octet-stream')}
                data = {'name': media_name}
                
                if tags:
                    data['tags'] = tags
                
                response = self._make_request('POST', 'library', files=files, data=data)
                
            result = response.json()
            
            # Handle different response formats
            if 'files' in result and len(result['files']) > 0:
                media_info = result['files'][0]
                self._log(f"Media uploaded successfully. Media ID: {media_info.get('mediaId')}")
                return media_info
            else:
                self.logger.error("Unexpected response format from media upload")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading media {file_path}: {e}")
            return None
    
    def set_display_content(self, media_id: str, display_name: str, 
            duration_hours: int = 24
        ) -> bool:
        """
        Set media as content for a specific display.
        
        Args:
            media_id: ID of the uploaded media
            display_name: Name of the target display
            duration_hours: How long to display the content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find display group for the screen
            display_group_id = self._find_display_group_by_display_name(display_name)
            if not display_group_id:
                self.logger.error(f"Could not find display group for screen '{display_name}'")
                return False
            
            # Create a fullscreen layout for the media
            layout_name = f"{auto_layout_prefix}: {display_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            fullscreen_layout = self._create_fullscreen_layout(int(media_id), name=layout_name)
            
            if not fullscreen_layout:
                return False
            
            campaign_id = fullscreen_layout.get('campaignId')
            if not campaign_id:
                self.logger.error("Failed to get campaign ID from layout")
                return False
            
            # Schedule the media
            schedule_result = self._schedule_media_relative(
                media_id=campaign_id,
                display_group_ids=[display_group_id],
                hours_from_now=0,  # Start now
                duration_hours=duration_hours,
                name=f"{auto_scheduled_prefix}: {display_name}",
                is_priority=True
            )
            
            event_id = schedule_result.get('eventId')
            if not event_id:
                self.logger.error("Failed to get event ID from schedule response")
                return False
            
            # Delete other auto-scheduled events to avoid conflicts
            deleted_count = self._delete_auto_scheduled_events(display_group_id, exclude_event_id=event_id)
            self.logger.info(f"Deleted {deleted_count} old auto-scheduled events for display group {display_group_id}")

            # Refresh display to apply changes
            self._force_refresh_display(display_group_id)
            
            self._log(f"Successfully set content for display '{display_name}'")
            self._log(f"  - Media ID: {media_id}")
            self._log(f"  - Campaign ID: {campaign_id}")
            self._log(f"  - Event ID: {event_id}")
            self._log(f"  - Duration: {duration_hours} hours")
            self._log(f"  - Deleted {deleted_count} old events")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting display content: {e}")
            return False
    
    def get_displays(self) -> List[Dict[str, Any]]:
        """
        Get list of available displays.
        
        Returns:
            List of display information dictionaries
        """
        try:
            response = self._make_request('GET', 'display')
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting displays: {e}")
            return []
    
    def _create_fullscreen_layout(self, media_id: int, name: Optional[str] = None, 
            resolution_id: Optional[int] = None
        ) -> Optional[Dict[str, Any]]:
        """Create a fullscreen layout with a single media item."""
        self._log(f"Creating fullscreen layout for media ID: {media_id}")
        
        try:
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
            
        except Exception as e:
            self.logger.error(f"Error creating fullscreen layout: {e}")
            return None
    
    def _find_display_group_by_display_name(self, display_name: str) -> Optional[int]:
        """Find display group ID for a specific display name."""
        display = self.find_display_by_name(display_name)
        if display:
            display_group_id = display.get('displayGroupId')
            if display_group_id:
                return display_group_id
            
            # If not in display info, try to find by display ID
            display_id = display.get('displayId')
            if display_id:
                display_groups = self._get_display_groups()
                for group in display_groups:
                    if display_id in group.get('displays', []):
                        return group.get('displayGroupId')
        
        return None
    
    def find_display_by_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """Find a display by name."""
        displays = self.get_displays()
        for display in displays:
            if display.get('display', '').lower() == display_name.lower():
                return display
        return None
    
    def _get_display_groups(self) -> List[Dict[str, Any]]:
        """Get list of display groups."""
        try:
            response = self._make_request('GET', 'displaygroup')
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting display groups: {e}")
            return []
    
    def _schedule_media_relative(self, media_id: int, display_group_ids: List[int],
                               hours_from_now: int = 0, duration_hours: int = 24,
                               name: Optional[str] = None, is_priority: bool = False) -> Dict[str, Any]:
        """Schedule a media item with relative timing."""
        start_time = datetime.now() + timedelta(hours=hours_from_now)
        end_time = start_time + timedelta(hours=duration_hours)
        
        from_dt = start_time.strftime('%Y-%m-%d %H:%M:%S')
        to_dt = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        self._log(f"Scheduling media {media_id} from {from_dt} to {to_dt}")
        
        return self._schedule_media(media_id, display_group_ids, from_dt, to_dt, name, is_priority=is_priority)
    
    def _schedule_media(self, media_id: int, display_group_ids: List[int], 
                       from_dt: str, to_dt: str, name: Optional[str] = None,
                       day_part_id: int = 1, is_priority: bool = False) -> Dict[str, Any]:
        """Schedule a media item to display groups."""
        self._log(f"Scheduling media {media_id} to display groups {display_group_ids}")
        
        try:
            data = {
                'name': name or '',
                'eventTypeId': 7,  # Schedule full screen media content
                'fromDt': from_dt,
                'toDt': to_dt,
                'fullScreenCampaignId': media_id,
                'displayOrder': 0,
                'isPriority': 1 if is_priority else '',
                'dayPartId': day_part_id,
            }
            
            # Add display group IDs
            for i, group_id in enumerate(display_group_ids):
                data[f'displayGroupIds[{i}]'] = group_id
            
            response = self._make_request('POST', 'schedule', data=data)
            result = response.json()
            
            self._log(f"Media scheduled successfully. Event ID: {result.get('eventId')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error scheduling media: {e}")
            return {}
    
    def _delete_auto_scheduled_events(self, display_group_id: int, exclude_event_id: Optional[int] = None) -> int:
        """Delete all auto-scheduled events for a display group."""
        try:
            events = self.get_events(display_group_id)
            deleted_count = 0
            
            for event in events:
                event_id = event.get('eventId')
                event_name = event.get('name', '')

                # Skip the current event
                if exclude_event_id and event_id == exclude_event_id:
                    continue
                
                # Delete events that start with "Auto-scheduled:"
                if event_name.startswith(f"{auto_scheduled_prefix}:"):
                    if self._delete_schedule_event(event_id):
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting auto-scheduled events: {e}")
            return 0
    
    def get_events(self, display_group_id: Optional[int]) -> List[Dict[str, Any]]:
        """
        Get all scheduled events for a display group.
        
        Args:
            display_group_id: ID of the display group
            
        Returns:
            List of event dictionaries
        """
        try:
            if not display_group_id:
                display_group_id = ""
            data = {'displayId': display_group_id}
            response = self._make_request('GET', f'schedule', params=data)
            result = response.json()
            return result
        except Exception as e:
            self.logger.error(f"Error getting events for display group {display_group_id}: {e}")
            return []

    def _delete_schedule_event(self, event_id: int) -> bool:
        """Delete a scheduled event."""
        try:
            self._make_request('DELETE', f'schedule/{event_id}')
            self._log(f"Deleted schedule event {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting schedule event {event_id}: {e}")
            return False
    
    def _force_refresh_display(self, display_id: int) -> bool:
        """Force refresh a display to apply changes immediately."""
        try:
            self._make_request('POST', f'display/{display_id}/action/collectNow')
            self._log(f"Display {display_id} refreshed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing display {display_id}: {e}")
            return False


# Factory function for creating Xibo providers from config
def create_xibo_provider(config: Dict[str, Any], debug: bool = False) -> XiboProvider:
    """
    Create a Xibo provider from configuration.
    
    Args:
        config: Configuration dictionary with project_to section
        debug: Enable debug logging
        
    Returns:
        Configured XiboProvider instance
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
    
    return XiboProvider(host, client_id, client_secret, debug=debug)


# Register the provider
registry.register_destination_provider('xibo', XiboProvider)


# Maintain backward compatibility
XiboClient = XiboProvider
create_xibo_client_from_config = create_xibo_provider
