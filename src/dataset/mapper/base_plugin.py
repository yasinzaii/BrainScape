# src/dataset/mapper/base.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class DatasetMapperPlugin(ABC):
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "BaseMapper"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    
    @abstractmethod
    def map(self, existing_mapping: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Maps Paths/Info for datasets into a JSON object.

        Args:
            existing_mapping (dict): Existing mapping which will be updated.

        Returns:
            List[Dict[str, Any]]: A mapping for the dataset containing 
            subject/session/modality/download-paths etc info.
        """
        pass
