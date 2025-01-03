"""
Timing utilities for measuring function execution time.
"""

import time
import functools
from typing import Callable, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timing_decorator(description: str = None):
    """
    A decorator that measures and logs the execution time of a function.
    
    Args:
        description (str, optional): A description of the function's purpose.
            If not provided, uses the function name.
            
    Returns:
        Callable: The wrapped function that logs timing information.
        
    Example:
        @timing_decorator("Fetching research papers from Springer")
        def fetch_papers():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get function description
            func_desc = description or func.__name__.replace('_', ' ').title()
            
            # Start timing
            start_time = time.time()
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Log timing information
                logger.info(
                    f"✓ {func_desc} - Completed in {execution_time:.2f} seconds"
                )
                
                return result
                
            except Exception as e:
                # Log error with timing
                execution_time = time.time() - start_time
                logger.error(
                    f"✗ {func_desc} - Failed after {execution_time:.2f} seconds: {str(e)}"
                )
                raise
                
        return wrapper
    return decorator
