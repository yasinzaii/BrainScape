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
        
        # Output Mapping Handler
        self.outDatasetJsonPath = Path(self.config.pathDataset) / self.config.datsetMriJson
        self.outDatasetJson = JsonHandler(self.outDatasetJsonPath, create_if_missing=True)

    # Download Mapping
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
                self.logger.error(f"Download Mapping - Mapper type (Key: 'mapping.plugin') missing from dataset '{dataset_name}' settings, skipping mapping job. Error: {e}")
                continue  # Skipping

            # Path of the download directory
            download_dir_path = dataset_path / final_settings["downloadDirName"]

            # Check if the dataset has been downloaded
            if not final_settings.get("isDownloaded"):
                self.logger.warning(f"Download Mapping - Dataset '{dataset_name}' has not been downloaded yet. Skipping mapping (downloaded MRIs) job for {dataset_name}.")
                continue  # Skipping

            # Check if dataset JSON has already been created
            if final_settings.get("isDatasetJsonCreated"):
                self.logger.info(f"Download Mapping - Dataset JSON for '{dataset_name}' already created. Skipping mapping job.")
                continue  # Skipping

            # Dynamically load the correct mapper plugin based on 'mapper' setting
            mapper_cls = self.plugin_loader.get_plugin_by_name(mapper_name)
            if not mapper_cls:
                self.logger.error(f"Download Mapping - Requested mapper plugin '{mapper_name}' not found. Skipping mapping for dataset '{dataset_name}'.")
                continue  # Skipping

            # Instantiate the mapper
            mapper = mapper_cls(dataset_settings=final_settings, dataset_path=str(dataset_path))

            # Perform the mapping
            try:
                dataset_mapping = mapper.map()
            except Exception as e:
                self.logger.error(f"Download Mapping - Mapping failed for dataset '{dataset_name}'. Error: {e}")
                dataset_settings.update_json({"isDatasetJsonCreated": False}).save_json()
                continue  # Skipping

            # Save the mapping result to the dataset JSON file
            self.mapping.update({dataset_name:dataset_mapping})


    def get_mapping(self):
        return self.mapping
    
    def save_mapping(self):
        self.outDatasetJson.set_data(self.mapping).save_json()
    
    
    # TODO - This following code is hardcoded fix it.
    def preprocessed_mapping(self):
        for dataset_name in self.target_datasets:
            
            self.logger.info(f"Preprocessed Mapping - Dataset:{dataset_name}")
            
            # Merging Default Settings with Dataset Settings.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings_path = dataset_path / self.config.datasetSettingsJson
            dataset_settings = JsonHandler(dataset_settings_path)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )

            # Path of the preprocessed directory
            preprocessed_dir_name = final_settings["preprocess"]["preprocessDirName"]
            preprocessed_dir_path = dataset_path / preprocessed_dir_name

            # Check if the dataset has been preprocessed
            if not final_settings.get("isPreprocessed"):
                self.logger.warning(f"Dataset '{dataset_name}' is not Preprocessed yet. Skipping mapping (preprocessed MRIs) job.")
                continue  # Skipping
            
            """
            # Check if dataset JSON has already been created
            if final_settings.get("isDatasetJsonCreated"):
                self.logger.info(f"Dataset JSON for '{dataset_name}' already created. Skipping mapping job.")
                continue  # Skipping
            """
            
            for entry in self.mapping[dataset_name]:
                entry[preprocessed_dir_name] = {}
                for mri in entry['mris'].keys():
                    
                    # Modality pattern to match with. 
                    mod_pattern = f"*{mri}.nii.gz"
                    
                    prep_mod_mri_dir = preprocessed_dir_path / f"{entry['subject']}.{entry['session']}.{entry['type']}.{entry['group']}"
                    prep_mod_mri_dir = prep_mod_mri_dir / "norm_bet"
                    prep_mod_mri_imgs = list(prep_mod_mri_dir.rglob(mod_pattern))
                    if len(prep_mod_mri_imgs) != 1:
                        self.logger.error(f"Preprocessed Mapping - MRIs Image Expectation and Actuality Mismatch. Dataset:{dataset_path.name}")
                        raise
                    else:
                        relative_path = prep_mod_mri_imgs[0].relative_to(preprocessed_dir_path)
                        entry[preprocessed_dir_name][mri] = str(relative_path)
                        pass
            
            self.logger.info(f"Preprocessed Mapping - Finished Mapping, Dataset:{dataset_name}")


    def demographic_mapping(self):
        """
        Applies DemographicMapper plugin to integrate participant 
        demographic data into the existing mappings in self.mapping.
        """
        for dataset_name in self.target_datasets:
            self.logger.info(f"Demographic Mapping - Dataset: {dataset_name}")

            # Load the dataset settings
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings_path = dataset_path / self.config.datasetSettingsJson
            dataset_settings = JsonHandler(dataset_settings_path)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )
            
            # Dataset demographics Schema and Data Paths
            demogr_dir = Path(self.config.demographicsDir)
            dataset_demogr_dir = demogr_dir / dataset_name
            demographics_data_path = dataset_demogr_dir / self.config.demographicsTSV
            demographics_schema_path = demogr_dir / self.config.demographicsMappingYaml
            
            # Issue warning if dataset demographics dir empty - Missing demographics
            if dataset_demogr_dir.exists() and dataset_demogr_dir.is_dir():
                if not any(dataset_demogr_dir.iterdir()):
                    self.logger.warning(f"Demographic Mapping - Demographics Dir is Empty for Dataset: {dataset_name}, Missing participants.tsv file. Skipping Mapping")  
                    continue  
            else:
                self.logger.warning(f"Demographic Mapping - Missing Demographics Dir for Dataset: {dataset_name}, Skipping Mapping")  
                continue  

            # Determine if we want to do demographics on this dataset now
            #if not final_settings.get("isDemographicsReady", False):
            #    self.logger.info(f"Dataset '{dataset_name}' not marked for demographics. Skipping.")
            #   continue
            
            
            # We assume the plugin name is stored in settings, or we can hard-code "DemographicMapper"
            try:
                mapper_name = final_settings['demographicsPlugin']
            except KeyError:
                self.logger.warning(f"No 'demographics_plugin' specified for dataset '{dataset_name}'. Skipping.")
                continue

            # Retrieve plugin class
            mapper_cls = self.plugin_loader.get_plugin_by_name(mapper_name)
            if not mapper_cls:
                self.logger.error(f"Demographic plugin '{mapper_name}' not found for dataset '{dataset_name}'.")
                continue
            
            mapper = mapper_cls(
                    dataset_settings=final_settings, 
                    dataset_name = dataset_name,
                    demogr_schema_path = str(demographics_schema_path), 
                    demogr_data_path = str(demographics_data_path))

            
            existing_map = self.mapping.get(dataset_name)
            try:
                updated_map = mapper.map(existing_map)  
                # Store updated map in the manager
                self.mapping[dataset_name] = updated_map
            
                 # Mark the dataset or update settings to indicate success
                 #dataset_dict['isDemographicsIncluded'] = True
                 #dataset_settings.update_json(dataset_dict).save_json()
                self.logger.info(f"Demographic Mapping - Completed for dataset '{dataset_name}'")

            
            except Exception as e:
                self.logger.error(f"Demographic Mapping failed for dataset '{dataset_name}': {e}")
                #dataset_dict['isDemographicsIncluded'] = False
                #dataset_settings.update_json(dataset_dict).save_json()



    def scanner_mapping(self):
        """
        Runs a scanner information mapper (default = ScannerMapper)
        that enriches each mapping entry with manufacturer & model data.
        """
        for dataset_name in self.target_datasets:
            self.logger.info(f"Scanner Mapping - Dataset: {dataset_name}")

            # Load the dataset settings
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings_path = dataset_path / self.config.datasetSettingsJson
            dataset_settings = JsonHandler(dataset_settings_path)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )
            

            # Aquire desired plugin or use default ScannerMapper
            plugin_name = final_settings.get("scannerPlugin", "ScannerMapper")

            # Retrieve plugin class
            mapper_cls = self.plugin_loader.get_plugin_by_name(plugin_name)
            if not mapper_cls:
                self.logger.error(f"scannerPlugin plugin '{plugin_name}' not found for dataset '{dataset_name}' - skipped..")
                continue
            
            mapper = mapper_cls(dataset_settings=final_settings, dataset_path=str(dataset_path))

            existing_map = self.mapping.get(dataset_name)
            try:
                updated_map = mapper.map(existing_map)  
                # Store updated map in the manager
                self.mapping[dataset_name] = updated_map
            except Exception as e:
                self.logger.error(f"Scanner Mapping failed for Dataset:{dataset_name} : {e}")

                