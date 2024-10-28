# src/dataset/dataset_manager.py

import os
import logging
from pathlib import Path
from typing import Dict, Any, List

from omegaconf import OmegaConf
from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# For Loading Mapper Plugins
from utils.plugin_loader import PluginLoader
from dataset.mapper.base_plugin import DatasetMapperPlugin

# Directory containing Mapper Plugins (in 'mapper' folder beside 'dataset_manager.py')
mapper_plugins_directory = Path(__file__).resolve().parent / 'mapper'

class DatasetManager:

    def __init__(self, config: OmegaConf, target_datasets: List[str], default_dataset_settings: Dict[str, Any]):
        
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings

        self.logger = logging.getLogger(__name__)

        # Acquiring Mapper Plugins
        self.plugin_loader = PluginLoader(mapper_plugins_directory, DatasetMapperPlugin)
        self.plugin_loader.load_plugins()  # Loading the Mapper Plugins.

        # Mapping Record 
        self.mapping = {}


    def initiate_mapping(self):
        for dataset_name in self.target_datasets:

            # Merging Default Settings with Dataset Settings.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings_path = dataset_path / self.config.datasetSettingsJson
            dataset_settings = JsonHandler(dataset_settings_path)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )


            # Acquiring Mapper Plugin Name
            try:
                mapper_name = final_settings['mapping']['plugin']
            except KeyError as e:
                self.logger.error(f"Mapper type (Key: 'mapping.plugin') missing from dataset '{dataset_name}' settings, skipping mapping job. Error: {e}")
                continue  # Skipping

            # Path of the download directory
            download_dir_path = dataset_path / final_settings["downloadDirName"]

            # Check if the dataset has been downloaded
            if not final_settings.get("isDownloaded"):
                self.logger.error(f"Dataset '{dataset_name}' has not been downloaded yet. Skipping mapping job.")
                continue  # Skipping

            # Check if dataset JSON has already been created
            if final_settings.get("isDatasetJsonCreated"):
                self.logger.info(f"Dataset JSON for '{dataset_name}' already created. Skipping mapping job.")
                continue  # Skipping

            # Dynamically load the correct mapper plugin based on 'mapper' setting
            mapper_cls = self.plugin_loader.get_plugin_by_name(mapper_name)
            if not mapper_cls:
                self.logger.error(f"Requested mapper plugin '{mapper_name}' not found. Skipping mapping for dataset '{dataset_name}'.")
                continue  # Skipping

            # Instantiate the mapper
            mapper = mapper_cls(dataset_settings=final_settings, dataset_path=str(dataset_path))

            # Perform the mapping
            try:
                dataset_mapping = mapper.map()
            except Exception as e:
                self.logger.error(f"Mapping failed for dataset '{dataset_name}'. Error: {e}")
                dataset_settings.update_json({"isDatasetJsonCreated": False}).save_json()
                continue  # Skipping

            # Save the mapping result to the dataset JSON file
            self.mapping.update({dataset_name:dataset_mapping})


    def get_mapping(self):
        return self.mapping