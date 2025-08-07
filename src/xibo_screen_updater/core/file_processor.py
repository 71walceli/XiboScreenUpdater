"""
File processor module for handling NextCloud file operations.

Provides file detection, downloading, and processing coordination.
"""

import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from ..providers.nextcloud import NextCloudProvider


@dataclass
class FileInfo:
    """File information from NextCloud."""
    name: str
    path: str
    upload_date: datetime
    size: Optional[int] = None
    content_type: Optional[str] = None
    etag: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of file processing operation."""
    success: bool
    file_name: str
    error: Optional[str] = None


class FileProcessor:
    """Handles NextCloud file operations and processing."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize file processor.
        
        Args:
            config: NextCloud configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self._client: Optional[NextCloudProvider] = None
        self._temp_dir: Optional[str] = None
    
    def __enter__(self):
        """Context manager entry."""
        self._setup_temp_dir()
        self._setup_client()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self._cleanup_temp_dir()
    
    def _setup_temp_dir(self):
        """Create temporary directory for downloads."""
        self._temp_dir = tempfile.mkdtemp(prefix="xibo_upload_")
        self.logger.info(f"Created temporary directory: {self._temp_dir}")
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self.logger.info(f"Cleaned up temporary directory: {self._temp_dir}")
    
    def _setup_client(self):
        """Initialize NextCloud client."""
        self._client = NextCloudProvider(
            self.config['server'],
            self.config['auth']['user'],
            self.config['auth']['password']
        )
        self.logger.info(f"Initialized NextCloud client for {self.config['server']}")
    
    def get_new_files(self, since: datetime) -> List[FileInfo]:
        """
        Get files uploaded since the given timestamp.
        
        Args:
            since: Only return files uploaded after this time
            
        Returns:
            List of new file information
        """
        try:
            files_data = self._client.get_files(
                directory_path=self.config['path'],
                extensions=self.config['extensions']
            )
            
            new_files = []
            for file_data in files_data:
                upload_date = file_data.get('upload_date')
                if upload_date and upload_date > since:
                    file_info = FileInfo(
                        name=file_data['name'],
                        path=file_data.get('path', file_data['name']),
                        upload_date=upload_date,
                        size=file_data.get('size'),
                        content_type=file_data.get('content_type'),
                        etag=file_data.get('etag')
                    )
                    new_files.append(file_info)
            
            self.logger.info(f"Found {len(new_files)} new files since {since}")
            return new_files
            
        except Exception as e:
            self.logger.error(f"Error getting file list: {e}")
            return []
    
    def download_file(self, file_info: FileInfo) -> Optional[str]:
        """
        Download a file to temporary directory.
        
        Args:
            file_info: File information
            
        Returns:
            Local path to downloaded file, or None if failed
        """
        try:
            if not self._temp_dir:
                raise RuntimeError("Temporary directory not initialized")
            
            local_path = os.path.join(self._temp_dir, file_info.name)
            remote_path = f"{self.config['path']}/{file_info.name}"
            
            self.logger.info(f"Downloading {file_info.name}")
            downloaded_path = self._client.download_file(remote_path, local_path)
            
            if downloaded_path and os.path.exists(downloaded_path):
                self.logger.info(f"Successfully downloaded: {downloaded_path}")
                return downloaded_path
            else:
                self.logger.error(f"Download failed for {file_info.name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading {file_info.name}: {e}")
            return None
    
    def cleanup_file(self, file_path: str):
        """Clean up a downloaded file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup file {file_path}: {e}")


class ProcessingStats:
    """Track processing statistics."""
    
    def __init__(self):
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.start_time = datetime.utcnow()
    
    def add_success(self):
        """Record a successful processing."""
        self.processed += 1
        self.succeeded += 1
    
    def add_failure(self):
        """Record a failed processing."""
        self.processed += 1
        self.failed += 1
    
    def get_summary(self) -> str:
        """Get processing summary."""
        duration = datetime.utcnow() - self.start_time
        return (f"Processed {self.processed} files in {duration.total_seconds():.1f}s: "
                f"{self.succeeded} succeeded, {self.failed} failed")
