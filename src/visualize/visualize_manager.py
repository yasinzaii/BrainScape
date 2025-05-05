# src/visualize/visualize_manager.py

import logging
from pathlib import Path
from omegaconf import OmegaConf
from typing import Dict, Any, List

from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# Import the DefaultVisualizer plugin
from visualize.visualizer.default_visualizar import DefaultVisualizer


class VisualizerManager:

    def __init__(
        self,
        config: OmegaConf,
        target_datasets: List[str],
        default_dataset_settings: Dict[str, Any],
        mapping: Dict[str, Any],
    ):
        """
        Initialize the VisualizerManager.

        Args:
            config (OmegaConf): Main configuration object.
            target_datasets (List[str]): List of dataset names to visualize.
            default_dataset_settings (Dict[str, Any]): Default dataset config for all datasets.
            mapping (Dict[str, Any]): Mapping information for datasets.
        """
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings
        self.mapping = mapping
        self.logger = logging.getLogger(__name__)
    
    def initiate_visualization(self):
        """
        Initiate the visualization process for all target datasets.
        """
        for dataset_name in self.target_datasets:
            self.logger.info(f"Visualization Manager - Visualizing dataset: {dataset_name}")

            # Merge default settings with dataset-specific settings
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings = JsonHandler(dataset_path / self.config.datasetSettingsJson)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )
            
            # Dataset visualization directory
            visualize_dir_dataset = dataset_path / self.config.visualizeDirName
            
            # Checking isVisualized Flag and visualize Folder.
            isVisualized = final_settings.get("isVisualized", False)
            if isVisualized:
                self.logger.info(f"VisualizerManager - 'isVisualized' flag set to True in dataset:{dataset_name} metadata.")
                if visualize_dir_dataset.exists() and any(visualize_dir_dataset.iterdir()):
                    self.logger.info(f"VisualizerManager - dataset:{dataset_name} visualize directory exists and not empty - path:{str(visualize_dir_dataset)} - Skipping Visualization.")
                    continue
                else:
                    self.logger.info(f"VisualizerManager - 'isVisualized' flag set to True for dataset:{dataset_name} yet visualize directory empty or missing - Path:{str(visualize_dir_dataset)} - visualizing again.")
                    # Updating dataset metadata and unsetting 'isVisualized' flag
                    dataset_settings.update_json({'isVisualized':False}).save_json()
            
            # TODO
            # Dynamically Acquire the plugin via Datset Config File
            # As there is only one 'DefaultVisualizer' plugin keeping it simple for now
            visualizer_cls = DefaultVisualizer
            
            # Retrieve the dataset-specific mapping 
            dataset_mapping = self.mapping.get(dataset_name, [])
            if not dataset_mapping:
                self.logger.error(f"VisualizerManager - No mapping found for dataset '{dataset_name}'. Cannot visualize. Skipping.")
                continue
            
            
            # Instantiate the visualizer plugin
            visualizer = visualizer_cls(
                dataset_settings=final_settings,
                dataset_path=dataset_path,
                mapping=dataset_mapping,
                config=self.config,
            )
            
            # Run the visualization
            success = visualizer.run()
            dataset_settings.update_json({"isVisualized": success}).save_json()
            if success:
                self.logger.info(f"VisualizerManager - Visualization completed for dataset '{dataset_name}'.")
            else:
                self.logger.error(f"VisualizerManager - Visualization failed for dataset '{dataset_name}'.")