"""
Media processing implementations.

This module provides media processors for transforming files before upload,
such as converting PDFs to images for better compatibility.
"""

import os
import logging
from typing import List
from abc import ABC, abstractmethod

from .base import MediaProcessor, registry


class PassThroughProcessor(MediaProcessor):
    """
    Pass-through processor that doesn't modify files.
    
    This processor handles all file types by simply copying them without modification.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def can_process(self, file_path: str) -> bool:
        """Can process any file by passing it through unchanged."""
        return os.path.exists(file_path)
    
    def process(self, input_path: str, output_path: str) -> bool:
        """Copy input file to output location without modification."""
        try:
            if input_path == output_path:
                return True  # No processing needed
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(input_path, output_path)
            
            self.logger.debug(f"Pass-through processed: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in pass-through processing: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        """Supports all file extensions."""
        return ['*']  # Wildcard indicates all extensions


class PDFToImageProcessor(MediaProcessor):
    """
    PDF to image converter processor.
    
    Converts PDF files to PNG images for better display compatibility.
    This is a placeholder implementation - requires additional dependencies.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            # Try to import required libraries
            # import pdf2image  # Would need: pip install pdf2image
            # import PIL        # Would need: pip install Pillow
            self._dependencies_available = False  # Set to False until dependencies are installed
            if not self._dependencies_available:
                self.logger.warning("PDF processing dependencies not available. Install pdf2image and Pillow to enable PDF conversion.")
        except ImportError:
            self._dependencies_available = False
            self.logger.warning("PDF processing dependencies not available.")
    
    def can_process(self, file_path: str) -> bool:
        """Can process PDF files if dependencies are available."""
        if not self._dependencies_available:
            return False
        return file_path.lower().endswith('.pdf')
    
    def process(self, input_path: str, output_path: str) -> bool:
        """Convert PDF to PNG image."""
        if not self._dependencies_available:
            self.logger.error("PDF processing dependencies not available")
            return False
        
        try:
            # Placeholder implementation
            # This would require pdf2image library:
            #
            # from pdf2image import convert_from_path
            # 
            # # Convert PDF to images
            # images = convert_from_path(input_path, first_page=1, last_page=1)
            # 
            # if images:
            #     # Save first page as PNG
            #     images[0].save(output_path, 'PNG')
            #     self.logger.info(f"Converted PDF to image: {input_path} -> {output_path}")
            #     return True
            
            self.logger.error("PDF to image conversion not implemented - requires pdf2image dependency")
            return False
            
        except Exception as e:
            self.logger.error(f"Error converting PDF to image: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        """Supports PDF files."""
        return ['.pdf']


class MediaProcessorChain:
    """
    Chain of media processors that tries each processor in order.
    
    This allows for a pipeline of different processors to handle different file types.
    """
    
    def __init__(self):
        self.processors = []
        self.logger = logging.getLogger(__name__)
    
    def add_processor(self, processor: MediaProcessor):
        """Add a processor to the chain."""
        self.processors.append(processor)
    
    def process_file(self, input_path: str, output_path: str) -> bool:
        """
        Process a file using the first capable processor in the chain.
        
        Args:
            input_path: Path to input file
            output_path: Path for processed output file
            
        Returns:
            True if processing successful, False otherwise
        """
        for processor in self.processors:
            if processor.can_process(input_path):
                self.logger.debug(f"Processing {input_path} with {processor.__class__.__name__}")
                return processor.process(input_path, output_path)
        
        self.logger.warning(f"No processor available for file: {input_path}")
        return False
    
    def get_processor_for_file(self, file_path: str) -> MediaProcessor:
        """Get the first processor that can handle the given file."""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        return None


def create_default_processor_chain() -> MediaProcessorChain:
    """
    Create a default media processor chain with common processors.
    
    Returns:
        MediaProcessorChain with default processors
    """
    chain = MediaProcessorChain()
    
    # Add processors in order of preference
    # PDF processor first (more specific)
    chain.add_processor(PDFToImageProcessor())
    
    # Pass-through processor last (handles everything else)
    chain.add_processor(PassThroughProcessor())
    
    return chain


# Register processors
registry.register_media_processor('passthrough', PassThroughProcessor)
registry.register_media_processor('pdf_to_image', PDFToImageProcessor)
