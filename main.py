import os
import shutil
import tempfile
from datetime import datetime
from time import sleep
import traceback
from typing import Dict, List, Optional
import argparse

from config_manager import ConfigManager, ConfigurationError, resolve_config_path
from nextcloud_client import NextCloudClient
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
    Main function that monitors NextCloud for new files and uploads them to Xibo.
    """
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor NextCloud for new files and upload to Xibo')
    parser.add_argument('-c', '--config', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    config_path = None
    if args.config:
        config_path = args.config
    elif 'CONFIG_PATH' in os.environ:
        config_path = os.environ['CONFIG_PATH']
    else:
        config_path = './config.yaml'
    config = load_config(config_path)
    display_name = config['project_to']['display'].get('name')  # Use the name from config
    poll_interval = config['copy_from'].get('poll_interval', 10)  # Default to 10 seconds

    start_time = datetime.utcnow()

    if not display_name:
        print("❌ Screen name not found in config. Please check your configuration.")
        exit(1)

    print(f"Starting file monitor for screen: {display_name}")
    print(f"Monitoring NextCloud path: {config['copy_from']['path']}")
    print(f"Extensions: {config['copy_from']['extensions']}")
    print(f"Poll interval: {poll_interval} seconds")
    
    tmp_folder = tempfile.mkdtemp("__xibo_upload")
    print(f"Temporary folder created: {tmp_folder}")
    print("-" * 50)

    latest_upload_date = start_time

    while True:
        try:
            new_files = get_nextcloud_files_detailed(config)
            if new_files:
                processed_count = success_count = failed_count = 0
                for file_info in new_files:
                    # Skip files modified before the script started
                    if file_info['upload_date'] <= latest_upload_date:
                        continue
                    
                    processed_count += 1
                    latest_upload_date = max(latest_upload_date, file_info['upload_date'])
                    file_name = file_info['name']
                    print(f"Processing: {file_name}")
                    
                    # Download file from NextCloud
                    try:
                        new_file_path = os.path.join(tmp_folder, file_name)
                        print(f"Downloading {file_name} to {new_file_path}")
                        downloaded_path = download_file(file_name, config)
                        if downloaded_path:
                            print(f"Downloaded: {downloaded_path}")
                            
                            # Upload to Xibo and set as default for screen
                            success = upload_and_set_xibo_screen(
                                downloaded_path, 
                                config, 
                                display_name
                            )
                            os.remove(downloaded_path)  # Clean up downloaded files after upload
                            
                            if success:
                                success_count += 1
                                print(f"✅ Successfully processed {file_name}")
                            else:
                                failed_count += 1
                                print(f"❌ Failed to upload {file_name} to Xibo")
                        else:
                            failed_count += 1
                            print(f"❌ Failed to download {file_name}")
                            
                    except Exception as e:
                        failed_count += 1
                        print(f"❌ Error processing {file_name}: {e}")
                        traceback.print_exc()
            else:
                pass
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            traceback.print_exc()
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)
            if processed_count > 0:
                print(f"Processed {processed_count} files: {success_count} succeeded, {failed_count} failed")
            
        sleep(poll_interval)

if __name__ == "__main__":
    main()
