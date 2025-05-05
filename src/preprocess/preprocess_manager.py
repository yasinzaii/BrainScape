# src/preprocess/preprocess_manager.py

import logging
from pathlib import Path
from omegaconf import OmegaConf
from typing import Dict, Any, List
from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# For Loading Preprocessor Plugins
from utils.plugin_loader import PluginLoader
from preprocess.preprocessor.base_plugin import PreprocessorPlugin

# Directory containing Preprocessor Plugins (in 'preprocessor' folder)
preprocessor_plugins_directory = Path(__file__).resolve().parent / 'preprocessor'

class PreprocessManager:
    def __init__(self, config: OmegaConf, target_datasets: List[str], default_dataset_settings: Dict[str, Any], mapping:Dict[str, Any]):
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings
        self.mapping = mapping

        self.logger = logging.getLogger(__name__)

        # Loading Preprocessor Plugins
        self.plugin_loader = PluginLoader(preprocessor_plugins_directory, PreprocessorPlugin)
        self.plugin_loader.load_plugins()

    def initiate_preprocessing(self):
        for dataset_name in self.target_datasets:
            
            # Merging Default Settings with Dataset Settings.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings = JsonHandler(dataset_path / self.config.datasetSettingsJson)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )
            
            # Check if the dataset has been downloaded
            if not final_settings.get("isDownloaded"):
                self.logger.warning(f"PreprocessManager - Dataset '{dataset_name}' has not been downloaded yet. Skipping preprocessing job for {dataset_name}.")
                continue  # Skipping
            
            # Acquiring the Mapping 
            mapping = self.mapping[dataset_name]
            
            # Acquiring Preprocessed Diretcory
            preprocess_dir_name =  final_settings.get("preprocessedDirName", "preprocessed")
            preprocess_dir_path = dataset_path / preprocess_dir_name


            # Acquiring Preprocessor Plugin Name
            try:
                preprocessor_name = final_settings['preprocess']['preprocessor']
            except KeyError as e:
                self.logger.error(f"PreprocessManager - Preprocessor (Key: 'preprocessor') missing from dataset '{dataset_name}' settings. Skipping preprocessing. Error: {e}")
                continue  # Skip to the next dataset

            # Check if preprocessing is already done
            if final_settings.get("isPreprocessed", False):
                self.logger.info(f"PreprocessManager - Dataset:{dataset_name} 'isPreprocessed' already set - Checking if Preprocessed dir is present and not empty.")
                
                # Check if the Preprocessed dir exist.
                if preprocess_dir_path.exists():
                    # Check if the Preprocessed dir is not empty
                    if any(preprocess_dir_path.iterdir()):
                        self.logger.info(f"PreprocessManager - Dataset:{dataset_name} Preprocessed dir is present and not empty - Skipping Preprocessing.")
                        continue 
                    else:
                        self.logger.error(f"PreprocessManager - Dataset:{dataset_name} 'isPreprocessed' already set but Preprocessed dir is empty - Preprocessing Again.")     
                else:
                    self.logger.error(f"PreprocessManager - Dataset:{dataset_name} 'isPreprocessed' already set but Preprocessed dir missing - Preprocessing Again.")


            # Get the preprocessor plugin class
            preprocessor_cls = self.plugin_loader.get_plugin_by_name(preprocessor_name)
            if not preprocessor_cls:
                self.logger.error(f"PreprocessManager - Requested preprocessor plugin '{preprocessor_name}' not found. Skipping dataset '{dataset_name}'.")
                continue

            # Initialize the preprocessor
            preprocessor = preprocessor_cls(dataset_settings=final_settings, dataset_path=dataset_path, mapping=mapping, config=self.config)

            # Perform preprocessing
            success = preprocessor.run()
            if success:
                self.logger.info(f"PreprocessManager - Preprocessing completed for dataset '{dataset_name}'. Updating 'isPreprocessed' flag.")
                dataset_settings.update_json({"isPreprocessed": True}).save_json()
            else:
                self.logger.error(f"PreprocessManager - Preprocessing failed for dataset '{dataset_name}'.")
                dataset_settings.update_json({"isPreprocessed": False}).save_json()


