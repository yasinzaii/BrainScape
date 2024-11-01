# src/preprocess/preprocessor/base_plugin.py

from abc import ABC, abstractmethod
from pathlib import Path

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
        self.dataset_settings = dataset_settings
        self.dataset_path = dataset_path
        self.mapping = mapping
        self.config = config

    @abstractmethod
    def run(self) -> bool:
        """
        Run the preprocessing steps.
        Returns:
            bool: True if preprocessing was successful, False otherwise.
        """
        pass
