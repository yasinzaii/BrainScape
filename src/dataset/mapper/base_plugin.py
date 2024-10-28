# src/dataset/mapper/base.py

from typing import List
from abc import ABC, abstractmethod

class DatasetMapperPlugin(ABC):
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "BaseMapper"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    
    @abstractmethod
    def map(self, final_settings: dict, dataset_path: str) -> dict:
        """
        Maps and saves the Subject-Session-MRI Modality paths into a JSON file.

        Args:
            final_settings (dict): Dataset-specific settings.
            dataset_path (str): Path to the dataset directory.
            mapping (dict): Dataset Mapping - Aquired from Mapper Module

        Returns:
            Dict[str, List[obj]]: A mapping of dataset names to lists of MRI file paths.
        """
        pass
