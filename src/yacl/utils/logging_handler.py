"""
Event Manager Logging Handler for YACL

This module provides a custom logging handler that bridges Python's standard
logging system with YACL's event management system.
"""

import logging
import traceback
from typing import Optional

from yacl.services.events import EventManager, Events


class EventManagerHandler(logging.Handler):
    """
    Custom logging handler that forwards log records to the event manager.
    """
    
    def __init__(self, event_manager: Optional[EventManager] = None, level: int = logging.NOTSET):
        """
        Initialize the event manager logging handler.
        
        Args:
            event_manager: The event manager instance to forward messages to.
                          If None, the handler will silently ignore log records.
            level: The minimum log level to handle (default: NOTSET)
        """
        super().__init__(level)
        self.event_manager = event_manager
        
        # Configure default formatter if none is set
        if not self.formatter:
            self.setFormatter(logging.Formatter(
                '%(name)s - %(levelname)s - %(message)s'
            ))
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record.
        """
        try:
            if self.event_manager is None:
                return

            formatted_message = self.format(record)

            if record.exc_info:
                exc_text = self.formatException(record.exc_info)
                formatted_message = f"{formatted_message}\n{exc_text}"


            self.event_manager.emit(Events.STATUS_MESSAGE, message=formatted_message, message_type=record.levelname.lower())

        except Exception as e:
            self.handleError(record)

    def formatException(self, ei) -> str:
        """
        Format exception information for inclusion in log messages.

        Args:
            ei: Exception info tuple (type, value, traceback) from sys.exc_info()

        Returns:
            str: Formatted exception string
        """
        try:
            return ''.join(traceback.format_exception(*ei))
        except Exception:
            return f"Exception formatting failed: {ei[1] if ei and len(ei) > 1 else 'Unknown exception'}"

    def set_event_manager(self, event_manager: Optional[EventManager]) -> None:
        """
        Set or update the event manager instance.
        
        Args:
            event_manager: New event manager instance, or None to disable
        """
        self.event_manager = event_manager
    
    def handleError(self, record: logging.LogRecord) -> None:
        """
        Handle errors that occur during logging.
        Args:
            record: The log record that caused the error
        """
        try:
            # Get exception info
            ei = __import__('sys').exc_info()
            if ei[1] is not None:
                error_msg = f"Error in EventManagerHandler while processing record: {record.getMessage()}"

                print(f"EventManagerHandler handleError failed: {error_msg}", file=__import__('sys').stderr)
                traceback.print_exception(*ei, file=__import__('sys').stderr)
        except Exception:
            pass

    
    
    def close(self) -> None:
        """
        Close the handler and clean up resources.
        """
        try:
            self.event_manager = None
            
            super().close()
            
        except Exception as e:
            print(f"Error closing EventManagerHandler: {e}", file=__import__('sys').stderr)

def create_event_manager_handler(
    event_manager: Optional[EventManager] = None,
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None
) -> EventManagerHandler:
    """
    Convenience function to create and configure an EventManagerHandler.
    
    Args:
        event_manager: Event manager instance to use
        level: Minimum log level to handle
        formatter: Custom formatter to use (optional)
        
    Returns:
        EventManagerHandler: Configured handler instance
    """
    handler = EventManagerHandler(event_manager, level)
    
    if formatter:
        handler.setFormatter(formatter)
    
    return handler


def add_event_manager_handler_to_logger(
    logger: logging.Logger,
    event_manager: Optional[EventManager] = None,
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None
) -> EventManagerHandler:
    """
    Convenience function to add an EventManagerHandler to an existing logger.
    
    Args:
        logger: Logger to add the handler to
        event_manager: Event manager instance to use
        level: Minimum log level to handle
        formatter: Custom formatter to use (optional)
        
    Returns:
        EventManagerHandler: The handler that was added to the logger
    """
    handler = create_event_manager_handler(event_manager, level, formatter)
    logger.addHandler(handler)
    return handler
