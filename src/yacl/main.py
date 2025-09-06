#!/usr/bin/env python3
"""
Main entry point for YACL application

This module provides the main application entry point and basic application setup.
"""

import sys
import os
import logging

def main():
    """Main application entry point."""
    logger = None
    try:
        logger = logging.getLogger("YACL")
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(module)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        logger.info("=" * 60)
        logger.info("Starting YACL - Yet Another Cataclysm Launcher")
        logger.info("=" * 60)
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Platform: {sys.platform}")

        try:
            logger.info("Checking Tkinter availability...")
            import tkinter as tk
            logger.info("Tkinter is available")
        except ImportError as e:
            logger.error(f"Failed to import Tkinter: {e}")
            logger.error("Tkinter should be included with Python. Please check your Python installation.")
            return 1
        except Exception as e:
            logger.error(f"Error with Tkinter: {e}")
            return 1

        try:
            logger.info("Creating YACL application...")
            from yacl.application import YACLApplication

            app = YACLApplication()
            exit_code = app.run()

            logger.info(f"YACL application exited with code: {exit_code}")
            return exit_code

        except Exception as e:
            logger.error(f"Error creating or running application: {e}", exc_info=True)
            return 1

    except KeyboardInterrupt:
        if logger:
            logger.info("Shutdown requested by user (Ctrl+C)")
        else:
            print("\nShutdown requested by user.")
        return 0
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error in main: {e}", exc_info=True)
        else:
            print(f"Unexpected error: {e}")
        return 1
    finally:
        if logger:
            logger.info("YACL main function completed")
            logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
