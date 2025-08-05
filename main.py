import os
import sys
from datetime import datetime
from time import sleep
import traceback
from typing import Dict, List, Optional
import argparse

from config_manager import ConfigManager, ConfigurationError, resolve_config_path
from file_processor import FileProcessor, ProcessingStats
from logging_config import setup_logging, get_component_logger, LogContext
from xibo_client import create_xibo_client_from_config

class XiboScreenUpdater:
    """Main application class for Xibo Screen Updater."""
    
    def __init__(self, config_path: str):
        """
        Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config(config_path)
        self.logger = setup_logging()
        self.xibo_client = None
        self.latest_upload_date = datetime.utcnow()
        
        # Get component loggers
        self.nextcloud_logger = get_component_logger('nextcloud', self.logger)
        self.xibo_logger = get_component_logger('xibo', self.logger)
        self.processor_logger = get_component_logger('processor', self.logger)
    
    def initialize(self):
        """Initialize all components and validate configuration."""
        with LogContext(self.logger, "initialization"):
            # Initialize Xibo client
            self.xibo_client = create_xibo_client_from_config(
                self.config, 
                debug=True
            )
            
            # Test Xibo authentication
            if not self.xibo_client.authenticate():
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
    
    def process_file(self, file_info, processor: FileProcessor) -> bool:
        """
        Process a single file: download and upload to Xibo.
        
        Args:
            file_info: File information from NextCloud
            processor: File processor instance
            
        Returns:
            True if successful, False otherwise
        """
        with LogContext(self.processor_logger, "file_processing", file=file_info.name):
            try:
                # Download file
                local_path = processor.download_file(file_info)
                if not local_path:
                    return False
                
                # Upload to Xibo and set as screen content
                display_name = self.config_manager.get_display_name()
                success = self.xibo_client.upload_and_set_screen(
                    local_path, 
                    display_name
                )
                
                # Cleanup downloaded file
                processor.cleanup_file(local_path)
                
                if success:
                    self.processor_logger.info(f"Successfully processed {file_info.name}")
                    return True
                else:
                    self.processor_logger.error(f"Failed to upload {file_info.name} to Xibo")
                    return False
                    
            except Exception as e:
                self.processor_logger.error(f"Error processing {file_info.name}: {e}")
                return False
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle."""
        nextcloud_config = self.config_manager.get_nextcloud_config()
        
        with FileProcessor(nextcloud_config, self.nextcloud_logger) as processor:
            # Get new files
            new_files = processor.get_new_files(self.latest_upload_date)
            
            if not new_files:
                return ProcessingStats()  # Empty stats
            
            # Process files
            stats = ProcessingStats()
            
            for file_info in new_files:
                # Update latest upload date
                self.latest_upload_date = max(self.latest_upload_date, file_info.upload_date)
                
                # Process file
                if self.process_file(file_info, processor):
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
