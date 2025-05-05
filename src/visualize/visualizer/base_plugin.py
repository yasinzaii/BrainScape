
from pathlib import Path
from omegaconf import OmegaConf
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class VisualizerPlugin(ABC):
    """
    Base abstract class for Visualizer plugins.
    All visualizer plugins must inherit from this class and implement `run()`.
    """

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return the unique name of the plugin."""
        pass

    @abstractmethod
    def __init__(self,
                 dataset_settings: Dict[str, Any],
                 dataset_path: Path,
                 mapping: List,
                 config: OmegaConf):
        """
        Initialize the VisualizerPlugin.

        Args:
            dataset_settings (dict): Final merged dataset settings.
            dataset_path (Path): Path object for the dataset root folder.
            mapping (list): Mapping of the dataset.
            config (OmegaConf): Main configuration object.
        """
        pass

    @abstractmethod
    def run(self) -> bool:
        """
        Execute the visualization job.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass
