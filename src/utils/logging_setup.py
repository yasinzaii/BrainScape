# src/utils/logging_setup.py
import os
import logging
import logging.config
from pathlib import Path
from typing import Optional, Union, Tuple
from utils.json_handler import JsonHandler


def configure_logging(log_config_path: str = "", default_level: int  = logging.DEBUG) -> logging.Logger:
    """
    Configure logging based on a JSON configuration file.

    Args:
        log_config_path (str): Path to the JSON logging configuration file.
        default_level (int, optional): The default logging level to use if the configuration file is not found or invalid. Defaults to logging.DEBUG.

    Returns:
        logging.Logger: The root logger configured based on the provided configuration.
    """
    
    # Check If nothing is passed for Logger Config Path
    log_config_path = "" if  log_config_path is None else log_config_path

    # Get the main logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=default_level)

    # Check if the configuration file exists
    if not os.path.exists(log_config_path):
        logger.error(f"Logging configuration file '{log_config_path}' not found. Using basic configuration, with 'level == {default_level}'.")
        return logger
    
    # Loading the logger configuration file
    json_handler = JsonHandler(log_config_path)
    if json_handler.is_loaded():
        
        # Read and Apply the logging config
        config = json_handler.get_data()
        
        try:
            logging.config.dictConfig(config)
            logger = logging.getLogger(__name__)
            logger.info(f"Logging configuration loaded successfully from '{log_config_path}'.")
        except Exception as e:
            logger.exception(f"""Error applying logging configuration from '{log_config_path}': {e}. 
                             Using basic configuration with level '{logging.getLevelName(default_level)}'.""")

        return logger
        
    else:
        logger.error(f"Unable to load Logger Configuration File: {log_config_path}, using default logger instead.")
        return logger


def configure_session_logging(
    session_log_file: Union[str, Path],
    log_config_path: Union[str, Path],
    formatter_name: str = 'simple',
    logger_name: str = 'session_logger',
    logger_level: int = logging.DEBUG,
    handler_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Configures a logger for a specific session, with logging output to a given log file.

    Args:
        session_log_file (str or Path): Path to the log file for this session.
        log_config_path (str or Path): Path to the JSON logging configuration file.
        formatter_name (str): Name of the formatter to use ('simple' or 'extra').
        logger_name (str): Name of the logger to create.
        logger_level (int): Logging level for the logger (default: logging.DEBUG).
        handler_level (int): Logging level for the file handler (default: logging.DEBUG).

    Returns:
        logging.Logger: The configured session logger.

    Raises:
        FileNotFoundError: If the logging configuration file is not found.
        ValueError: If the formatter is not found in the configuration.
    """
    
    # Ensure session_log_file is a Path object
    session_log_file = Path(session_log_file)
    session_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if the logging configuration file exists
    log_config_path = Path(log_config_path)
    if not log_config_path.exists():
        raise FileNotFoundError(f"Logging configuration file '{log_config_path}' not found.")
    
    # Load the logging configuration file
    json_handler = JsonHandler(log_config_path)
    if not json_handler.is_loaded():
        raise ValueError(f"Unable to load logging configuration file: '{log_config_path}'.")
    
    # Get the configuration dictionary
    config = json_handler.get_data()
    
    # Get the formatter configuration from the config dictionary
    formatter_config = config.get('formatters', {}).get(formatter_name)
    if not formatter_config:
        raise ValueError(f"Formatter '{formatter_name}' not found in configuration.")

    # Create the formatter
    formatter = logging.Formatter(
        fmt=formatter_config['format'],
        datefmt=formatter_config.get('datefmt')
    )
    
    # Create the file handler for the session log
    file_handler = logging.FileHandler(session_log_file, encoding='utf8')
    file_handler.setLevel(handler_level)
    file_handler.setFormatter(formatter)
    
    # Create a custom logger for the session
    logger = logging.getLogger(logger_name)
    logger.setLevel(logger_level)
    logger.addHandler(file_handler)
    logger.propagate = False  # Prevent logs from propagating to ancestor loggers

    return logger