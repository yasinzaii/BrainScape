# src/download/downloader/base.py

from typing import List
from abc import ABC, abstractmethod

class DownloaderPlugin(ABC):
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "BaseDownloader"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    
    @abstractmethod
    def download(self, final_settings: dict, dataset_path: str) -> bool:
        """
        Download the dataset.

        Args:
            final_settings (dict): Dataset-specific settings.
            dataset_path (str): Path to the dataset directory.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_source_file_list(self, final_settings: dict) -> List[str]:
        """
        Acquire Source File List.

        Args:
            final_settings (dict): Dataset-specific settings.

        Returns:
            list: A list of paths from the source
        """
        pass