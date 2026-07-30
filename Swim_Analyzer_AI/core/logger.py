"""
Structured logger for SwimAnalyzer AI.
"""
import logging
import sys
from typing import Optional
from core.config import config


def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return a standard logger instance.
    
    Args:
        name (str): The name of the logger, typically __name__ of the module.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times if instantiated repeatedly
    if not logger.handlers:
        level = getattr(logging, config.log_level.upper(), logging.INFO)
        logger.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Stream Handler (Console)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
    return logger
