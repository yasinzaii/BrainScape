# src/utils/logging_setup.py
import os
import logging
import logging.config
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
        