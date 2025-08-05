"""
Provider abstraction for source and destination services.

This module defines the abstract base classes that all providers must implement,
enabling pluggable architecture for different source and destination services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a file from a source provider."""
    name: str
    path: str
    size: int
    upload_date: datetime
    content_type: Optional[str] = None
    etag: Optional[str] = None
    
    def __str__(self):
        return f"FileInfo(name='{self.name}', size={self.size}, upload_date={self.upload_date})"


class SourceProvider(ABC):
    """Abstract base class for source providers (e.g., NextCloud, FTP, etc.)."""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the source service.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_files(self, directory_path: str = "", extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Get list of files from the source.
        
        Args:
            directory_path: Path to search for files
            extensions: List of file extensions to filter by
            
        Returns:
            List of FileInfo objects
        """
        pass
    
    @abstractmethod
    def download_file(self, file_path: str, local_path: str) -> Optional[str]:
        """
        Download a file from the source.
        
        Args:
            file_path: Remote path of the file
            local_path: Local path to save the file
            
        Returns:
            Local path of downloaded file if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_new_files_since(self, timestamp: datetime, directory_path: str = "", 
                          extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Get files that have been uploaded since the given timestamp.
        
        Args:
            timestamp: Only return files newer than this timestamp
            directory_path: Path to search for files
            extensions: List of file extensions to filter by
            
        Returns:
            List of FileInfo objects for new files
        """
        pass


class DestinationProvider(ABC):
    """Abstract base class for destination providers (e.g., Xibo, other CMS)."""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the destination service.
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def upload_media(self, file_path: str, name: Optional[str] = None, 
                    tags: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Upload a media file to the destination.
        
        Args:
            file_path: Local path of the file to upload
            name: Custom name for the media
            tags: Tags to associate with the media
            
        Returns:
            Media information dict if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def set_display_content(self, media_id: str, display_name: str, 
                          duration_hours: int = 24) -> bool:
        """
        Set media as content for a specific display.
        
        Args:
            media_id: ID of the uploaded media
            display_name: Name of the target display
            duration_hours: How long to display the content
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_displays(self) -> List[Dict[str, Any]]:
        """
        Get list of available displays.
        
        Returns:
            List of display information dictionaries
        """
        pass


class MediaProcessor(ABC):
    """Abstract base class for media processing (transformations, etc.)."""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """
        Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if processor can handle this file type
        """
        pass
    
    @abstractmethod
    def process(self, input_path: str, output_path: str) -> bool:
        """
        Process the media file (transform, convert, etc.).
        
        Args:
            input_path: Path to input file
            output_path: Path for processed output file
            
        Returns:
            True if processing successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions this processor supports.
        
        Returns:
            List of supported file extensions (e.g., ['.pdf', '.doc'])
        """
        pass


# Registry for dynamic provider loading
class ProviderRegistry:
    """Registry for managing provider implementations."""
    
    def __init__(self):
        self._source_providers = {}
        self._destination_providers = {}
        self._media_processors = {}
    
    def register_source_provider(self, name: str, provider_class: type):
        """Register a source provider implementation."""
        self._source_providers[name] = provider_class
    
    def register_destination_provider(self, name: str, provider_class: type):
        """Register a destination provider implementation."""
        self._destination_providers[name] = provider_class
    
    def register_media_processor(self, name: str, processor_class: type):
        """Register a media processor implementation."""
        self._media_processors[name] = processor_class
    
    def get_source_provider(self, name: str) -> Optional[type]:
        """Get a source provider class by name."""
        return self._source_providers.get(name)
    
    def get_destination_provider(self, name: str) -> Optional[type]:
        """Get a destination provider class by name."""
        return self._destination_providers.get(name)
    
    def get_media_processor(self, name: str) -> Optional[type]:
        """Get a media processor class by name."""
        return self._media_processors.get(name)
    
    def list_source_providers(self) -> List[str]:
        """List all registered source provider names."""
        return list(self._source_providers.keys())
    
    def list_destination_providers(self) -> List[str]:
        """List all registered destination provider names."""
        return list(self._destination_providers.keys())
    
    def list_media_processors(self) -> List[str]:
        """List all registered media processor names."""
        return list(self._media_processors.keys())


# Global registry instance
registry = ProviderRegistry()
