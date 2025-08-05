"""
Xibo Screen Updater - Automated NextCloud to Xibo CMS sync tool.

This package provides tools for monitoring NextCloud directories and automatically
uploading new files to Xibo CMS displays.
"""

__version__ = "2.0.0"
__author__ = "XiboScreenUpdater Team"

from .core.application import XiboScreenUpdater
from .core.config_manager import ConfigManager, ConfigurationError
from .providers.nextcloud import NextCloudClient
from .providers.xibo import XiboClient

__all__ = [
    "XiboScreenUpdater",
    "ConfigManager", 
    "ConfigurationError",
    "NextCloudClient",
    "XiboClient",
]
