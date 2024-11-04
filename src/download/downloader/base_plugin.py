# src/download/downloader/base.py

from typing import List, Tuple
from abc import ABC, abstractmethod

class DownloaderPlugin(ABC):
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "BaseDownloader"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    
    
    @abstractmethod
    def download(self) -> Tuple[bool, List[str]]:
        """
        Download the dataset.

        Returns:
            tuple: (success flag, output data)
        """
        pass

    @abstractmethod
    def get_source_file_list(self) -> List[str]:
        """
        Acquire source file list.

        Returns:
            list: A list of paths from the source
        """
        pass