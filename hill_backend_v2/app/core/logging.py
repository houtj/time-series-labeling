"""Logging configuration for the application"""

import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Set up application logging with JSON formatting
    
    Args:
        debug: Whether to enable debug logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set log level
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

