# src/preprocess/preprocessor/base_plugin.py

import logging

from pathlib import Path
from abc import ABC, abstractmethod

from utils.logging_setup import configure_session_logging

class PreprocessorPlugin(ABC):
    
    # Class-specific plugin name 
    plugin_name = "BasePreprocessor"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    

    def __init__(self, dataset_settings: dict, dataset_path: Path, mapping: dict, config: dict):
        """
        Args:
            dataset_settings (dict): Dataset-specific settings.
            dataset_path (str): Path to the dataset directory.
            mapping (dict): Dataset Mapping - Aquired from Mapper Module. 
            config (dict): Configurations

        """
        
        logger = logging.getLogger(__name__)
        
        self.dataset_settings = dataset_settings
        self.dataset_path = dataset_path
        self.mapping = mapping
        self.config = config
        
        
        # Processor Logger configuration
        self.preprocessor_log_file = self.dataset_path / "preprocess.log"
        
        # Delete the existing log file if it exists
        if self.preprocessor_log_file.exists():
            try:
                self.preprocessor_log_file.unlink()
                logger.info(f"Deleted existing log file: {self.preprocessor_log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file: {e}")
                
        self.preprocessor_logger = configure_session_logging(
            session_log_file=self.preprocessor_log_file,
            log_config_path=self.config.logger_config_file,
            logger_name=f'preprocess.{self.dataset_path.name}',
        )
        
 
        

    @abstractmethod
    def run(self) -> bool:
        """
        Run the preprocessing steps.
        Returns:
            bool: True if preprocessing was successful, False otherwise.
        """
        pass
