"""
Main application class for Xibo Screen Updater.

This module contains the core application logic that orchestrates
the monitoring, processing, and uploading workflow.
"""

import sys
import argparse
from datetime import datetime
from time import sleep

from .config_manager import ConfigManager, ConfigurationError, resolve_config_path
from .file_processor import ProcessingStats
from .logging_config import setup_logging, get_component_logger, LogContext
from ..providers.xibo import create_xibo_provider
from ..providers.nextcloud import create_nextcloud_provider


class XiboScreenUpdater:
    """Main application class for Xibo Screen Updater."""
    
    def __init__(self, config_path: str):
        """
        Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config_manager = ConfigManager()
        self.logger = setup_logging()
        self.latest_upload_date = datetime.utcnow()
        
        # Providers will be initialized during setup
        self.nextcloud_provider = None
        self.xibo_provider = None
        
        # Get component loggers
        self.nextcloud_logger = get_component_logger('nextcloud', self.logger)
        self.xibo_logger = get_component_logger('xibo', self.logger)
        self.processor_logger = get_component_logger('processor', self.logger)
    
    def initialize(self):
        """Initialize all components and validate configuration."""
        with LogContext(self.logger, "initialization"):
            # Load configuration
            config = self.config_manager.load_config(self.config_path)
            self.logger.info(f"Loaded configuration from: {self.config_path}")
            
            # Initialize providers
            self.nextcloud_provider = create_nextcloud_provider(config)
            self.xibo_provider = create_xibo_provider(config, debug=True)
            
            # Test connections
            if not self.nextcloud_provider.connect():
                raise RuntimeError("Failed to connect to NextCloud server")
            self.logger.info("Successfully connected to NextCloud")
            
            if not self.xibo_provider.authenticate():
                raise RuntimeError("Failed to authenticate with Xibo CMS")
            self.logger.info("Successfully authenticated with Xibo CMS")
            
            # Log configuration summary
            display_name = self.config_manager.get_display_name()
            poll_interval = self.config_manager.get_poll_interval()
            extensions = self.config_manager.get_extensions()
            nextcloud_path = self.config_manager.get_nextcloud_config()['path']
            
            self.logger.info(f"Configuration loaded:")
            self.logger.info(f"  Display: {display_name}")
            self.logger.info(f"  NextCloud path: {nextcloud_path}")
            self.logger.info(f"  Extensions: {extensions}")
            self.logger.info(f"  Poll interval: {poll_interval}s")
    
    def process_file(self, file_info) -> bool:
        """
        Process a single file: download and upload to Xibo.
        
        Args:
            file_info: File information from NextCloud
            
        Returns:
            True if successful, False otherwise
        """
        with LogContext(self.processor_logger, "file_processing", file=file_info.name):
            try:
                # Download file to temporary location
                temp_dir = "/tmp"  # Simple temp directory for now
                local_path = f"{temp_dir}/{file_info.name}"
                
                downloaded_path = self.nextcloud_provider.download_file(file_info.path, local_path)
                if not downloaded_path:
                    return False
                
                # Upload to Xibo
                media_info = self.xibo_provider.upload_media(downloaded_path)
                if not media_info:
                    return False
                
                # Set as display content
                display_name = self.config_manager.get_display_name()
                success = self.xibo_provider.set_display_content(
                    str(media_info.get('mediaId')), 
                    display_name
                )
                
                # Cleanup downloaded file
                import os
                try:
                    os.remove(downloaded_path)
                except:
                    pass
                
                if success:
                    self.processor_logger.info(f"Successfully processed {file_info.name}")
                    return True
                else:
                    self.processor_logger.error(f"Failed to set display content for {file_info.name}")
                    return False
                    
            except Exception as e:
                self.processor_logger.error(f"Error processing {file_info.name}: {e}")
                return False
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle."""        
        # Get new files
        new_files = self.nextcloud_provider.get_new_files_since(
            self.latest_upload_date,
            self.config_manager.get_nextcloud_config()['path'],
            self.config_manager.get_extensions()
        )
        
        if not new_files:
            return ProcessingStats()  # Empty stats
        
        # Process files
        stats = ProcessingStats()
        
        for file_info in new_files:
            # Update latest upload date
            self.latest_upload_date = max(self.latest_upload_date, file_info.upload_date)
            
            # Process file
            if self.process_file(file_info):
                stats.add_success()
            else:
                stats.add_failure()
        
        return stats
    
    def run(self):
        """Run the main monitoring loop."""
        self.logger.info("Starting Xibo Screen Updater")
        
        try:
            self.initialize()
            poll_interval = self.config_manager.get_poll_interval()
            
            self.logger.info("Starting monitoring loop")
            self.logger.info("-" * 50)
            
            while True:
                try:
                    stats = self.run_monitoring_cycle()
                    
                    if stats.processed > 0:
                        self.logger.info(stats.get_summary())
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring cycle: {e}")
                    self.logger.debug("Full traceback:", exc_info=True)
                
                sleep(poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            self.logger.debug("Full traceback:", exc_info=True)
            sys.exit(1)


def main():
    """
    Main entry point for Xibo Screen Updater.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor NextCloud for new files and upload to Xibo')
    parser.add_argument('-c', '--config', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    try:
        # Resolve configuration file path
        config_path = resolve_config_path(args.config)
        
        # Create and run application
        app = XiboScreenUpdater(config_path)
        app.run()
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
