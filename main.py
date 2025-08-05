#!/usr/bin/env python3
"""
Xibo Screen Updater - Main Entry Point

This is the main entry point for the Xibo Screen Updater application.
It imports and runs the main application from the new modular structure.
"""

import sys
import os

# Add src directory to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from xibo_screen_updater.core.application import main

if __name__ == "__main__":
    main()
