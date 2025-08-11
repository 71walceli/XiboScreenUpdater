from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FileInfo:
    """Information about a file from a source provider."""
    name: str
    path: str
    upload_date: datetime
    size: int
    content_type: Optional[str] = None
    etag: Optional[str] = None
    
    def __str__(self):
        return f"FileInfo(name='{self.name}', size={self.size}, upload_date={self.upload_date})"
