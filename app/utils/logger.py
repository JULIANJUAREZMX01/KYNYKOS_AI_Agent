"""Logging configuration"""

import sys
from loguru import logger as _logger


def get_logger(name: str = "kynikos"):
    """Get configured logger instance"""
    _logger.remove()
    
    # Console logging
    _logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | {name}:{function}:{line} - <level>{message}</level>",
        level="INFO"
    )
    
    # File logging for Sentinel Monitoring
    _logger.add(
        "logs/kynikos.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",  # Sentinel only cares about Errors by default
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    return _logger
